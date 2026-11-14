from datetime import timedelta

from sqlalchemy import select

from .. import domain
from ..models import Asset, Loan, Need
from .common import (
    active_policy,
    check_availability,
    event,
    invalidate_reports,
    loan_context,
    locked,
    require_no_checkout,
)


def create_loan(db, actor, data):
    domain.require_member(actor)
    domain.require(
        not (data.need_id and data.new_need), "Chọn nhu cầu có sẵn hoặc ghi nhu cầu mới."
    )
    asset = locked(db, Asset, data.asset_id)
    domain.require(not asset.withdrawn, "Không tìm thấy tài sản.", 404)
    request_id = str(data.request_id)
    existing = db.scalar(select(Loan).where(Loan.request_id == request_id))
    if existing:
        same_need = existing.need_id == data.need_id
        if data.new_need:
            original = db.get(Need, existing.need_id) if existing.need_id else None
            same_need = original is not None and all(
                getattr(original, field) == getattr(data.new_need, field)
                for field in (
                    "category_id",
                    "purpose",
                    "start_at",
                    "end_at",
                    "alternative",
                    "evidence_path",
                )
            )
        same = (
            existing.borrower_id == actor.id
            and existing.asset_id == data.asset_id
            and existing.start_at == data.start_at
            and existing.end_at == data.end_at
            and existing.purpose == data.purpose
            and same_need
        )
        domain.require(same, "Mã gửi đã dùng cho nội dung khác. Hãy tải lại biểu mẫu.", 409)
        return existing
    domain.check_period(data.start_at, data.end_at)
    domain.require(data.start_at >= domain.now(), "Không đặt mượn vào thời điểm đã qua.")
    domain.require(
        actor.unit_id != asset.unit_id,
        "Chức năng này dành cho mượn tài sản giữa các đơn vị.",
    )
    domain.require(
        asset.status == "CHO_CHIA_SE"
        and asset.unit.active
        and asset.category.active
        and asset.location.active
        and asset.custodian.active,
        "Tài sản hiện chưa được cho phép chia sẻ.",
        409,
    )
    policy = active_policy(db)
    require_no_checkout(db, asset.id)
    domain.require(
        data.end_at - data.start_at <= timedelta(days=policy.max_days),
        f"Thời hạn mượn tối đa là {policy.max_days} ngày.",
    )
    check_availability(db, asset.id, data.start_at, data.end_at, policy.buffer_hours)
    need_id = data.need_id
    if data.new_need:
        from .needs import save_need

        need_data = data.new_need.model_copy(update={"auto_submit": True})
        need = save_need(db, actor, need_data)
        need_id = need.id
    if need_id:
        need = locked(db, Need, need_id)
        domain.require(
            need is not None
            and need.unit_id == actor.unit_id
            and need.category_id == asset.category_id,
            "Nhu cầu phải cùng đơn vị mượn và đúng loại tài sản.",
        )
        domain.require(
            need.creator_id == actor.id or domain.manages(actor, need.unit_id),
            "Bạn không được liên kết nhu cầu này.",
            403,
        )
        domain.require(
            need.status in {"NHAP", "CHO_XAC_MINH"},
            "Nhu cầu này không còn tiếp nhận phiếu mới.",
        )
        domain.require(
            need.start_at <= data.start_at and data.end_at <= need.end_at,
            "Thời gian mượn phải nằm trong thời gian của nhu cầu.",
        )
    loan = Loan(
        asset_id=asset.id,
        borrower_id=actor.id,
        borrower_unit_id=actor.unit_id,
        need_id=need_id,
        policy_id=policy.id,
        start_at=data.start_at,
        end_at=data.end_at,
        purpose=data.purpose,
        status="CHO_DUYET",
        created_at=domain.now(),
        request_id=request_id,
    )
    db.add(loan)
    db.flush()
    return loan


def decide(db, actor, loan_id, data):
    asset, loan = loan_context(db, loan_id)
    domain.require_manager(actor, asset.unit_id)
    domain.require(actor.id != loan.borrower_id, "Không được tự xét duyệt phiếu của mình.", 403)
    domain.require(loan.status == "CHO_DUYET", "Phiếu đã được xử lý. Hãy tải lại danh sách.", 409)
    if data.approve:
        domain.require(
            asset.status == "CHO_CHIA_SE"
            and asset.unit.active
            and asset.category.active
            and asset.location.active
            and asset.custodian.active,
            "Tài sản không còn đủ điều kiện chia sẻ.",
            409,
        )
        deadline = domain.pickup_deadline(loan)
        domain.require(
            deadline > domain.now(),
            "Đã hết khoảng thời gian nhận tài sản. Hãy từ chối hoặc hủy phiếu.",
            409,
        )
        domain.require(
            loan.borrower.active
            and loan.borrower.unit.active
            and loan.borrower.unit_id == loan.borrower_unit_id,
            "Tài khoản hoặc đơn vị người mượn đã thay đổi.",
            409,
        )
        check_availability(
            db, asset.id, loan.start_at, loan.end_at, loan.policy.buffer_hours, loan.id
        )
        require_no_checkout(db, asset.id, loan.id)
        loan.status, loan.pickup_deadline, loan.buffer_hours = (
            "DA_DUYET",
            deadline,
            loan.policy.buffer_hours,
        )
    else:
        domain.require(len(data.reason.strip()) >= 5, "Vui lòng ghi lý do từ chối.")
        loan.status = "TU_CHOI"
    loan.approver_id, loan.decided_at, loan.reason = (
        actor.id,
        domain.now(),
        data.reason or None,
    )
    event(
        db,
        asset.id,
        actor.id,
        f"{'Duyệt' if data.approve else 'Từ chối'} phiếu #{loan.id}. {data.reason}",
    )
    if data.approve:
        # The asset lock serializes approval and creation, including simultaneous requests.
        candidates = list(
            db.scalars(
                select(Loan)
                .where(Loan.asset_id == asset.id, Loan.id != loan.id, Loan.status == "CHO_DUYET")
                .order_by(Loan.id)
            ).unique()
        )
        for candidate in candidates:
            other = locked(db, Loan, candidate.id)
            other.status = "TU_CHOI"
            other.reason = "Đã có người khác mượn tài sản này"
            other.approver_id, other.decided_at = actor.id, domain.now()
            invalidate_reports(db, other)
            event(db, asset.id, actor.id, f"Tự động từ chối phiếu #{other.id}: {other.reason}")
    db.flush()
    db.refresh(loan)
    return loan


def cancel(db, actor, loan_id, reason):
    asset, loan = loan_context(db, loan_id)
    domain.require(
        loan.borrower_id == actor.id or domain.manages(actor, asset.unit_id),
        "Bạn không được hủy phiếu này.",
        403,
    )
    if loan.status == "DA_HUY":
        return loan
    domain.require(
        loan.status in domain.PENDING and loan.handed_at is None,
        "Chỉ hủy phiếu chưa bàn giao.",
        409,
    )
    loan.status, loan.reason = "DA_HUY", reason
    invalidate_reports(db, loan)
    event(db, asset.id, actor.id, f"Hủy phiếu #{loan.id}: {reason}")
    db.flush()
    return loan


def request_return(db, actor, loan_id):
    _, loan = loan_context(db, loan_id)
    domain.require(actor.id == loan.borrower_id, "Chỉ đúng người mượn được báo trả.", 403)
    domain.require(loan.status in domain.HOLDING, "Phiếu chưa được giao hoặc đã kết thúc.", 409)
    loan.status = "CHO_XAC_NHAN_TRA"
    db.flush()
    return loan


def expire_due(sessions):
    """Each expired voucher uses a separate short transaction, asset first, voucher second."""
    with sessions() as db:
        ids = list(
            db.scalars(
                select(Loan.id)
                .where(Loan.status == "DA_DUYET", Loan.pickup_deadline <= domain.now())
                .order_by(Loan.asset_id, Loan.id)
            )
        )
    for loan_id in ids:
        try:
            with sessions.begin() as db:
                asset, loan = loan_context(db, loan_id)
                if (
                    loan.status == "DA_DUYET"
                    and loan.handed_at is None
                    and loan.pickup_deadline <= domain.now()
                ):
                    loan.status, loan.reason = "HET_HAN_NHAN", "Hết hạn nhận tài sản."
                    invalidate_reports(db, loan)
                    event(
                        db,
                        asset.id,
                        None,
                        f"Tác vụ máy chủ: phiếu #{loan.id} hết hạn nhận; giải phóng lịch.",
                    )
        except domain.BusinessError as exc:
            if exc.status != 404:
                raise
            # A concurrent withdrawal already removed this undelivered voucher.
            continue
