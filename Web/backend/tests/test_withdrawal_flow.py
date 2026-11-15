from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from sqlalchemy import select

from backend.app.models import Asset, Handover, LifecycleEvent, Loan, Need
from backend.tests.test_quick_workflows import need_data
from backend.tests.test_workflows import approve, confirm, create, delivered, report, request_data


def completed_booking(env, alternative="MUA_MOI", username="an", asset_id=None, owner="ql.hn"):
    member, manager = env["login"](username), env["login"](owner)
    payload = request_data(env, asset=asset_id)
    with env["sessions"]() as db:
        category = db.get(Asset, payload["asset_id"]).category_id
    payload["new_need"] = {
        **need_data(env, payload),
        "category_id": category,
        "alternative": alternative,
    }
    loan = create(member, payload)
    approve(manager, loan)
    env["clock"][0] += timedelta(minutes=11)
    giao = report(manager, loan)
    assert confirm(manager, loan, giao).status_code == 200
    assert confirm(member, loan, giao).status_code == 200
    tra = member.post(
        f"/api/loans/{loan['id']}/return",
        json={"content": "Trả đủ thiết bị và phụ kiện.", "condition": "Đạt"},
    )
    assert tra.status_code == 200
    assert confirm(manager, loan, tra.json()).status_code == 200
    return member, manager, loan


@pytest.mark.parametrize("condition", ["Đạt", "Hư hỏng"])
def test_requested_withdrawal_finishes_only_after_both_return_signatures(env, condition):
    member, manager, loan = delivered(env)
    with env["sessions"].begin() as db:
        db.get(Loan, loan["id"]).reason = "Đã đối chiếu lịch đào tạo."
    path = f"/api/assets/{loan['asset_id']}"
    before = manager.get(path).json()
    result = manager.post(path + "/withdraw", json={"version": before["version"]})
    assert result.status_code == 200 and result.json()["pending"]
    reason = member.get(f"/api/loans/{loan['id']}").json()["reason"]
    assert reason == "Người phụ trách đã thu hồi tài sản. Đã đối chiếu lịch đào tạo."
    waiting = manager.get(path).json()
    assert waiting["status"] == "CHO_THU_HOI" and waiting["holding"] and not waiting["withdrawn"]
    assert loan["asset_id"] in {
        a["id"] for a in manager.get("/api/assets?scope=own&page_size=100").json()["items"]
    }
    assert manager.post(path + "/withdraw", json={"version": before["version"]}).json()["pending"]
    for kind in ("DANH_GIA", "XU_LY", "SU_CO"):
        data = {"kind": kind, "content": "Không xử lý khi chưa nhận trả tài sản."}
        if kind == "DANH_GIA":
            data["decision"] = "BAO_TRI"
        assert manager.post(path + "/events", json=data).status_code == 409
    # A factual incident report from the borrower must not erase the pending withdrawal.
    assert (
        member.post(
            path + "/events",
            json={"kind": "SU_CO", "content": "Ghi nhận hiện trạng trong khi đang sử dụng."},
        ).status_code
        == 201
    )
    assert manager.get(path).json()["status"] == "CHO_THU_HOI"
    assert member.post("/api/loans", json=request_data(env)).status_code == 409
    tra = member.post(
        f"/api/loans/{loan['id']}/return",
        json={
            "content": "Đã mang thiết bị và các phụ kiện tới nơi nhận trả.",
            "condition": condition,
        },
    )
    assert tra.status_code == 200
    assert manager.get(path).status_code == 200  # One signature is insufficient.
    assert confirm(manager, loan, tra.json()).status_code == 200
    assert manager.get(path).status_code == 404
    retained = member.get(f"/api/loans/{loan['id']}").json()
    assert retained["status"] == "DA_HOAN_TRA" and retained["asset"]["status"] == "DA_THU_HOI"
    with env["sessions"]() as db:
        assert db.get(Asset, loan["asset_id"]).withdrawn
        assert db.get(Loan, loan["id"]).returned_at
        assert len(list(db.scalars(select(Handover).where(Handover.loan_id == loan["id"])))) == 2


def test_withdrawal_deletes_only_undelivered_vouchers_and_their_reports(env):
    member, manager = env["login"]("an"), env["login"]("ql.hn")
    payload = request_data(env)
    payload["new_need"] = need_data(env, payload)
    loan = create(member, payload)
    approve(manager, loan)
    env["clock"][0] += timedelta(minutes=11)
    giao = report(manager, loan)
    assert confirm(manager, loan, giao).status_code == 200
    path = f"/api/assets/{loan['asset_id']}"
    version = manager.get(path).json()["version"]
    result = manager.post(path + "/withdraw", json={"version": version})
    assert result.status_code == 200 and not result.json()["pending"]
    assert result.json()["deleted_loans"] >= 1
    assert manager.post(path + "/withdraw", json={"version": version}).status_code == 200
    inbox = member.get("/api/notifications").json()
    matches = [item for item in inbox["items"] if item["loan_id"] == loan["id"]]
    assert len(matches) == 1
    notice = matches[0]
    assert notice["asset_name"] == loan["asset_name"]
    assert notice["reason"] == "Người phụ trách đã thu hồi tài sản"
    assert notice["read_at"] is None
    read = f"/api/notifications/{notice['id']}/read"
    assert manager.get("/api/notifications").json()["items"] == []
    assert manager.post(read).status_code == 404
    assert member.post(read).status_code == 200
    assert member.post(read).status_code == 200
    refreshed = member.get("/api/notifications").json()
    assert refreshed["unread"] == inbox["unread"] - 1
    assert next(item for item in refreshed["items"] if item["id"] == notice["id"])["read_at"]
    assert member.get(f"/api/loans/{loan['id']}").status_code == 404
    with env["sessions"]() as db:
        assert db.get(Loan, loan["id"]) is None
        assert db.get(Handover, giao["id"]) is None
        assert db.get(Need, loan["need_id"]) is not None  # Initial declaration is retained.
        assert (
            db.scalar(
                select(LifecycleEvent.id).where(
                    LifecycleEvent.asset_id == loan["asset_id"],
                    LifecycleEvent.content.contains(
                        f"Hủy và xóa phiếu chưa giao #{loan['id']}. Lý do: Người phụ trách đã thu hồi tài sản."
                    ),
                )
            )
            is not None
        )
    assert member.get(f"/api/needs/{loan['need_id']}").status_code == 404
    assert member.get("/api/needs").json()["items"] == []


def test_withdrawal_racing_final_delivery_cannot_delete_a_delivered_loan(env):
    member, manager = env["login"]("an"), env["login"]("ql.hn")
    loan = create(member, request_data(env))
    approve(manager, loan)
    env["clock"][0] += timedelta(minutes=11)
    giao = report(manager, loan)
    assert confirm(manager, loan, giao).status_code == 200
    path = f"/api/assets/{loan['asset_id']}"
    version = manager.get(path).json()["version"]
    barrier = Barrier(2)

    def withdraw():
        barrier.wait(timeout=10)
        return manager.post(path + "/withdraw", json={"version": version}).status_code

    def deliver():
        barrier.wait(timeout=10)
        return confirm(member, loan, giao).status_code

    with ThreadPoolExecutor(2) as executor:
        f1, f2 = executor.submit(withdraw), executor.submit(deliver)
        assert f1.result() == 200
        assert f2.result() in {200, 404}
    with env["sessions"]() as db:
        asset, retained = db.get(Asset, loan["asset_id"]), db.get(Loan, loan["id"])
        if retained:
            assert retained.status == "DANG_MUON" and not asset.withdrawn
            assert asset.status == "CHO_THU_HOI"
        else:
            assert asset.withdrawn and db.get(Handover, giao["id"]) is None


def test_need_appears_after_completed_return_and_cannot_be_added_manually(env):
    member, manager = env["login"]("an"), env["login"]("ql.hn")
    payload = request_data(env)
    payload["new_need"] = need_data(env, payload)
    assert member.post("/api/needs", json=payload["new_need"]).status_code == 405
    loan = create(member, payload)
    need_path = f"/api/needs/{loan['need_id']}"
    assert member.get("/api/needs").json()["items"] == []
    assert member.get(need_path).status_code == 404
    assert member.put(need_path, json=payload["new_need"]).status_code == 405
    assert member.post(need_path + "/outcome", json={"purchased": False}).status_code == 409
    approve(manager, loan)
    env["clock"][0] += timedelta(minutes=11)
    giao = report(manager, loan)
    assert confirm(manager, loan, giao).status_code == 200
    assert confirm(member, loan, giao).status_code == 200
    assert member.get("/api/needs").json()["items"] == []
    tra = member.post(
        f"/api/loans/{loan['id']}/return",
        json={"content": "Thiết bị và phụ kiện đã được trả đầy đủ.", "condition": "Đạt"},
    ).json()
    assert member.get("/api/needs").json()["items"] == []
    assert confirm(manager, loan, tra).status_code == 200
    needs = member.get("/api/needs").json()["items"]
    assert [n["id"] for n in needs] == [loan["need_id"]]
    assert needs[0]["alternative"] == "HOAN_NHU_CAU"
    assert member.post(need_path + "/outcome", json={"purchased": False}).status_code == 200


def test_combined_booking_normalizes_fractional_seconds_before_sql_comparison(env):
    member = env["login"]("an")
    payload = request_data(env)
    payload["start_at"] = (env["clock"][0] + timedelta(minutes=10, microseconds=123456)).isoformat()
    payload["end_at"] = (env["clock"][0] + timedelta(hours=2, microseconds=123456)).isoformat()
    payload["new_need"] = need_data(env, payload)
    loan = create(member, payload)
    assert create(member, payload)["id"] == loan["id"]
    with env["sessions"]() as db:
        stored, need = db.get(Loan, loan["id"]), db.get(Need, loan["need_id"])
        assert stored.start_at == need.start_at and stored.end_at == need.end_at
        assert stored.start_at.microsecond == stored.end_at.microsecond == 0


def test_expiry_worker_skips_a_voucher_deleted_after_its_snapshot(env, monkeypatch):
    from backend.app.services import loans

    member, manager = env["login"]("an"), env["login"]("ql.hn")
    loan = create(member, request_data(env))
    approve(manager, loan)
    env["clock"][0] += timedelta(hours=3)
    original = loans.loan_context
    intercepted = []

    def withdraw_before_lock(db, loan_id):
        if loan_id == loan["id"]:
            path = f"/api/assets/{loan['asset_id']}"
            version = manager.get(path).json()["version"]
            assert manager.post(path + "/withdraw", json={"version": version}).status_code == 200
            intercepted.append(loan_id)
        return original(db, loan_id)

    monkeypatch.setattr(loans, "loan_context", withdraw_before_lock)
    loans.expire_due(env["sessions"])
    assert intercepted == [loan["id"]]
    with env["sessions"]() as db:
        assert db.get(Loan, loan["id"]) is None
        assert db.get(Asset, loan["asset_id"]).withdrawn
