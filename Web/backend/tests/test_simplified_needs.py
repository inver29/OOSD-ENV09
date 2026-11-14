from datetime import timedelta

import pytest
from sqlalchemy import select, text

from backend.app.bootstrap import initialize
from backend.app.models import LifecycleEvent, Need
from backend.tests.test_quick_workflows import need_data
from backend.tests.test_workflows import approve, confirm, create, request_data


@pytest.mark.parametrize("alternative", ["THUE_NGOAI", "DUNG_TAI_SAN_KHAC"])
def test_removed_alternatives_are_rejected_by_api(env, alternative):
    member = env["login"]("an")
    loan = request_data(env)
    need = {**need_data(env, loan), "alternative": alternative, "auto_submit": True}
    assert member.post("/api/needs", json=need).status_code == 405
    assert member.post("/api/loans", json={**loan, "new_need": need}).status_code == 422


def test_purchase_verification_and_indicator_work_without_attachments(env):
    member, owner, verifier = env["login"]("an"), env["login"]("ql.hn"), env["login"]("ql.hcm")
    payload = request_data(env)
    payload["new_need"] = {**need_data(env, payload), "alternative": "MUA_MOI"}
    loan = create(member, payload)
    approve(owner, loan)
    env["clock"][0] += timedelta(minutes=11)
    path = f"/api/loans/{loan['id']}"
    giao = owner.post(
        path + "/reports",
        json={
            "kind": "GIAO",
            "content": "Tài sản hoạt động tốt, đủ phụ kiện.",
            "condition": "Đạt",
            "confirm_self": True,
        },
    )
    assert giao.status_code == 200, giao.text
    assert confirm(member, loan, giao.json()).status_code == 200
    tra = member.post(
        path + "/return", json={"content": "Trả đủ hiện vật và các phụ kiện.", "condition": "Đạt"}
    )
    assert tra.status_code == 200
    assert confirm(owner, loan, tra.json()).status_code == 200
    need = member.get(f"/api/needs/{loan['need_id']}").json()
    verify = {
        "accepted": True,
        "intended_purchase": True,
        "purpose_met": True,
        "conclusion": "Đã đối chiếu khai báo mua mới và phiếu đã hoàn trả.",
    }
    blocked = verifier.post(f"/api/needs/{need['id']}/verify", json=verify)
    assert blocked.status_code == 409 and "khai báo kết quả mua mới" in blocked.json()["message"]
    env["clock"][0] += timedelta(hours=3)
    assert (
        member.post(f"/api/needs/{need['id']}/outcome", json={"purchased": False}).status_code
        == 200
    )
    result = verifier.post(f"/api/needs/{need['id']}/verify", json=verify)
    assert result.status_code == 200, result.text
    assert (
        result.json()["status"] == "DA_XAC_MINH"
        and result.json()["verification"]["evidence_path"] is None
    )
    report = verifier.get(
        "/api/reports/avoidance",
        params={
            "start": (env["clock"][0] - timedelta(days=1)).isoformat(),
            "end": (env["clock"][0] + timedelta(days=1)).isoformat(),
        },
    ).json()
    assert (report["total"], report["avoided"], report["rate"]) == (1, 1, 100.0)


def test_postponed_need_cannot_be_verified_as_an_intended_purchase(env):
    from backend.tests.test_withdrawal_flow import completed_booking

    member, _, loan = completed_booking(env, alternative="HOAN_NHU_CAU")
    manager = env["login"]("ql.hcm")
    need = member.get(f"/api/needs/{loan['need_id']}").json()
    verify = {
        "accepted": True,
        "intended_purchase": True,
        "purpose_met": False,
        "conclusion": "Đối chiếu phương án đã khai báo lúc tạo nhu cầu.",
    }
    assert member.post(f"/api/needs/{need['id']}/outcome", json={"purchased": False}).status_code == 200
    assert manager.post(f"/api/needs/{need['id']}/verify", json=verify).status_code == 400
    verify["intended_purchase"] = False
    assert manager.post(f"/api/needs/{need['id']}/verify", json=verify).status_code == 200


def test_evaluation_without_basis_still_requires_decision_and_condition(env):
    manager = env["login"]("ql.hn")
    asset_id = env["assets"]["Máy in Brother HL-L2321D"]
    path = f"/api/assets/{asset_id}/events"
    payload = {"kind": "DANH_GIA", "content": "Đã kiểm tra và sửa bộ phận kéo giấy."}
    assert manager.post(path, json=payload).status_code == 400
    payload["decision"] = "TIEP_TUC"
    assert manager.post(path, json=payload).status_code == 400
    payload["condition"] = "Hoạt động ổn định sau kiểm tra."
    response = manager.post(path, json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "CHO_CHIA_SE"
    with env["sessions"]() as db:
        event = db.scalar(
            select(LifecycleEvent).where(
                LifecycleEvent.asset_id == asset_id, LifecycleEvent.kind == "DANH_GIA"
            )
        )
        assert event.basis is None and event.decision == "TIEP_TUC"


def test_reverification_preserves_historical_attachments_when_omitted(env):
    creator, manager = env["login"]("chi"), env["login"]("ql.hn")
    need = creator.get("/api/needs").json()["items"][-1]
    original = manager.get(f"/api/needs/{need['id']}").json()
    response = manager.post(
        f"/api/needs/{need['id']}/verify",
        json={
            "accepted": True,
            "intended_purchase": True,
            "purpose_met": True,
            "conclusion": "Đối chiếu lại kết quả và giữ nguyên hồ sơ lịch sử.",
        },
    )
    assert response.status_code == 200
    assert (
        response.json()["verification"]["evidence_path"]
        == original["verification"]["evidence_path"]
    )
    with env["sessions"]() as db:
        assert db.get(Need, need["id"]).evidence_path == original["evidence_path"]


def test_existing_database_migration_relaxes_basis_without_losing_history(env, database):
    config, engine = database
    assert config.db_name.startswith("ENV09_Test_")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "ALTER TABLE dbo.SuKienVongDoi DROP CONSTRAINT CK_SuKienVongDoi_DanhGia"
        )
        connection.exec_driver_sql(
            "ALTER TABLE dbo.SuKienVongDoi ADD CONSTRAINT CK_SuKienVongDoi_DanhGia CHECK ((Loai=N'DANH_GIA' AND CanCu IS NOT NULL AND QuyetDinh IS NOT NULL) OR (Loai<>N'DANH_GIA' AND QuyetDinh IS NULL))"
        )
        before = connection.scalar(text("SELECT COUNT(*) FROM dbo.SuKienVongDoi"))
    for _ in range(2):
        migrated = initialize(config)
        migrated.dispose()
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT COUNT(*) FROM dbo.SuKienVongDoi")) == before
        definition = connection.scalar(
            text(
                "SELECT definition FROM sys.check_constraints WHERE name=N'CK_SuKienVongDoi_DanhGia'"
            )
        )
        assert "CanCu" not in definition
