from fastapi import APIRouter, Query
from sqlalchemy import func, or_, select

from .. import domain
from ..db import Db
from ..models import Asset, Loan, Need
from ..schemas import DecisionInput, LoanInput, ReasonInput, ReportInput, ReturnInput, VersionInput
from ..security import Actor
from ..services import handover, loans
from ..services.common import (
    can_read_loan,
    can_read_need,
    get_or_404,
    loan_view,
    need_view,
    report_view,
)

router = APIRouter(prefix="/loans", tags=["Mượn, xét duyệt và giao nhận"])


@router.get("")
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
    query = select(Loan).join(Asset, Loan.asset_id == Asset.id)
    if scope == "manage":
        domain.require_manager(actor, actor.unit_id)
        query = query.where(Asset.unit_id == actor.unit_id)
    else:
        domain.require(scope == "mine", "Phạm vi phiếu không hợp lệ.")
        query = query.where(Loan.borrower_id == actor.id)
    if status == "OVERDUE":
        query = query.where(Loan.status.in_(domain.HOLDING), Loan.end_at < domain.now())
    elif status:
        query = query.where(Loan.status == status)
    if q:
        query = query.where(
            or_(
                Asset.name.icontains(q, autoescape=True),
                Loan.purpose.icontains(q, autoescape=True),
            )
        )
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(
        query.order_by(Loan.created_at.desc(), Loan.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).unique()
    return {
        "items": [loan_view(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", status_code=201)
def create(data: LoanInput, db: Db, actor: Actor):
    return loan_view(loans.create_loan(db, actor, data), True)


@router.get("/{loan_id}")
def detail(loan_id: int, db: Db, actor: Actor):
    loan = get_or_404(db, Loan, loan_id)
    domain.require(can_read_loan(actor, loan), "Không tìm thấy phiếu mượn.", 404)
    result = loan_view(loan, True)
    result["return_managers"] = [
        {"id": u.id, "name": u.name} for u in handover.return_managers(db, loan)
    ]
    need = db.get(Need, loan.need_id) if loan.need_id else None
    result["need"] = (
        need_view(need)
        if need and loan.status == "DA_DONG" and can_read_need(actor, need)
        else None
    )
    return result


@router.post("/{loan_id}/decision")
def decide(loan_id: int, data: DecisionInput, db: Db, actor: Actor):
    return loan_view(loans.decide(db, actor, loan_id, data), True)


@router.post("/{loan_id}/cancel")
def cancel(loan_id: int, data: ReasonInput, db: Db, actor: Actor):
    return loan_view(loans.cancel(db, actor, loan_id, data.reason), True)


@router.post("/{loan_id}/return")
def request_return(loan_id: int, db: Db, actor: Actor, data: ReturnInput | None = None):
    if data:
        return report_view(handover.submit_return(db, actor, loan_id, data))
    return loan_view(loans.request_return(db, actor, loan_id), True)


@router.post("/{loan_id}/reports")
def save_report(loan_id: int, data: ReportInput, db: Db, actor: Actor):
    return report_view(handover.save_and_confirm(db, actor, loan_id, data))


@router.post("/{loan_id}/reports/{report_id}/confirm")
def confirm(loan_id: int, report_id: int, data: VersionInput, db: Db, actor: Actor):
    return report_view(handover.confirm(db, actor, loan_id, report_id, data.version))


@router.post("/{loan_id}/reports/{report_id}/cancel")
def cancel_report(loan_id: int, report_id: int, data: VersionInput, db: Db, actor: Actor):
    return report_view(handover.cancel_report(db, actor, loan_id, report_id, data.version))
