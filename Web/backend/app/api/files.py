import re
from io import BytesIO
from uuid import uuid4

from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select

from .. import domain
from ..db import Db
from ..models import Asset, Handover, Loan, Need, Verification
from ..security import Actor
from ..services.common import can_read_loan, can_read_need

router = APIRouter(prefix="/files", tags=["Tệp đính kèm"])
PATTERN = re.compile(r"\d+-[a-f0-9]{32}\.(?:png|jpg|webp|pdf)")


@router.post("", status_code=201)
async def upload(file: UploadFile, request: Request, actor: Actor):
    domain.require_member(actor)
    config = request.app.state.config
    data = await file.read(config.max_upload_bytes + 1)
    await file.close()
    domain.require(
        0 < len(data) <= config.max_upload_bytes,
        "Tệp phải có dung lượng từ 1 byte đến 8 MB.",
    )
    if data.startswith(b"%PDF-"):
        ext = "pdf"
    else:
        try:
            with Image.open(BytesIO(data)) as image:
                domain.require(
                    image.width * image.height <= 30_000_000,
                    "Ảnh quá lớn. Vui lòng dùng ảnh dưới 30 megapixel.",
                )
                ext = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}.get(image.format)
                domain.require(ext is not None, "Chỉ hỗ trợ PNG, JPG, WEBP hoặc PDF.")
                image.verify()
        except (
            UnidentifiedImageError,
            OSError,
            SyntaxError,
            ValueError,
            Image.DecompressionBombError,
        ):
            raise domain.BusinessError("Tệp ảnh không hợp lệ.")
    name = f"{actor.id}-{uuid4().hex}.{ext}"
    config.storage_dir.mkdir(parents=True, exist_ok=True)
    (config.storage_dir / name).write_bytes(data)
    return {"filename": name, "url": f"/api/files/{name}"}


@router.get("/{name}")
def download(name: str, request: Request, db: Db, actor: Actor):
    domain.require_member(actor)
    domain.require(PATTERN.fullmatch(name) is not None, "Không tìm thấy tệp.", 404)
    path = request.app.state.config.storage_dir / name
    domain.require(path.is_file(), "Không tìm thấy tệp.", 404)
    allowed = name.startswith(f"{actor.id}-")
    if not allowed:
        allowed = (
            db.scalar(
                select(Asset.id).where(
                    Asset.image_path == name,
                    Asset.withdrawn == False,
                    (Asset.unit_id == actor.unit_id)
                    | (Asset.status.not_in({"CHO_DUYET", "TU_CHOI"})),
                )
            )
            is not None
        )
    if not allowed:
        report = db.scalar(select(Handover).where(Handover.evidence_path == name))
        allowed = report is not None and can_read_loan(actor, db.get(Loan, report.loan_id))
    if not allowed:
        need = db.scalar(select(Need).where(Need.evidence_path == name))
        if need is None:
            verification = db.scalar(select(Verification).where(Verification.evidence_path == name))
            need = db.get(Need, verification.need_id) if verification else None
        allowed = need is not None and can_read_need(actor, need)
    domain.require(allowed, "Bạn không được xem tệp này.", 403)
    return FileResponse(
        path,
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
