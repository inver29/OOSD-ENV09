"""Tạo database mới và áp dụng SQL gốc; không xóa dữ liệu đang có."""

import argparse
import re

from sqlalchemy import inspect, text

from .config import ROOT, settings
from .db import make_engine, session_factory
from .models import Base, WithdrawalNotice


def initialize(config=settings):
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,99}", config.db_name):
        raise ValueError("Tên database chỉ được chứa chữ, số và dấu gạch dưới.")
    master = make_engine(config, database="master")
    try:
        with master.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            exists = connection.scalar(text("SELECT DB_ID(:name)"), {"name": config.db_name})
            if exists is None:
                connection.exec_driver_sql(f"CREATE DATABASE [{config.db_name}]")
    finally:
        master.dispose()
    engine = make_engine(config)
    existing = set(inspect(engine).get_table_names())
    expected = set(Base.metadata.tables)
    if existing & expected:
        if not (expected - {WithdrawalNotice.__tablename__}) <= existing:
            engine.dispose()
            raise RuntimeError(
                "Database có một phần cấu trúc ENV09. Không ghi đè; hãy kiểm tra schema trước."
            )
        # Apply explicit migrations without deleting the existing business data.
        with engine.begin() as connection:
            for migration in (
                "002_unit_address.sql",
                "003_asset_review.sql",
                "004_optional_evaluation_basis.sql",
                "005_need_alternatives.sql",
                "006_unified_withdrawal.sql",
                "007_single_account_role.sql",
                "008_withdrawal_notifications.sql",
                "009_loan_status_codes.sql",
            ):
                connection.exec_driver_sql(
                    (ROOT / "sql" / migration).read_text(encoding="utf-8-sig")
                )
        inspector = inspect(engine)
        for name, table in Base.metadata.tables.items():
            actual = {column["name"] for column in inspector.get_columns(name)}
            if actual != {column.name for column in table.columns}:
                engine.dispose()
                raise RuntimeError(
                    f"Cấu trúc bảng {name} khác script ENV09. Không tự thay đổi database hiện hữu."
                )
    else:
        script = (ROOT / "sql" / "001_schema.sql").read_text(encoding="utf-8-sig")
        batches = re.split(r"^\s*GO\s*$", script, flags=re.MULTILINE | re.IGNORECASE)
        with engine.begin() as connection:
            for batch in batches:
                if re.search(r"\b(CREATE DATABASE|USE ENV09)\b", batch, flags=re.IGNORECASE):
                    continue
                if batch.strip():
                    connection.exec_driver_sql(batch)
    return engine


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seed", action="store_true", help="Thêm bộ dữ liệu minh họa vào database rỗng"
    )
    args = parser.parse_args()
    engine = initialize()
    if args.seed or settings.seed_demo:
        from .seed import seed_demo

        with session_factory(engine).begin() as db:
            seed_demo(db, settings)
    print(f"Database {settings.db_name}: sẵn sàng ({len(Base.metadata.tables)} bảng).")
    engine.dispose()
