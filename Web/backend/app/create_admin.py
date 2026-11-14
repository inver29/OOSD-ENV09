"""Tạo quản trị đầu tiên bằng dữ liệu người triển khai nhập, không có mật khẩu cố định."""

from getpass import getpass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .bootstrap import initialize
from .db import session_factory
from .models import Grant, Unit, User
from .schemas import UserInput
from .security import hash_password


def main():
    username = input("Tên đăng nhập: ").strip().lower()
    name = input("Họ tên: ").strip()
    email = input("Email: ").strip().lower()
    unit_name = input("Tên đơn vị: ").strip()
    address = input("Địa chỉ cụ thể của đơn vị: ").strip()
    password = getpass("Mật khẩu (ít nhất 8 ký tự): ")
    if password != getpass("Nhập lại mật khẩu: "):
        raise ValueError("Mật khẩu nhập lại chưa khớp.")
    if not 2 <= len(unit_name) <= 150:
        raise ValueError("Tên đơn vị phải có 2–150 ký tự.")
    if not 8 <= len(address) <= 300:
        raise ValueError("Địa chỉ phải có 8–300 ký tự.")
    data = UserInput(
        username=username, name=name, email=email, unit_id=1, roles=["QUAN_TRI"], password=password
    )
    engine = initialize()
    try:
        with session_factory(engine).begin() as db:
            unit = db.scalar(select(Unit).where(Unit.name == unit_name))
            if unit is None:
                unit = Unit(name=unit_name, address=address, active=True)
                db.add(unit)
                db.flush()
            if not unit.active:
                raise ValueError("Đơn vị đã ngừng hoạt động.")
            db.add(
                User(
                    username=data.username,
                    name=data.name,
                    email=data.email,
                    unit_id=unit.id,
                    password_hash=hash_password(password),
                    active=True,
                    grants=[Grant(role="QUAN_TRI")],
                )
            )
        print("Đã tạo tài khoản quản trị.")
    except IntegrityError:
        raise ValueError(
            "Tên đăng nhập hoặc email đã tồn tại. Không thay đổi tài khoản đang có."
        ) from None
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
