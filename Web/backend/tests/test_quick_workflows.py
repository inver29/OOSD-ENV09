from datetime import timedelta

import pytest
from sqlalchemy import func, select

from backend.app.models import Loan, Need
from backend.tests.test_workflows import approve, confirm, create, request_data


def quick_delivery(env):
    member, manager = env["login"]("an"), env["login"]("ql.hn")
    loan = create(member, request_data(env))
    approve(manager, loan)
    env["clock"][0] += timedelta(minutes=11)
    data = dict(
        kind="GIAO",
        condition="Đạt",
        content="Đã kiểm tra đủ phụ kiện và hoạt động tốt.",
        confirm_self=True,
    )
    response = manager.post(f"/api/loans/{loan['id']}/reports", json=data)
    assert response.status_code == 200, response.text
    record = response.json()
    assert record["giver_confirmed_at"] and not record["receiver_confirmed_at"]
    assert member.get(f"/api/loans/{loan['id']}").json()["status"] == "CHO_BAN_GIAO"
    assert confirm(member, loan, record).status_code == 200
    assert member.get(f"/api/loans/{loan['id']}").json()["status"] == "DANG_MUON"
    return member, manager, loan


def return_payload(**extra):
    return dict(content="Kiểm tra hiện vật và phụ kiện khi hoàn trả.", condition="Đạt", **extra)


@pytest.mark.parametrize("condition,asset_status", [("Đạt", "CHO_CHIA_SE"), ("Hư hỏng", "BAO_TRI")])
def test_quick_handover_and_return_keep_two_independent_signatures(env, condition, asset_status):
    member, manager, loan = quick_delivery(env)
    path = f"/api/loans/{loan['id']}"
    payload = return_payload()
    payload["condition"] = condition
    response = member.post(path + "/return", json=payload)
    assert response.status_code == 200, response.text
    record = response.json()
    assert record["giver_id"] == env["users"]["an"]
    assert record["receiver_id"] == env["users"]["ql.hn"]
    assert record["giver_confirmed_at"] and not record["receiver_confirmed_at"]
    assert member.get(path).json()["status"] == "CHO_XAC_NHAN_TRA"
    # Saving the exact same content again must preserve the current version and signature.
    repeated = member.post(path + "/return", json={**payload, "version": record["version"]})
    assert repeated.status_code == 200 and repeated.json()["version"] == record["version"]
    assert confirm(env["login"]("ql.dn"), loan, record).status_code == 403
    assert confirm(manager, loan, record).status_code == 200
    finished = member.get(path).json()
    assert finished["status"] == "DA_HOAN_TRA" and finished["returned_at"]
    assert finished["asset"]["status"] == asset_status


def test_return_edit_signs_editor_and_invalidates_other_party(env):
    member, manager, loan = quick_delivery(env)
    path = f"/api/loans/{loan['id']}"
    record = member.post(path + "/return", json=return_payload()).json()
    edited = manager.post(
        path + "/reports",
        json={
            "kind": "TRA",
            "version": record["version"],
            "condition": "Hư hỏng",
            "content": "Có vết nứt mới, hai bên cần đối chiếu lại.",
            "confirm_self": True,
        },
    )
    assert edited.status_code == 200, edited.text
    updated = edited.json()
    assert updated["version"] == record["version"] + 1
    assert updated["receiver_confirmed_at"] and not updated["giver_confirmed_at"]
    assert member.get(path).json()["status"] == "CHO_XAC_NHAN_TRA"
    assert confirm(member, loan, record).status_code == 409
    assert confirm(member, loan, updated).status_code == 200
    assert member.get(path).json()["status"] == "DA_HOAN_TRA"


def test_unchanged_manager_review_does_not_erase_borrower_signature(env):
    member, manager, loan = quick_delivery(env)
    path = f"/api/loans/{loan['id']}"
    payload = return_payload()
    record = member.post(path + "/return", json=payload).json()
    saved = manager.post(
        path + "/reports",
        json={**payload, "kind": "TRA", "version": record["version"], "confirm_self": True},
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["status"] == "HOAN_TAT" and saved.json()["version"] == record["version"]
    assert member.get(path).json()["status"] == "DA_HOAN_TRA"


def test_invalid_return_is_atomic_and_scoped(env):
    member, manager, loan = quick_delivery(env)
    path = f"/api/loans/{loan['id']}"
    assert manager.post(path + "/return", json=return_payload()).status_code == 403
    assert (
        member.post(
            path + "/return", json=return_payload(receiver_id=env["users"]["ql.dn"])
        ).status_code
        == 409
    )
    assert (
        member.post(path + "/return", json=return_payload(evidence_path="missing.pdf")).status_code
        == 400
    )
    detail = member.get(path).json()
    assert detail["status"] == "DANG_MUON" and not any(
        r["kind"] == "TRA" for r in detail["reports"]
    )


def test_quick_delivery_still_checks_time_role_and_version(env):
    member, manager = env["login"]("an"), env["login"]("ql.hn")
    loan = create(member, request_data(env))
    approve(manager, loan)
    path = f"/api/loans/{loan['id']}/reports"
    data = dict(
        kind="GIAO",
        condition="Đạt",
        content="Hiện vật đủ phụ kiện, hoạt động tốt.",
        confirm_self=True,
    )
    assert manager.post(path, json=data).status_code == 409
    env["clock"][0] += timedelta(minutes=11)
    assert member.post(path, json=data).status_code == 403
    first = manager.post(path, json=data).json()
    repeated = manager.post(path, json={**data, "version": first["version"]})
    assert repeated.status_code == 200 and repeated.json()["version"] == first["version"]
    assert manager.post(path, json={**data, "version": 0}).status_code == 422
    assert confirm(member, loan, first).status_code == 200


def need_data(env, loan_data):
    member = env["login"]("an")
    asset = member.get(f"/api/assets/{loan_data['asset_id']}").json()
    return dict(
        category_id=asset["category_id"],
        purpose=loan_data["purpose"],
        start_at=loan_data["start_at"],
        end_at=loan_data["end_at"],
        alternative="HOAN_NHU_CAU",
    )


def test_booking_creates_need_atomically_and_retry_does_not_duplicate(env):
    member = env["login"]("an")
    payload = request_data(env)
    payload["new_need"] = need_data(env, payload)
    with env["sessions"]() as db:
        count = db.scalar(select(func.count()).select_from(Need))
    loan = create(member, payload)
    assert loan["need_id"]
    assert create(member, payload)["id"] == loan["id"]
    detail = member.get(f"/api/loans/{loan['id']}").json()
    assert detail["need"] is None
    with env["sessions"]() as db:
        assert db.scalar(select(func.count()).select_from(Need)) == count + 1
    payload["new_need"]["alternative"] = "MUA_MOI"
    assert member.post("/api/loans", json=payload).status_code == 409


def test_failed_combined_booking_rolls_back_need_and_loan(env):
    member = env["login"]("an")
    payload = request_data(env)
    payload["new_need"] = need_data(env, payload)
    # Need insert succeeds, then the loan-vs-need period check fails.
    payload["new_need"]["start_at"] = (env["clock"][0] + timedelta(minutes=20)).isoformat()
    with env["sessions"]() as db:
        counts = [db.scalar(select(func.count()).select_from(model)) for model in (Need, Loan)]
    assert member.post("/api/loans", json=payload).status_code == 400
    with env["sessions"]() as db:
        assert [
            db.scalar(select(func.count()).select_from(model)) for model in (Need, Loan)
        ] == counts


@pytest.mark.parametrize("alternative", ["MUA_MOI", "HOAN_NHU_CAU"])
def test_standalone_need_creation_is_disabled(env, alternative):
    member = env["login"]("an")
    payload = need_data(env, request_data(env))
    payload.update(alternative=alternative, auto_submit=True)
    response = member.post("/api/needs", json=payload)
    assert response.status_code == 405


def test_combined_booking_records_purchase_plan_without_evidence(env):
    member = env["login"]("an")
    payload = request_data(env)
    payload["new_need"] = {**need_data(env, payload), "alternative": "MUA_MOI"}
    with env["sessions"]() as db:
        count = db.scalar(select(func.count()).select_from(Need))
    response = member.post("/api/loans", json=payload)
    assert response.status_code == 201, response.text
    loan = response.json()
    detail = member.get(f"/api/loans/{loan['id']}").json()
    assert detail["need"] is None
    with env["sessions"]() as db:
        need = db.get(Need, loan["need_id"])
        assert need.alternative == "MUA_MOI" and need.evidence_path is None
    assert create(member, payload)["id"] == loan["id"]
    with env["sessions"]() as db:
        assert db.scalar(select(func.count()).select_from(Need)) == count + 1
