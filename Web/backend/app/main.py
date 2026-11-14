import asyncio
import logging
import time
from contextlib import asynccontextmanager, suppress
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from . import domain
from .api import admin, assets, auth, dashboard, files, loans, needs, notifications
from .config import Settings, settings
from .db import make_engine, session_factory
from .security import SessionStore
from .services.loans import expire_due

logger = logging.getLogger("env09")


def create_app(config: Settings = settings, engine=None):
    database = engine or make_engine(config)
    sessions = session_factory(database)

    async def expiry_loop():
        while True:
            try:
                await asyncio.to_thread(expire_due, sessions)
            except Exception:
                logger.exception("Không thể cập nhật phiếu hết hạn nhận")
            await asyncio.sleep(30)

    @asynccontextmanager
    async def lifespan(app):
        config.storage_dir.mkdir(parents=True, exist_ok=True)
        task = asyncio.create_task(expiry_loop()) if config.expiry_worker else None
        yield
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        database.dispose()

    app = FastAPI(
        title="ENV09 — Chia sẻ tài sản",
        version="1.0.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    app.state.config, app.state.engine = config, database
    app.state.sessions, app.state.auth = sessions, SessionStore(config.session_hours)

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = uuid4().hex
        started = time.perf_counter()
        origin = request.headers.get("origin")
        if request.method not in {"GET", "HEAD", "OPTIONS"} and origin:
            permitted = {str(request.base_url).rstrip("/")}
            if not config.cookie_secure:
                permitted.update({"http://127.0.0.1:5173", "http://localhost:5173"})
            if origin.rstrip("/") not in permitted:
                return JSONResponse({"message": "Nguồn yêu cầu không được phép."}, status_code=403)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["X-Frame-Options"] = (
            "SAMEORIGIN" if request.url.path.startswith("/api/files/") else "DENY"
        )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        logger.info(
            "%s %s %s %.0fms %s",
            request.method,
            request.url.path,
            response.status_code,
            (time.perf_counter() - started) * 1000,
            request_id,
        )
        return response

    @app.exception_handler(domain.BusinessError)
    async def business_error(request, exc):
        return JSONResponse({"message": exc.message}, status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        fields = [
            ".".join(str(x) for x in e["loc"] if x not in {"body", "query"}) for e in exc.errors()
        ]
        return JSONResponse(
            {
                "message": "Vui lòng kiểm tra dữ liệu: " + ", ".join(fields) + ".",
                "fields": fields,
            },
            status_code=422,
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error(request, exc):
        logger.warning("Ràng buộc dữ liệu tại %s", request.url.path)
        return JSONResponse(
            {
                "message": "Dữ liệu bị trùng, đang được tham chiếu hoặc chưa đáp ứng ràng buộc. Hãy tải lại và kiểm tra."
            },
            status_code=409,
        )

    @app.exception_handler(DBAPIError)
    async def database_error(request, exc):
        logger.error("Lỗi database tại %s: %s", request.url.path, type(exc.orig).__name__)
        deadlock = "1205" in str(exc.orig)
        return JSONResponse(
            {
                "message": "Có thao tác đồng thời, vui lòng thử lại."
                if deadlock
                else "Chưa thể kết nối dữ liệu. Vui lòng thử lại sau."
            },
            status_code=409 if deadlock else 503,
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request, exc):
        logger.exception("Lỗi xử lý %s", request.url.path)
        return JSONResponse(
            {"message": "Chưa thể hoàn tất thao tác. Vui lòng thử lại."},
            status_code=500,
        )

    @app.get("/api/health", tags=["Hệ thống"])
    def health():
        with database.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "database": "SQL Server"}

    for module in (auth, dashboard, assets, loans, needs, admin, files, notifications):
        app.include_router(module.router, prefix="/api")

    if config.otel_endpoint:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider(resource=Resource.create({"service.name": "env09-api"}))
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=config.otel_endpoint))
        )
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
        SQLAlchemyInstrumentor().instrument(engine=database)

    if (config.frontend_dir / "index.html").is_file():
        app.mount(
            "/static",
            StaticFiles(directory=config.frontend_dir / "static"),
            name="static",
        )

        @app.get("/{path:path}", include_in_schema=False)
        def frontend(path: str):
            if path.startswith("api/"):
                return JSONResponse({"message": "Không tìm thấy chức năng."}, status_code=404)
            return FileResponse(
                config.frontend_dir / "index.html",
                headers={"Cache-Control": "no-cache"},
            )

    return app


logging.basicConfig(
    level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
app = create_app()
