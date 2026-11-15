from datetime import timedelta

from fastapi import APIRouter, Query
from pydantic import AwareDatetime
from sqlalchemy import and_, exists, func, literal_column, or_, select

from .. import domain
from ..db import Db
from ..models import Asset, LifecycleEvent, Loan
from ..schemas import AssetInput, AssetReviewInput, AssetWithdrawInput, EventInput
from ..security import Actor
from ..services import assets
from ..services.common import (
    active_policy,
    asset_view,
    asset_views,
    blocked_end,
    can_read_loan,
    has_checkout,
    reservations,
)

router = APIRouter(prefix="/assets", tags=["Tài sản"])


@router.get("")
def listing(
    db: Db,
    actor: Actor,
    q: str = Query("", max_length=200),
    scope: str = "shared",
    category_id: int | None = None,
    unit_id: int | None = None,
    location_id: int | None = None,
    status: str | None = None,
    start: AwareDatetime | None = None,
    end: AwareDatetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
):
    domain.require_member(actor)
    query = select(Asset).where(Asset.withdrawn == False)
    if scope == "shared":
        query = query.where(
            Asset.status == "CHO_CHIA_SE", Asset.unit_id != actor.unit_id, ~has_checkout()
        )
    else:
        domain.require(scope == "own", "Phạm vi tra cứu không hợp lệ.")
        query = query.where(Asset.unit_id == actor.unit_id)
    if q:
        query = query.where(
            or_(
                Asset.name.icontains(q, autoescape=True),
                Asset.description.icontains(q, autoescape=True),
            )
        )
    for column, value in [
        (Asset.category_id, category_id),
        (Asset.unit_id, unit_id),
        (Asset.location_id, location_id),
    ]:
        if value is not None:
            query = query.where(column == value)
    if status == "CHO_CHIA_SE":
        query = query.where(Asset.status == "CHO_CHIA_SE", ~has_checkout())
    elif status in {"CHO_BAN_GIAO", "DA_DUOC_MUON"}:
        holding = exists(
            select(Loan.id).where(Loan.asset_id == Asset.id, Loan.status.in_(domain.HOLDING))
        )
        query = query.where(
            Asset.status != "CHO_THU_HOI",
            holding if status == "DA_DUOC_MUON" else and_(has_checkout(), ~holding),
        )
    elif status:
        query = query.where(Asset.status == status)
    domain.require((start is None) == (end is None), "Vui lòng chọn đủ ngày bắt đầu và kết thúc.")
    if start and end:
        domain.check_period(start, end)
        policy = active_policy(db)
        effective_end = func.dateadd(
            literal_column("hour"),
            func.coalesce(Loan.buffer_hours, 0),
            func.coalesce(Loan.returned_at, Loan.end_at),
        )
        blocks = or_(
            Loan.status.in_(domain.HOLDING | {"DA_HOAN_TRA"}),
            and_(Loan.status == "CHO_BAN_GIAO", Loan.pickup_deadline > domain.now()),
        )
        conflict = exists(
            select(Loan.id).where(
                Loan.asset_id == Asset.id,
                blocks,
                start < effective_end,
                Loan.start_at < end + timedelta(hours=policy.buffer_hours),
            )
        )
        overdue = exists(
            select(Loan.id).where(
                Loan.asset_id == Asset.id,
                Loan.status.in_(domain.HOLDING),
                Loan.end_at <= domain.now(),
            )
        )
        query = query.where(~conflict, ~overdue)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    records = list(
        db.scalars(
            query.order_by(Asset.id.desc()).offset((page - 1) * page_size).limit(page_size)
        ).unique()
    )
    return {
        "items": asset_views(db, records),
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", status_code=201)
def create(data: AssetInput, db: Db, actor: Actor):
    return asset_view(assets.save_asset(db, actor, data))


@router.get("/{asset_id}")
def detail(asset_id: int, db: Db, actor: Actor):
    domain.require_member(actor)
    asset = assets.read_asset(db, actor, asset_id)
    result = asset_view(asset)
    calendar = []
    for loan in reservations(db, asset_id):
        if loan.status == "CHO_BAN_GIAO" and loan.pickup_deadline <= domain.now():
            continue
        if blocked_end(loan) < domain.now() and loan.status not in domain.HOLDING:
            continue
        calendar.append(
            dict(
                loan_id=loan.id if can_read_loan(actor, loan) else None,
                start_at=loan.start_at,
                end_at=blocked_end(loan),
                overdue=loan.status in domain.HOLDING and loan.end_at < domain.now(),
                status=loan.status,
            )
        )
    result["calendar"] = sorted(calendar, key=lambda r: r["start_at"])
    return result


@router.put("/{asset_id}")
def update(asset_id: int, data: AssetInput, db: Db, actor: Actor):
    return asset_view(assets.save_asset(db, actor, data, asset_id))


@router.post("/{asset_id}/review")
def review(asset_id: int, data: AssetReviewInput, db: Db, actor: Actor):
    return asset_view(assets.review_asset(db, actor, asset_id, data))


@router.post("/{asset_id}/withdraw")
def withdraw(asset_id: int, data: AssetWithdrawInput, db: Db, actor: Actor):
    domain.require_member(actor)
    return assets.withdraw_asset(db, actor, asset_id, data)


@router.get("/{asset_id}/events")
def history(asset_id: int, db: Db, actor: Actor):
    domain.require_member(actor)
    asset = assets.read_asset(db, actor, asset_id)
    own_loan = db.scalar(
        select(Loan.id).where(Loan.asset_id == asset.id, Loan.borrower_id == actor.id)
    )
    domain.require(
        asset.unit_id == actor.unit_id or own_loan is not None,
        "Bạn chưa có quyền xem lịch sử chi tiết của tài sản.",
        403,
    )
    records = db.scalars(
        select(LifecycleEvent)
        .where(LifecycleEvent.asset_id == asset.id)
        .order_by(LifecycleEvent.created_at.desc(), LifecycleEvent.id.desc())
    )
    return [
        dict(
            id=e.id,
            asset_id=e.asset_id,
            asset_name=asset.name,
            actor_name=e.actor.name if e.actor else "Hệ thống",
            created_at=e.created_at,
            kind=e.kind,
            content=e.content,
            basis=e.basis,
            decision=e.decision,
        )
        for e in records
    ]


@router.post("/{asset_id}/events", status_code=201)
def add_event(asset_id: int, data: EventInput, db: Db, actor: Actor):
    return asset_view(assets.lifecycle_event(db, actor, asset_id, data))
