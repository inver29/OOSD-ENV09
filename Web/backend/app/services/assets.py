from sqlalchemy import select

from .. import domain
from ..models import Asset, Category, Loan, Location
from .common import (
    cancel_pending,
    delete_pending_for_withdrawal,
    event,
    get_or_404,
    locked,
    upload_path,
)


def read_asset(db, actor, asset_id):
    asset = get_or_404(db, Asset, asset_id)
    domain.require(not asset.withdrawn, "Không tìm thấy tài sản.", 404)
    domain.require(
        asset.unit_id == actor.unit_id or asset.status not in {"CHO_DUYET", "TU_CHOI"},
        "Không tìm thấy tài sản.",
        404,
    )
    return asset


def save_asset(db, actor, data, asset_id=None):
    domain.require_member(actor)
    asset = locked(db, Asset, asset_id) if asset_id else None
    if asset:
        domain.require(not asset.withdrawn, "Không tìm thấy tài sản.", 404)
        domain.require(
            asset.custodian_id == actor.id and asset.unit_id == actor.unit_id,
            "Chỉ người phụ trách được sửa hồ sơ tài sản này.",
            403,
        )
        domain.require(
            data.version == asset.version.hex(),
            "Hồ sơ đã được cập nhật. Hãy tải lại trước khi lưu.",
            409,
        )
        domain.require(
            asset.status != "CHO_THU_HOI",
            "Tài sản đang chờ thu hồi; không được sửa hồ sơ.",
            409,
        )
    location = get_or_404(db, Location, data.location_id)
    category = get_or_404(db, Category, data.category_id)
    domain.require(
        location.active and location.unit_id == actor.unit_id and category.active,
        "Loại tài sản hoặc địa điểm không hợp lệ trong đơn vị của bạn.",
    )
    custodian = asset.custodian if asset else actor
    domain.require(
        data.custodian_id is None or data.custodian_id == custodian.id,
        "Người thêm là người phụ trách; không được thay đổi người phụ trách.",
        403,
    )
    if asset and category.id != asset.category_id:
        domain.require(
            db.scalar(select(Loan.id).where(Loan.asset_id == asset.id)) is None,
            "Tài sản đã có phiếu mượn; giữ nguyên loại để bảo toàn lịch sử và nhu cầu liên kết.",
            409,
        )
    image = upload_path(db, actor, data.image_path, asset.image_path if asset else None)
    if image:
        domain.require(not image.endswith(".pdf"), "Ảnh tài sản cần là PNG, JPG hoặc WEBP.")
    if not asset:
        asset = Asset(
            unit_id=actor.unit_id,
            status="CHO_CHIA_SE" if domain.manages(actor, actor.unit_id) else "CHO_DUYET",
        )
        db.add(asset)
    elif asset.status == "TU_CHOI":
        asset.status = "CHO_DUYET"
    asset.name, asset.category_id, asset.location_id = (
        data.name,
        category.id,
        location.id,
    )
    asset.custodian_id, asset.description, asset.condition = (
        custodian.id,
        data.description,
        data.condition,
    )
    asset.image_path = image
    db.flush()
    event(
        db,
        asset.id,
        actor.id,
        "Cập nhật hồ sơ tài sản."
        if asset_id
        else "Quản lý thêm tài sản và tự động duyệt chia sẻ."
        if asset.status == "CHO_CHIA_SE"
        else "Thêm tài sản, chờ quản lý chi nhánh duyệt.",
    )
    db.flush()
    db.refresh(asset)
    return asset


def lifecycle_event(db, actor, asset_id, data):
    asset = locked(db, Asset, asset_id)
    domain.require(not asset.withdrawn, "Không tìm thấy tài sản.", 404)
    domain.require(
        asset.status not in {"CHO_DUYET", "TU_CHOI"},
        "Cần duyệt đăng ký tài sản trước khi ghi nhận vòng đời.",
        409,
    )
    manager = domain.manages(actor, asset.unit_id)
    held = db.scalar(
        select(Loan.id).where(
            Loan.asset_id == asset.id,
            Loan.borrower_id == actor.id,
            Loan.status.in_(domain.HOLDING),
        )
    )
    domain.require(
        manager or (data.kind == "SU_CO" and held is not None),
        "Bạn không được xử lý vòng đời tài sản này.",
        403,
    )
    # A borrower may report an incident, but a manager must receive the item
    # before processing it or making a lifecycle decision.
    if manager or data.kind != "SU_CO":
        any_holder = db.scalar(
            select(Loan.id).where(Loan.asset_id == asset.id, Loan.status.in_(domain.HOLDING))
        )
        domain.require(
            any_holder is None,
            "Phải nhận trả tài sản trước khi xử lý và đánh giá vòng đời.",
            409,
        )
        domain.require(asset.status != "CHO_THU_HOI", "Tài sản đang chờ thu hồi.", 409)
    if data.kind == "SU_CO":
        domain.require(data.decision is None, "Báo sự cố chưa phải quyết định đánh giá.")
        if asset.status != "CHO_THU_HOI":
            asset.status = "BAO_TRI"
    elif data.kind == "DANH_GIA":
        domain.require(
            data.decision is not None,
            "Đánh giá cần có quyết định xử lý.",
        )
        cancel_pending(db, asset, actor, data.content, data.cancel_pending)
        if data.decision == "TIEP_TUC":
            domain.require(
                asset.unit.active
                and asset.location.active
                and asset.category.active
                and asset.custodian.active,
                "Đơn vị, địa điểm, loại tài sản và người phụ trách phải đang hoạt động.",
                409,
            )
            domain.require(
                bool(data.condition),
                "Vui lòng ghi tình trạng sau kiểm tra trước khi cho chia sẻ lại.",
            )
        if data.condition:
            asset.condition = data.condition
        asset.status = {
            "TIEP_TUC": "CHO_CHIA_SE",
            "BAO_TRI": "BAO_TRI",
        }[data.decision]
    else:
        domain.require(data.decision is None, "Quyết định chỉ dùng trong bước đánh giá.")
    if data.kind != "DANH_GIA" and data.cancel_pending:
        domain.require_manager(actor, asset.unit_id)
        cancel_pending(db, asset, actor, data.content, True)
    event(db, asset.id, actor.id, data.content, data.kind, data.basis, data.decision)
    db.flush()
    db.refresh(asset)
    return asset


def review_asset(db, actor, asset_id, data):
    asset = locked(db, Asset, asset_id)
    domain.require(not asset.withdrawn, "Không tìm thấy tài sản.", 404)
    domain.require_manager(actor, asset.unit_id)
    domain.require(
        data.version == asset.version.hex(), "Hồ sơ đã thay đổi. Hãy tải lại trước khi duyệt.", 409
    )
    domain.require(asset.status == "CHO_DUYET", "Tài sản không còn ở trạng thái Chờ duyệt.", 409)
    if data.approve:
        domain.require(
            asset.unit.active
            and asset.category.active
            and asset.location.active
            and asset.custodian.active,
            "Đơn vị, địa điểm, loại và người phụ trách cần đang hoạt động.",
            409,
        )
        asset.status = "CHO_CHIA_SE"
    else:
        domain.require(len(data.reason.strip()) >= 5, "Vui lòng ghi lý do từ chối.")
        asset.status = "TU_CHOI"
    event(
        db,
        asset.id,
        actor.id,
        f"{'Duyệt' if data.approve else 'Từ chối'} đăng ký tài sản. {data.reason}",
    )
    db.flush()
    db.refresh(asset)
    return asset


def withdraw_asset(db, actor, asset_id, data):
    asset = locked(db, Asset, asset_id)
    domain.require(
        asset.unit_id == actor.unit_id and asset.custodian_id == actor.id,
        "Chỉ người phụ trách được thu hồi tài sản.",
        403,
    )
    if asset.withdrawn:
        return dict(pending=False, deleted_loans=0, message="Đã thu hồi tài sản.")
    if asset.status == "CHO_THU_HOI":
        return dict(pending=True, deleted_loans=0, message="Tài sản đang chờ nhận trả để thu hồi.")
    domain.require(
        data.version == asset.version.hex(),
        "Hồ sơ đã thay đổi. Hãy tải lại trước khi thu hồi.",
        409,
    )
    held = db.scalar(
        select(Loan.id).where(Loan.asset_id == asset.id, Loan.status.in_(domain.HOLDING))
    )
    deleted = delete_pending_for_withdrawal(db, asset, actor)
    if held is not None:
        loan = locked(db, Loan, held)
        loan.reason = (
            f"{domain.WITHDRAWAL_REASON}. {loan.reason}"
            if loan.reason
            else domain.WITHDRAWAL_REASON
        )[:500]
        asset.status = "CHO_THU_HOI"
        message = "Đã yêu cầu thu hồi. Tài sản sẽ ẩn sau khi hoàn tất nhận trả."
    else:
        asset.withdrawn = True
        message = "Đã thu hồi tài sản."
    event(db, asset.id, actor.id, f"{message} Lý do: {domain.WITHDRAWAL_REASON}.")
    db.flush()
    return dict(pending=held is not None, deleted_loans=deleted, message=message)
