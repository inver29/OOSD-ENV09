"""Khởi tạo database ENV09 từ tập lệnh SQL."""

import argparse
import re

from sqlalchemy import inspect, text

from .config import ROOT, settings
from .db import make_engine, session_factory
from .models import Base


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
    try:
        with engine.begin() as connection:
            inspector = inspect(connection)
            existing = set(inspector.get_table_names(schema="dbo"))
            expected = set(Base.metadata.tables)
            if expected.isdisjoint(existing):
                script = (ROOT / "SQL" / "ENV09.sql").read_text(encoding="utf-8-sig")
                batches = re.split(r"^[ \t]*GO[ \t]*$", script, flags=re.MULTILINE | re.IGNORECASE)
                # CREATE DATABASE and USE are for SSMS. This connection uses APP_DB_NAME.
                for batch in batches[2:]:
                    if batch.strip():
                        connection.exec_driver_sql(batch)
            elif not expected <= existing:
                raise RuntimeError("Database thiếu bảng ENV09. Dùng APP_DB_NAME mới để cài lại.")

            for name, table in Base.metadata.tables.items():
                actual = {column["name"] for column in inspector.get_columns(name, schema="dbo")}
                if actual != {column.name for column in table.columns}:
                    raise RuntimeError(f"Bảng {name} khác ENV09.sql. Dùng APP_DB_NAME mới để cài lại.")

            status_rule = connection.exec_driver_sql(
                "SELECT OBJECT_DEFINITION(OBJECT_ID(N'dbo.CK_PhieuMuon_TrangThai'))"
            ).scalar_one() or ""
            if "CHO_BAN_GIAO" not in status_rule or "DA_HOAN_TRA" not in status_rule:
                raise RuntimeError("Database dùng mã phiếu mượn cũ. Dùng APP_DB_NAME mới để cài lại.")
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
