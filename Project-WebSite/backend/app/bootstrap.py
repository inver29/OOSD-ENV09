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
    script = (ROOT / "SQL" / "ENV09.sql").read_text(encoding="utf-8-sig")
    schema, upgrades = script.split("\n-- NANG CAP DATABASE CU\n", maxsplit=1)
    go = re.compile(r"^[ \t]*GO[ \t]*$", re.MULTILINE | re.IGNORECASE)
    engine = make_engine(config)
    try:
        with engine.begin() as connection:
            inspector = inspect(connection)
            existing = set(inspector.get_table_names(schema="dbo"))
            expected = set(Base.metadata.tables)
            if existing & expected:
                required = expected - {WithdrawalNotice.__tablename__}
                if not required <= existing:
                    raise RuntimeError("Database có một phần cấu trúc ENV09. Hãy kiểm tra các bảng hiện có.")
                batches = go.split(upgrades)
            else:
                # CREATE DATABASE and USE are for SSMS. This connection uses APP_DB_NAME.
                batches = go.split(schema)[2:]

            # Keep pyodbc from closing a batch after the first DML row count.
            nocount_was_on = connection.exec_driver_sql("SELECT @@OPTIONS & 512").scalar_one()
            if not nocount_was_on:
                connection.exec_driver_sql("SET NOCOUNT ON")
            for batch in batches:
                if batch.strip():
                    connection.exec_driver_sql(batch)
            if not nocount_was_on:
                connection.exec_driver_sql("SET NOCOUNT OFF")

            inspector.clear_cache()
            for name, table in Base.metadata.tables.items():
                actual = {column["name"] for column in inspector.get_columns(name, schema="dbo")}
                if actual != {column.name for column in table.columns}:
                    raise RuntimeError(f"Cấu trúc bảng {name} không khớp với ENV09.sql.")
    except Exception:
        engine.dispose()
        raise
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
