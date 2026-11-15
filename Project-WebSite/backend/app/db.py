from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import Settings


def odbc_value(value: str) -> str:
    return "{" + value.replace("}", "}}") + "}"


def make_engine(config: Settings, database: str | None = None):
    connection = (
        f"DRIVER={odbc_value(config.db_driver)};"
        f"SERVER={odbc_value(config.db_server)};"
        f"DATABASE={odbc_value(database or config.db_name)};"
        "Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=8;"
    )
    if config.db_trusted:
        connection += "Trusted_Connection=yes;"
    else:
        connection += f"UID={odbc_value(config.db_user)};PWD={odbc_value(config.db_password)};"
    return create_engine(
        URL.create("mssql+pyodbc", query={"odbc_connect": connection}),
        pool_pre_ping=True,
        pool_size=8,
        max_overflow=4,
        fast_executemany=True,
        isolation_level="READ COMMITTED",
    )


def session_factory(engine):
    return sessionmaker(engine, expire_on_commit=False)


def get_db(request: Request) -> Iterator[Session]:
    with request.app.state.sessions() as db:
        db.info["storage_dir"] = request.app.state.config.storage_dir
        try:
            yield db
            # Function scope commits before FastAPI sends a successful response.
            db.commit()
        except Exception:
            db.rollback()
            raise


Db = Annotated[Session, Depends(get_db, scope="function")]
