from datetime import UTC, datetime, timedelta

PENDING = {"CHO_DUYET", "CHO_BAN_GIAO"}
HOLDING = {"DANG_MUON", "CHO_XAC_NHAN_TRA"}
OPEN = PENDING | HOLDING
ROLES = {"THANH_VIEN", "QUAN_LY", "QUAN_TRI"}
WITHDRAWAL_REASON = "Người phụ trách đã thu hồi tài sản"


def now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


class BusinessError(Exception):
    def __init__(self, message: str, status: int = 400):
        self.message = message
        self.status = status


def require(condition: bool, message: str, status: int = 400):
    if not condition:
        raise BusinessError(message, status)


def manages(user, unit_id: int) -> bool:
    return "QUAN_LY" in user.roles and user.unit_id == unit_id


def require_member(user):
    require(
        bool(set(user.roles) & {"THANH_VIEN", "QUAN_LY"}),
        "Tài khoản chưa được cấp quyền nghiệp vụ.",
        403,
    )


def require_manager(user, unit_id: int):
    require(
        manages(user, unit_id),
        "Bạn không quản lý tài sản hoặc hồ sơ của đơn vị này.",
        403,
    )


def require_admin(user):
    require("QUAN_TRI" in user.roles, "Chức năng chỉ dành cho quản trị hệ thống.", 403)


def check_period(start: datetime, end: datetime):
    require(start.tzinfo is not None and end.tzinfo is not None, "Thời gian cần có múi giờ.")
    require(start < end, "Thời gian kết thúc phải sau thời gian bắt đầu.")


def pickup_deadline(loan):
    return min(loan.end_at, loan.start_at + timedelta(hours=loan.policy.pickup_hours))
