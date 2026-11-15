import re
from datetime import timedelta

from sqlalchemy import exists, select
from sqlalchemy.orm import Session, object_session

from .. import domain
from ..models import Asset, Handover, LifecycleEvent, Loan, Need, Policy, User, WithdrawalNotice


def get_or_404(db: Session, model, record_id: int):
    item = db.get(model, record_id)
    domain.require(item is not None, "Không tìm thấy dữ liệu.", 404)
    return item


def locked(db: Session, model, record_id: int):
    record = db.scalar(
        select(model.id)
        .where(model.id == record_id)
        .with_hint(model, "WITH (UPDLOCK, HOLDLOCK)", "mssql")
    )
    domain.require(record is not None, "Không tìm thấy dữ liệu.", 404)
    return db.get(model, record_id, populate_existing=True)


def loan_context(db: Session, loan_id: int):
    asset_id = db.scalar(select(Loan.asset_id).where(Loan.id == loan_id))
    domain.require(asset_id is not None, "Không tìm thấy phiếu mượn.", 404)
    asset = locked(db, Asset, asset_id)
    loan = locked(db, Loan, loan_id)
    return asset, loan


def event(
    db,
    asset_id: int,
    actor_id: int | None,
    content: str,
    kind="CAP_NHAT",
    basis=None,
    decision=None,
):
    item = LifecycleEvent(
        asset_id=asset_id,
        actor_id=actor_id,
        created_at=domain.now(),
        kind=kind,
        content=content[:1000],
        basis=basis,
        decision=decision,
    )
    db.add(item)
    return item


def upload_path(db, user, value: str | None, previous: str | None = None):
    if not value:
        return None
    domain.require(
        bool(re.fullmatch(r"\d+-[a-f0-9]{32}\.(png|jpg|jpeg|webp|pdf)", value)),
        "Tệp đính kèm không hợp lệ.",
    )
    domain.require(
        value == previous or value.startswith(f"{user.id}-"),
        "Bạn không được dùng tệp của người khác.",
        403,
    )
    domain.require(
        (db.info["storage_dir"] / value).is_file(),
        "Tệp đính kèm chưa được tải lên hoặc không còn tồn tại.",
    )
    return value


def active_policy(db):
    item = db.scalar(
        select(Policy)
        .where(Policy.effective_from <= domain.now())
        .order_by(Policy.effective_from.desc())
    )
    domain.require(
        item is not None,
        "Chưa có chính sách mượn đang có hiệu lực. Vui lòng liên hệ quản trị.",
        409,
    )
    return item


def can_read_loan(user, loan):
    return (
        loan.borrower_id == user.id
        or domain.manages(user, loan.asset.unit_id)
        or (loan.need_id is not None and domain.manages(user, loan.borrower_unit_id))
    )


def can_read_need(user, need):
    return need.creator_id == user.id or domain.manages(user, need.unit_id)


def reservations(db, asset_id: int, exclude_id: int | None = None):
    query = select(Loan).where(
        Loan.asset_id == asset_id,
        Loan.status.in_(domain.HOLDING | {"CHO_BAN_GIAO", "DA_HOAN_TRA"}),
    )
    if exclude_id:
        query = query.where(Loan.id != exclude_id)
    return list(db.scalars(query).unique())


def active_checkout_condition():
    """An approved voucher occupies the whole item until cancellation/expiry/return."""
    return Loan.status.in_(domain.HOLDING | {"CHO_BAN_GIAO"})


def has_checkout(asset_id=Asset.id):
    return exists(select(Loan.id).where(Loan.asset_id == asset_id, active_checkout_condition()))


def require_no_checkout(db, asset_id, exclude_id=None):
    query = select(Loan.id).where(Loan.asset_id == asset_id, active_checkout_condition())
    if exclude_id is not None:
        query = query.where(Loan.id != exclude_id)
    domain.require(
        db.scalar(query.limit(1)) is None,
        "Đã có người khác mượn tài sản này",
        409,
    )


def checkout_statuses(db, asset_ids):
    if not asset_ids:
        return {}
    rows = db.execute(
        select(Loan.asset_id, Loan.status).where(
            Loan.asset_id.in_(asset_ids), active_checkout_condition()
        )
    )
    states = {}
    for asset_id, status in rows:
        # Holding takes precedence if older data contains several future reservations.
        if status in domain.HOLDING or asset_id not in states:
            states[asset_id] = status
    return states


def blocked_end(loan):
    return (loan.returned_at or loan.end_at) + timedelta(hours=loan.buffer_hours or 0)


def check_availability(db, asset_id, start, end, buffer_hours, exclude_id=None):
    requested_end = end + timedelta(hours=buffer_hours)
    for loan in reservations(db, asset_id, exclude_id):
        if loan.status == "CHO_BAN_GIAO" and loan.pickup_deadline <= domain.now():
            continue
        if loan.status in domain.HOLDING and loan.end_at <= domain.now():
            raise domain.BusinessError(
                "Tài sản đang quá hạn trả. Chỉ có thể duyệt thêm sau khi nhận trả.", 409
            )
        if start < blocked_end(loan) and loan.start_at < requested_end:
            raise domain.BusinessError(
                "Khoảng thời gian đã có lịch mượn hoặc còn giờ dự phòng. Vui lòng chọn thời gian khác.",
                409,
            )


def invalidate_reports(db, loan):
    for report in db.scalars(
        select(Handover).where(Handover.loan_id == loan.id, Handover.status != "HOAN_TAT")
    ):
        report.status = "DA_HUY"
        report.version += 1
        report.giver_confirmed_at = report.receiver_confirmed_at = None


def cancel_pending(db, asset, actor, reason: str, requested: bool):
    loans = list(
        db.scalars(
            select(Loan)
            .where(Loan.asset_id == asset.id, Loan.status.in_(domain.PENDING))
            .order_by(Loan.id)
        ).unique()
    )
    domain.require(
        not loans or requested,
        f"Còn {len(loans)} phiếu chưa giao. Hãy xử lý hoặc chọn hủy các phiếu này trước.",
        409,
    )
    for candidate in loans:
        loan = locked(db, Loan, candidate.id)
        loan.status = "DA_HUY"
        loan.reason = reason[:500]
        invalidate_reports(db, loan)
        event(db, asset.id, actor.id, f"Hủy phiếu #{loan.id}: {reason}")


def delete_pending_for_withdrawal(db, asset, actor):
    """The asset lock serializes withdrawal against approval and delivery."""
    candidates = list(
        db.scalars(
            select(Loan)
            .where(Loan.asset_id == asset.id, Loan.status.in_(domain.PENDING))
            .order_by(Loan.id)
        ).unique()
    )
    for candidate in candidates:
        loan = locked(db, Loan, candidate.id)
        domain.require(
            loan.handed_at is None and all(r.status != "HOAN_TAT" for r in loan.reports),
            "Phiếu có dữ liệu bàn giao; cần kiểm tra trước khi thu hồi.",
            409,
        )
        for report in loan.reports:
            db.delete(report)
        db.flush()
        event(
            db,
            asset.id,
            actor.id,
            f"Hủy và xóa phiếu chưa giao #{loan.id}. Lý do: {domain.WITHDRAWAL_REASON}.",
        )
        db.add(
            WithdrawalNotice(
                recipient_id=loan.borrower_id,
                loan_id=loan.id,
                asset_name=asset.name,
                reason=domain.WITHDRAWAL_REASON,
                created_at=domain.now(),
            )
        )
        db.delete(loan)
    db.flush()
    return len(candidates)


def user_view(user: User):
    return dict(
        id=user.id,
        username=user.username,
        name=user.name,
        email=user.email,
        unit_id=user.unit_id,
        unit_name=user.unit.name,
        unit_address=user.unit.address,
        roles=user.roles,
        active=user.active,
    )


def asset_view(asset: Asset, checkout_status=None):
    if checkout_status is None:
        db = object_session(asset)
        checkout_status = checkout_statuses(db, [asset.id]).get(asset.id, "") if db else ""
    status = asset.status
    if asset.withdrawn:
        status = "DA_THU_HOI"
    elif status != "CHO_THU_HOI":
        if checkout_status in domain.HOLDING:
            status = "DA_DUOC_MUON"
        elif status == "CHO_CHIA_SE" and checkout_status == "CHO_BAN_GIAO":
            status = "CHO_BAN_GIAO"
    return dict(
        id=asset.id,
        name=asset.name,
        category_id=asset.category_id,
        category_name=asset.category.name,
        unit_id=asset.unit_id,
        unit_name=asset.unit.name,
        unit_address=asset.unit.address,
        location_id=asset.location_id,
        location_name=asset.location.name,
        custodian_id=asset.custodian_id,
        custodian_name=asset.custodian.name,
        contact_email=asset.custodian.email,
        description=asset.description,
        condition=asset.condition,
        status=status,
        lifecycle_status=asset.status,
        withdrawn=asset.withdrawn,
        holding=checkout_status in domain.HOLDING,
        image_path=asset.image_path,
        version=asset.version.hex(),
    )


def asset_views(db, assets):
    states = checkout_statuses(db, [asset.id for asset in assets])
    return [asset_view(asset, states.get(asset.id, "")) for asset in assets]


def report_view(report: Handover):
    return dict(
        id=report.id,
        loan_id=report.loan_id,
        kind=report.kind,
        content=report.content,
        condition=report.condition,
        evidence_path=report.evidence_path,
        giver_id=report.giver_id,
        giver_name=report.giver.name,
        receiver_id=report.receiver_id,
        receiver_name=report.receiver.name,
        giver_confirmed_at=report.giver_confirmed_at,
        receiver_confirmed_at=report.receiver_confirmed_at,
        status=report.status,
        version=report.version,
    )


def loan_view(loan: Loan, detail=False):
    result = dict(
        id=loan.id,
        asset_id=loan.asset_id,
        asset_name=loan.asset.name,
        asset_unit_id=loan.asset.unit_id,
        asset_unit_name=loan.asset.unit.name,
        category_name=loan.asset.category.name,
        borrower_id=loan.borrower_id,
        borrower_name=loan.borrower.name,
        borrower_unit_id=loan.borrower_unit_id,
        borrower_unit_name=loan.borrower_unit.name,
        need_id=loan.need_id,
        purpose=loan.purpose,
        start_at=loan.start_at,
        end_at=loan.end_at,
        status=loan.status,
        reason=loan.reason,
        approver_name=loan.approver.name if loan.approver else None,
        created_at=loan.created_at,
        decided_at=loan.decided_at,
        pickup_deadline=loan.pickup_deadline,
        handed_at=loan.handed_at,
        returned_at=loan.returned_at,
        buffer_hours=loan.buffer_hours,
        overdue=loan.status in domain.HOLDING and loan.end_at < domain.now(),
    )
    if detail:
        result.update(
            asset=asset_view(loan.asset),
            reports=[report_view(r) for r in loan.reports],
            policy=dict(
                name=loan.policy.name,
                max_days=loan.policy.max_days,
                pickup_hours=loan.policy.pickup_hours,
                buffer_hours=loan.policy.buffer_hours,
            ),
        )
    return result


def need_view(need: Need):
    verification = need.verification
    return dict(
        id=need.id,
        unit_id=need.unit_id,
        unit_name=need.unit.name,
        creator_id=need.creator_id,
        creator_name=need.creator.name,
        category_id=need.category_id,
        category_name=need.category.name,
        purpose=need.purpose,
        start_at=need.start_at,
        end_at=need.end_at,
        alternative=need.alternative,
        evidence_path=need.evidence_path,
        purchased=need.purchased,
        status=need.status,
        created_at=need.created_at,
        verification=None
        if not verification
        else dict(
            id=verification.id,
            verifier_id=verification.verifier_id,
            verifier_name=verification.verifier.name,
            verified_at=verification.verified_at,
            intended_purchase=verification.intended_purchase,
            purpose_met=verification.purpose_met,
            conclusion=verification.conclusion,
            evidence_path=verification.evidence_path,
        ),
    )
