from fastapi import APIRouter
from sqlalchemy import func, select

from .. import domain
from ..db import Db
from ..models import Asset, Loan, Need
from ..security import Actor
from ..services.common import has_checkout, loan_view
from ..services.needs import completed_need

router = APIRouter(tags=["Tổng quan"])


@router.get("/dashboard")
def dashboard(db: Db, actor: Actor):
    domain.require(
        "QUAN_TRI" not in actor.roles, "Tài khoản quản trị sử dụng trang Quản trị hệ thống.", 403
    )

    def count(model, *conditions):
        return db.scalar(select(func.count()).select_from(model).where(*conditions)) or 0

    result = {
        "shared": count(
            Asset,
            Asset.withdrawn == False,
            Asset.status == "CHO_CHIA_SE",
            Asset.unit_id != actor.unit_id,
            ~has_checkout(),
        ),
        "my_open": count(Loan, Loan.borrower_id == actor.id, Loan.status.in_(domain.OPEN)),
        "my_holding": count(Loan, Loan.borrower_id == actor.id, Loan.status.in_(domain.HOLDING)),
        "my_overdue": count(
            Loan,
            Loan.borrower_id == actor.id,
            Loan.status.in_(domain.HOLDING),
            Loan.end_at < domain.now(),
        ),
    }
    recent = select(Loan).where(Loan.borrower_id == actor.id)
    if "QUAN_LY" in actor.roles:
        owned = select(Asset.id).where(Asset.unit_id == actor.unit_id)
        result.update(
            pending=count(Loan, Loan.asset_id.in_(owned), Loan.status == "CHO_DUYET"),
            need_review=count(
                Need,
                Need.unit_id == actor.unit_id,
                Need.creator_id != actor.id,
                Need.status == "CHO_XAC_MINH",
                Need.purchased.is_not(None),
                completed_need(),
            ),
            paused=count(
                Asset,
                Asset.unit_id == actor.unit_id,
                Asset.withdrawn == False,
                Asset.status.in_({"BAO_TRI", "CHO_THU_HOI"}),
            ),
            overdue=count(
                Loan,
                Loan.asset_id.in_(owned),
                Loan.status.in_(domain.HOLDING),
                Loan.end_at < domain.now(),
            ),
        )
        recent = select(Loan).where((Loan.asset_id.in_(owned)) | (Loan.borrower_id == actor.id))
    result["recent"] = [
        loan_view(x) for x in db.scalars(recent.order_by(Loan.created_at.desc()).limit(5)).unique()
    ]
    return result
