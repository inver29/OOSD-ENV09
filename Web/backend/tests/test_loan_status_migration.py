from sqlalchemy import text

from backend.app.bootstrap import initialize


def test_legacy_loan_codes_migrate_and_saved_filters_still_work(env, database):
    config, engine = database
    old_codes = {"CHO_BAN_GIAO": "DA_DUYET", "DA_HOAN_TRA": "DA_DONG"}
    constraints = (
        "CK_PhieuMuon_TrangThai",
        "CK_PhieuMuon_DaDuyet",
        "CK_PhieuMuon_DangMuon",
        "CK_PhieuMuon_DaDong",
    )
    read_loans = text("""
        SELECT MaPhieuMuon, TrangThai, MaYeuCau, MaNhuCauMuaMoi, MaNguoiDuyet,
               CAST(GiaoLuc AS nvarchar(40)), CAST(TraLuc AS nvarchar(40))
        FROM dbo.PhieuMuon ORDER BY MaPhieuMuon
    """)
    with engine.begin() as connection:
        before = connection.execute(read_loans).all()
        assert old_codes.keys() <= {row.TrangThai for row in before}
        definitions = {}
        for name in constraints:
            definitions[name] = connection.scalar(
                text("SELECT definition FROM sys.check_constraints WHERE name = :name"),
                {"name": name},
            )
            connection.exec_driver_sql(f"ALTER TABLE dbo.PhieuMuon DROP CONSTRAINT {name}")
        for new, old in old_codes.items():
            connection.execute(
                text("UPDATE dbo.PhieuMuon SET TrangThai=:old WHERE TrangThai=:new"),
                {"old": old, "new": new},
            )
        for name, definition in definitions.items():
            for new, old in old_codes.items():
                definition = definition.replace(f"N'{new}'", f"N'{old}'")
            connection.exec_driver_sql(
                f"ALTER TABLE dbo.PhieuMuon WITH CHECK ADD CONSTRAINT {name} CHECK {definition}"
            )
    for _ in range(2):
        migrated = initialize(config)
        migrated.dispose()
    with engine.connect() as connection:
        assert connection.execute(read_loans).all() == before
        (enabled, trusted) = connection.execute(
            text("""
            SELECT COUNT(*), SUM(CASE WHEN is_not_trusted = 0 THEN 1 ELSE 0 END)
            FROM sys.check_constraints WHERE parent_object_id = OBJECT_ID(N'dbo.PhieuMuon')
                  AND is_disabled = 0
        """)
        ).one()
        assert enabled == trusted
    for username, status in (("an", "CHO_BAN_GIAO"), ("chi", "DA_HOAN_TRA")):
        client = env["login"](username)
        current = client.get("/api/loans", params={"status": status})
        legacy = client.get("/api/loans", params={"status": old_codes[status]})
        assert current.status_code == legacy.status_code == 200
        assert current.json() == legacy.json()
        assert current.json()["items"]
        assert {item["status"] for item in current.json()["items"]} == {status}
