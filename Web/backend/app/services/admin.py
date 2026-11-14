from sqlalchemy import func, or_, select

from .. import domain
from ..models import Asset, Category, Grant, Handover, Loan, Location, Need, Policy, Unit, User
from ..security import hash_password
from .common import get_or_404, locked
from .needs import completed_need

CATALOGS = {"units": Unit, "categories": Category, "locations": Location}


def user_open_work(db, user_id):
    return db.scalar(
        select(Loan.id).where(
            Loan.status.in_(domain.OPEN),
            or_(
                Loan.borrower_id == user_id,
                Loan.id.in_(
                    select(Handover.loan_id).where(
                        Handover.status != "HOAN_TAT",
                        or_(Handover.giver_id == user_id, Handover.receiver_id == user_id),
                    )
                ),
                Loan.asset_id.in_(select(Asset.id).where(Asset.custodian_id == user_id)),
            ),
        )
    )


def save_user(db, actor, data, user_id=None):
    domain.require_admin(actor)
    role = data.roles[0]
    unit = get_or_404(db, Unit, data.unit_id)
    domain.require(unit.active, "Đơn vị đã ngừng hoạt động.")
    username, email = data.username.lower(), data.email.lower()
    user = locked(db, User, user_id) if user_id else None
    other = db.scalar(
        select(User.id).where(
            or_(User.username == username, User.email == email),
            User.id != (user_id or 0),
        )
    )
    domain.require(other is None, "Tên đăng nhập hoặc email đã được sử dụng.", 409)
    if user:
        sensitive_change = (
            user.unit_id != data.unit_id or not data.active or set(user.roles) - set(data.roles)
        )
        if sensitive_change:
            domain.require(
                user_open_work(db, user.id) is None,
                "Tài khoản còn trách nhiệm trên phiếu đang mở. Hãy xử lý trước khi đổi quyền/đơn vị hoặc khóa.",
                409,
            )
            custodian = db.scalar(
                select(Asset.id).where(
                    Asset.custodian_id == user.id,
                    Asset.withdrawn == False,
                )
            )
            domain.require(
                custodian is None,
                "Người phụ trách cần hoàn tất thu hồi các tài sản trước.",
                409,
            )
            pending_need = db.scalar(
                select(Need.id).where(
                    Need.creator_id == user.id,
                    Need.status.in_({"NHAP", "CHO_XAC_MINH"}),
                    completed_need(),
                )
            )
            domain.require(pending_need is None, "Tài khoản còn nhu cầu đang xử lý.", 409)
        if user.id == actor.id:
            domain.require(
                data.active and "QUAN_TRI" in data.roles,
                "Không thể tự khóa hoặc tự bỏ quyền quản trị.",
            )
        if "QUAN_TRI" in user.roles and (not data.active or "QUAN_TRI" not in data.roles):
            count = db.scalar(
                select(func.count())
                .select_from(User)
                .join(Grant)
                .where(User.active == True, Grant.role == "QUAN_TRI", User.id != user.id)
            )
            domain.require(count > 0, "Phải còn ít nhất một quản trị hoạt động.")
        # Update the existing row so a role change respects the unique user constraint.
        grant = next((g for g in user.grants if g.role == role), None)
        if grant is None:
            grant = user.grants[0] if user.grants else Grant()
        grant.role = role
        user.grants[:] = [grant]
    else:
        domain.require(data.password is not None, "Vui lòng nhập mật khẩu cho tài khoản mới.")
        user = User()
        db.add(user)
        user.grants = [Grant(role=role)]
    user.username, user.email, user.name, user.unit_id, user.active = (
        username,
        email,
        data.name,
        data.unit_id,
        data.active,
    )
    if data.password:
        user.password_hash = hash_password(data.password)
    db.flush()
    db.refresh(user)
    return user


def save_catalog(db, actor, kind, data, record_id=None):
    domain.require_admin(actor)
    domain.require(kind in CATALOGS, "Danh mục không tồn tại.", 404)
    model = CATALOGS[kind]
    item = locked(db, model, record_id) if record_id else model()
    duplicate_query = select(model.id).where(model.name == data.name, model.id != (record_id or 0))
    if kind == "locations":
        duplicate_query = duplicate_query.where(model.unit_id == data.unit_id)
    duplicate = db.scalar(duplicate_query)
    domain.require(duplicate is None, "Tên danh mục đã tồn tại.", 409)
    if record_id and not data.active:
        if kind == "units":
            referenced = db.scalar(
                select(User.id).where(User.unit_id == item.id, User.active == True)
            )
        elif kind == "categories":
            referenced = db.scalar(
                select(Asset.id).where(
                    Asset.category_id == item.id,
                    Asset.withdrawn == False,
                )
            )
        else:
            referenced = db.scalar(
                select(Asset.id).where(
                    Asset.location_id == item.id,
                    Asset.withdrawn == False,
                )
            )
        domain.require(referenced is None, "Danh mục đang được sử dụng bởi dữ liệu hoạt động.", 409)
    if kind == "units":
        domain.require(
            bool(data.address and len(data.address) >= 8),
            "Vui lòng nhập địa chỉ cụ thể của đơn vị (ít nhất 8 ký tự).",
        )
        item.address = data.address
    if kind == "locations":
        domain.require(data.unit_id is not None, "Vui lòng chọn đơn vị của địa điểm.")
        unit = get_or_404(db, Unit, data.unit_id)
        domain.require(unit.active, "Đơn vị đã ngừng hoạt động.")
        if record_id and item.unit_id != data.unit_id:
            domain.require(
                not db.scalar(select(Asset.id).where(Asset.location_id == item.id)),
                "Không đổi đơn vị của địa điểm đã có tài sản.",
                409,
            )
        item.unit_id, item.description = data.unit_id, data.description
    item.name, item.active = data.name, data.active
    db.add(item)
    db.flush()
    return item


def save_policy(db, actor, data, policy_id=None):
    domain.require_admin(actor)
    policy = locked(db, Policy, policy_id) if policy_id else Policy()
    if policy_id:
        domain.require(
            not db.scalar(select(Loan.id).where(Loan.policy_id == policy.id)),
            "Chính sách đã dùng: hãy tạo chính sách mới để giữ lịch sử.",
            409,
        )
    duplicate = db.scalar(
        select(Policy.id).where(
            Policy.effective_from == data.effective_from, Policy.id != (policy_id or 0)
        )
    )
    domain.require(duplicate is None, "Đã có chính sách tại thời điểm hiệu lực này.", 409)
    policy.name, policy.max_days = data.name, data.max_days
    policy.buffer_hours, policy.pickup_hours, policy.effective_from = (
        data.buffer_hours,
        data.pickup_hours,
        data.effective_from,
    )
    db.add(policy)
    db.flush()
    return policy
