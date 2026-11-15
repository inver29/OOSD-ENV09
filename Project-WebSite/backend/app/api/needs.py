from fastapi import APIRouter, Query
from pydantic import AwareDatetime
from sqlalchemy import func, select

from .. import domain
from ..db import Db
from ..models import Loan, Need
from ..schemas import OutcomeInput, VerificationInput
from ..security import Actor
from ..services import needs
from ..services.common import can_read_need, get_or_404, loan_view, need_view

router = APIRouter(tags=["Nhu cầu và chỉ số"])


@router.get("/needs")
def listing(
    db: Db,
    actor: Actor,
    scope: str = "mine",
    status: str | None = None,
    q: str = Query("", max_length=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
):
    domain.require_member(actor)
    query = select(Need).where(needs.completed_need())
    if scope == "manage":
        domain.require_manager(actor, actor.unit_id)
        query = query.where(Need.unit_id == actor.unit_id)
    else:
        domain.require(scope == "mine", "Phạm vi không hợp lệ.")
        query = query.where(Need.creator_id == actor.id)
    if status:
        query = query.where(Need.status == status)
    if q:
        query = query.where(Need.purpose.icontains(q, autoescape=True))
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(
        query.order_by(Need.created_at.desc(), Need.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).unique()
    return {
        "items": [need_view(n) for n in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/needs/{need_id}")
def detail(need_id: int, db: Db, actor: Actor):
    need = get_or_404(db, Need, need_id)
    domain.require(can_read_need(actor, need), "Không tìm thấy nhu cầu.", 404)
    domain.require(
        db.scalar(select(Loan.id).where(Loan.need_id == need.id, Loan.status == "DA_HOAN_TRA").limit(1))
        is not None,
        "Không tìm thấy nhu cầu.",
        404,
    )
    result = need_view(need)
    result["loans"] = [
        loan_view(n)
        for n in db.scalars(
            select(Loan).where(Loan.need_id == need_id).order_by(Loan.id.desc())
        ).unique()
    ]
    return result


@router.post("/needs/{need_id}/outcome")
def outcome(need_id: int, data: OutcomeInput, db: Db, actor: Actor):
    return need_view(needs.record_outcome(db, actor, need_id, data.purchased))


@router.post("/needs/{need_id}/verify")
def verify(need_id: int, data: VerificationInput, db: Db, actor: Actor):
    return need_view(needs.verify(db, actor, need_id, data))


@router.get("/reports/avoidance")
def indicator(
    db: Db,
    actor: Actor,
    start: AwareDatetime,
    end: AwareDatetime,
    category_id: int | None = None,
):
    return needs.indicator(db, actor, start, end, category_id)
