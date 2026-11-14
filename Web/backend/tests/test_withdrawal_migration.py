from sqlalchemy import text

from backend.app.bootstrap import initialize


def test_old_states_migrate_without_deleting_assets_loans_or_history(env, database):
    config, engine = database
    assert config.db_name.startswith("ENV09_Test_")
    paused = env["assets"]["Máy in HP LaserJet"]
    retired = env["assets"]["Webcam Logitech C920"]
    with engine.begin() as connection:
        connection.exec_driver_sql("ALTER TABLE dbo.TaiSan DROP CONSTRAINT CK_TaiSan_TrangThai")
        connection.exec_driver_sql("""
            ALTER TABLE dbo.TaiSan ADD CONSTRAINT CK_TaiSan_TrangThai CHECK (
                TrangThai IN (N'CHO_DUYET', N'TU_CHOI', N'CHO_CHIA_SE', N'TAM_NGUNG', N'BAO_TRI', N'NGUNG_SU_DUNG'))
        """)
        connection.execute(
            text("UPDATE dbo.TaiSan SET TrangThai=N'TAM_NGUNG' WHERE MaTaiSan=:id"), {"id": paused}
        )
        connection.execute(
            text("UPDATE dbo.TaiSan SET TrangThai=N'NGUNG_SU_DUNG' WHERE MaTaiSan=:id"),
            {"id": retired},
        )
        connection.exec_driver_sql(
            "ALTER TABLE dbo.SuKienVongDoi DROP CONSTRAINT CK_SuKienVongDoi_QuyetDinh"
        )
        connection.exec_driver_sql("""
            ALTER TABLE dbo.SuKienVongDoi ADD CONSTRAINT CK_SuKienVongDoi_QuyetDinh CHECK (
                QuyetDinh IS NULL OR QuyetDinh IN (N'TIEP_TUC', N'BAO_TRI', N'NGUNG_SU_DUNG'))
        """)
        connection.execute(
            text("""
            INSERT dbo.SuKienVongDoi (MaTaiSan, MaNguoiGhi, GhiLuc, Loai, NoiDung, QuyetDinh)
            VALUES (:asset, :actor, SYSDATETIMEOFFSET(), N'DANH_GIA', N'Quyết định từ phiên bản cũ.', N'NGUNG_SU_DUNG')
        """),
            {"asset": retired, "actor": env["users"]["ql.hn"]},
        )
        tables = ("TaiSan", "PhieuMuon", "BienBanGiaoNhan", "SuKienVongDoi")
        before = {
            table: connection.scalar(text(f"SELECT COUNT(*) FROM dbo.{table}")) for table in tables
        }
    for _ in range(2):
        migrated = initialize(config)
        migrated.dispose()
    with engine.connect() as connection:
        assert {
            table: connection.scalar(text(f"SELECT COUNT(*) FROM dbo.{table}")) for table in tables
        } == before
        assert (
            connection.scalar(
                text("SELECT TrangThai FROM dbo.TaiSan WHERE MaTaiSan=:id"), {"id": paused}
            )
            == "BAO_TRI"
        )
        assert connection.scalar(
            text("SELECT DaThuHoi FROM dbo.TaiSan WHERE MaTaiSan=:id"), {"id": retired}
        )
        assert (
            connection.scalar(
                text(
                    "SELECT QuyetDinh FROM dbo.SuKienVongDoi WHERE NoiDung=N'Quyết định từ phiên bản cũ.'"
                )
            )
            == "THU_HOI"
        )
        definition = connection.scalar(
            text("SELECT definition FROM sys.check_constraints WHERE name=N'CK_TaiSan_TrangThai'")
        )
        assert "TAM_NGUNG" not in definition and "NGUNG_SU_DUNG" not in definition
        assert "CHO_THU_HOI" in definition
