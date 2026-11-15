from fastapi import APIRouter, Query
from sqlalchemy import func, select, update

from .. import domain
from ..db import Db
from ..models import WithdrawalNotice
from ..security import Actor

router = APIRouter(prefix="/notifications", tags=["Thông báo"])


@router.get("")
def listing(db: Db, actor: Actor, page: int = Query(1, ge=1)):
    page_size = 12
    own = WithdrawalNotice.recipient_id == actor.id
    counts = select(func.count()).select_from(WithdrawalNotice).where(own)
    total = db.scalar(counts)
    unread = db.scalar(counts.where(WithdrawalNotice.read_at.is_(None)))
    rows = db.scalars(
        select(WithdrawalNotice)
        .where(own)
        .order_by(WithdrawalNotice.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {
        "items": [
            dict(
                id=row.id,
                loan_id=row.loan_id,
                asset_name=row.asset_name,
                reason=row.reason,
                created_at=row.created_at,
                read_at=row.read_at,
            )
            for row in rows
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
        "unread": unread,
    }


@router.post("/{notice_id}/read")
def mark_read(notice_id: int, db: Db, actor: Actor):
    result = db.execute(
        update(WithdrawalNotice)
        .where(WithdrawalNotice.id == notice_id, WithdrawalNotice.recipient_id == actor.id)
        .values(read_at=func.coalesce(WithdrawalNotice.read_at, domain.now()))
    )
    domain.require(result.rowcount == 1, "Không tìm thấy thông báo.", 404)
    return {"message": "Đã đọc thông báo."}
