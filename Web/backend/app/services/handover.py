from sqlalchemy import select

from .. import domain
from ..models import Grant, Handover, User
from ..schemas import ReportInput
from .common import blocked_end, event, loan_context, locked, reservations, upload_path


def check_delivery(db, asset, loan):
    stamp = domain.now()
    domain.require(loan.status == "DA_DUYET", "Phiếu không còn ở trạng thái Chờ bàn giao.", 409)
    domain.require(
        loan.start_at <= stamp < loan.pickup_deadline,
        "Chưa đến thời gian mượn hoặc đã hết hạn nhận.",
        409,
    )
    domain.require(
        not asset.withdrawn
        and asset.status == "CHO_CHIA_SE"
        and asset.custodian.active
        and asset.unit.active
        and asset.category.active
        and asset.location.active,
        "Hiện vật chưa đủ điều kiện bàn giao.",
        409,
    )
    for other in reservations(db, asset.id, loan.id):
        domain.require(
            other.status not in domain.HOLDING,
            "Tài sản vẫn do người khác giữ, chưa thể bàn giao.",
            409,
        )
        if other.returned_at:
            domain.require(
                stamp >= blocked_end(other),
                "Tài sản vẫn trong khoảng dự phòng sau trả.",
                409,
            )


def return_managers(db, loan):
    return list(
        db.scalars(
            select(User)
            .join(Grant)
            .where(User.unit_id == loan.asset.unit_id, User.active == True, Grant.role == "QUAN_LY")
            .order_by(User.id)
        ).unique()
    )


def save_report(db, actor, loan_id, data):
    asset, loan = loan_context(db, loan_id)
    if data.kind == "GIAO":
        domain.require_manager(actor, asset.unit_id)
        check_delivery(db, asset, loan)
        domain.require(data.condition == "Đạt", "Hiện vật hư hỏng không được bàn giao.")
        giver, receiver = actor.id, loan.borrower_id
    else:
        domain.require(
            loan.status == "CHO_XAC_NHAN_TRA",
            "Người mượn cần báo trả trước khi lập biên bản Trả.",
            409,
        )
        giver = loan.borrower_id
        if actor.id == loan.borrower_id:
            candidates = return_managers(db, loan)
            ids = {u.id for u in candidates}
            preferred = next(
                (r.giver_id for r in loan.reports if r.kind == "GIAO" and r.status == "HOAN_TAT"),
                loan.approver_id,
            )
            receiver = data.receiver_id or (
                preferred if preferred in ids else next((u.id for u in candidates), None)
            )
            domain.require(
                receiver in ids,
                "Chưa có quản lý hợp lệ để nhận trả. Vui lòng liên hệ quản trị.",
                409,
            )
        else:
            domain.require_manager(actor, asset.unit_id)
            receiver = actor.id
    report = db.scalar(
        select(Handover).where(Handover.loan_id == loan.id, Handover.kind == data.kind)
    )
    if report:
        report = locked(db, Handover, report.id)
        domain.require(report.status != "HOAN_TAT", "Biên bản hoàn tất được giữ nguyên.", 409)
        domain.require(
            report.version == data.version,
            "Nội dung biên bản đã thay đổi. Hãy tải lại trước khi sửa.",
            409,
        )
        unchanged = (
            report.content == data.content
            and report.condition == data.condition
            and report.evidence_path == data.evidence_path
            and report.giver_id == giver
            and report.receiver_id == receiver
        )
        if data.confirm_self and unchanged and report.status != "DA_HUY":
            return report
        report.version += 1
        report.giver_confirmed_at = report.receiver_confirmed_at = None
    else:
        domain.require(data.version is None, "Biên bản này chưa tồn tại.", 409)
        report = Handover(loan_id=loan.id, kind=data.kind, version=1)
        db.add(report)
    report.content, report.condition = data.content, data.condition
    report.evidence_path = upload_path(db, actor, data.evidence_path, report.evidence_path)
    report.giver_id, report.receiver_id, report.status = giver, receiver, "NHAP"
    db.flush()
    db.refresh(report)
    return report


def save_and_confirm(db, actor, loan_id, data):
    report = save_report(db, actor, loan_id, data)
    if data.confirm_self:
        return confirm(db, actor, loan_id, report.id, report.version)
    return report


def submit_return(db, actor, loan_id, data):
    _, loan = loan_context(db, loan_id)
    domain.require(loan.borrower_id == actor.id, "Chỉ người mượn được xác nhận trả tài sản.", 403)
    domain.require(loan.status in domain.HOLDING, "Phiếu chưa giao hoặc đã kết thúc.", 409)
    loan.status = "CHO_XAC_NHAN_TRA"
    db.flush()
    payload = ReportInput(kind="TRA", **data.model_dump(), confirm_self=True)
    return save_and_confirm(db, actor, loan_id, payload)


def confirm(db, actor, loan_id, report_id, version):
    asset, loan = loan_context(db, loan_id)
    report = locked(db, Handover, report_id)
    domain.require(report.loan_id == loan.id, "Biên bản không thuộc phiếu này.", 404)
    domain.require(
        actor.id in {report.giver_id, report.receiver_id},
        "Tài khoản không phải bên xác nhận trên biên bản.",
        403,
    )
    domain.require(
        report.version == version,
        "Biên bản đã có nội dung mới. Hãy đọc và xác nhận lại.",
        409,
    )
    if report.status == "HOAN_TAT":
        return report
    domain.require(
        report.status != "DA_HUY",
        "Biên bản đã hủy; cần mở lại trước khi xác nhận.",
        409,
    )
    manager_id = report.giver_id if report.kind == "GIAO" else report.receiver_id
    manager = report.giver if report.kind == "GIAO" else report.receiver
    domain.require(
        domain.manages(manager, asset.unit_id) and manager.active and loan.borrower.active,
        "Quyền của một trong hai bên đã thay đổi.",
        409,
    )
    domain.require(manager_id != loan.borrower_id, "Hai bên xác nhận phải là hai người khác nhau.")
    if report.kind == "GIAO":
        check_delivery(db, asset, loan)
    else:
        domain.require(loan.status == "CHO_XAC_NHAN_TRA", "Phiếu không còn chờ xác nhận trả.", 409)
    if actor.id == report.giver_id:
        report.giver_confirmed_at = report.giver_confirmed_at or domain.now()
    else:
        report.receiver_confirmed_at = report.receiver_confirmed_at or domain.now()
    report.status = "CHO_XAC_NHAN"
    if report.giver_confirmed_at and report.receiver_confirmed_at:
        report.status = "HOAN_TAT"
        if report.kind == "GIAO":
            loan.status, loan.handed_at = "DANG_MUON", domain.now()
            event(
                db,
                asset.id,
                actor.id,
                f"Hoàn tất bàn giao theo phiếu #{loan.id}; người giữ: {loan.borrower.name}.",
            )
        else:
            withdrawing = asset.status == "CHO_THU_HOI"
            loan.status, loan.returned_at = "DA_DONG", domain.now()
            if report.condition == "Hư hỏng":
                asset.status = "BAO_TRI"
                asset.condition = report.content[:500]
                event(
                    db,
                    asset.id,
                    actor.id,
                    f"Phiếu #{loan.id} trả hư hỏng: {report.content}",
                    "SU_CO",
                )
            else:
                event(
                    db,
                    asset.id,
                    actor.id,
                    f"Hoàn tất trả theo phiếu #{loan.id}. Giữ giờ dự phòng sau trả.",
                )
            if withdrawing:
                asset.status = "CHO_THU_HOI"
                asset.withdrawn = True
                event(db, asset.id, actor.id, "Đã nhận trả; hoàn tất thu hồi và ẩn tài sản.")
    db.flush()
    db.refresh(report)
    return report


def cancel_report(db, actor, loan_id, report_id, version):
    asset, loan = loan_context(db, loan_id)
    domain.require_manager(actor, asset.unit_id)
    report = locked(db, Handover, report_id)
    domain.require(
        report.loan_id == loan.id and report.status != "HOAN_TAT",
        "Không thể hủy biên bản này.",
        409,
    )
    domain.require(report.version == version, "Biên bản đã thay đổi.", 409)
    domain.require(loan.status in {"DA_DUYET", "CHO_XAC_NHAN_TRA"}, "Phiếu không còn phù hợp.", 409)
    report.status = "DA_HUY"
    report.version += 1
    report.giver_confirmed_at = report.receiver_confirmed_at = None
    db.flush()
    return report
