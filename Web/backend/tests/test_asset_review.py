from datetime import timedelta

from backend.app.models import Asset, Handover, Loan
from backend.tests.test_workflows import confirm, create, delivered, report, request_data


def new_asset(member):
    lookups = member.get("/api/lookups").json()
    user = member.get("/api/auth/me").json()["user"]
    data = dict(
        name="Tài sản đăng ký để kiểm tra",
        category_id=lookups["categories"][0]["id"],
        location_id=next(x["id"] for x in lookups["locations"] if x["unit_id"] == user["unit_id"]),
        condition="Tốt, đầy đủ phụ kiện.",
    )
    response = member.post("/api/assets", json=data)
    assert response.status_code == 201, response.text
    return response.json(), data


def test_pending_rejection_resubmission_and_no_review_bypass(env):
    member, manager, outsider = env["login"]("an"), env["login"]("ql.hcm"), env["login"]("chi")
    asset, data = new_asset(member)
    path = f"/api/assets/{asset['id']}"
    assert asset["status"] == "CHO_DUYET"
    assert outsider.get(path).status_code == 404
    assert (
        member.post(
            path + "/review", json={"approve": True, "version": asset["version"]}
        ).status_code
        == 403
    )
    assert (
        manager.post(
            path + "/state",
            json={
                "status": "CHO_CHIA_SE",
                "reason": "Thử bỏ qua xét duyệt.",
                "version": asset["version"],
            },
        ).status_code
        == 404
    )
    assert (
        manager.post(
            path + "/events",
            json={
                "kind": "DANH_GIA",
                "content": "Thử mở chia sẻ qua đánh giá.",
                "basis": "Căn cứ kiểm tra.",
                "decision": "TIEP_TUC",
                "condition": "Tốt",
            },
        ).status_code
        == 409
    )
    assert (
        manager.post(
            path + "/review", json={"approve": False, "version": asset["version"]}
        ).status_code
        == 400
    )
    rejected = manager.post(
        path + "/review",
        json={
            "approve": False,
            "reason": "Cần bổ sung mô tả phụ kiện.",
            "version": asset["version"],
        },
    )
    assert rejected.status_code == 200 and rejected.json()["status"] == "TU_CHOI"
    assert outsider.get(path).status_code == 404
    data.update(description="Đã bổ sung đầy đủ phụ kiện.", version=rejected.json()["version"])
    submitted = member.put(path, json=data)
    assert submitted.status_code == 200 and submitted.json()["status"] == "CHO_DUYET"
    approved = manager.post(
        path + "/review", json={"approve": True, "version": submitted.json()["version"]}
    )
    assert approved.status_code == 200 and approved.json()["status"] == "CHO_CHIA_SE"
    assert outsider.get(path).status_code == 200


def test_custodian_can_withdraw_pending_and_not_restore_it(env):
    member, outsider = env["login"]("an"), env["login"]("ql.dn")
    asset, data = new_asset(member)
    path = f"/api/assets/{asset['id']}"
    assert outsider.post(path + "/withdraw", json={"version": asset["version"]}).status_code == 403
    assert member.post(path + "/withdraw", json={"version": asset["version"]}).status_code == 200
    assert member.get(path).status_code == 404
    assert member.get(path + "/events").status_code == 404
    assert asset["id"] not in [
        a["id"] for a in member.get("/api/assets?scope=own&page_size=100").json()["items"]
    ]
    data["version"] = asset["version"]
    assert member.put(path, json=data).status_code == 404


def test_only_custodian_can_edit_or_withdraw_even_for_same_unit_manager(env):
    owner, manager = env["login"]("an"), env["login"]("ql.hcm")
    asset, data = new_asset(owner)
    path = f"/api/assets/{asset['id']}"
    payload = {**data, "version": asset["version"]}
    for username in ("ql.hcm", "ql.hn", "chi", "admin"):
        other = env["login"](username)
        assert other.put(path, json=payload).status_code == 403
        assert other.post(path + "/withdraw", json={"version": asset["version"]}).status_code == 403
    # Sending the manager's own ID cannot claim ownership of someone else's record.
    assert (
        manager.put(path, json={**payload, "custodian_id": env["users"]["ql.hcm"]}).status_code
        == 403
    )
    assert owner.get(path).json()["custodian_id"] == env["users"]["an"]
    approved = manager.post(path + "/review", json={"approve": True, "version": asset["version"]})
    assert approved.status_code == 200
    payload.update(
        version=approved.json()["version"], description="Bổ sung mô tả sau khi tài sản được duyệt."
    )
    updated = owner.put(path, json=payload)
    assert updated.status_code == 200 and updated.json()["status"] == "CHO_CHIA_SE"
    assert (
        manager.put(path, json={**payload, "version": updated.json()["version"]}).status_code == 403
    )
    assert (
        manager.post(path + "/withdraw", json={"version": updated.json()["version"]}).status_code
        == 403
    )
    assert (
        owner.post(path + "/withdraw", json={"version": updated.json()["version"]}).status_code
        == 200
    )


def test_manager_keeps_edit_and_withdraw_only_when_they_are_custodian(env):
    manager = env["login"]("ql.hn")
    asset, data = new_asset(manager)
    path = f"/api/assets/{asset['id']}"
    updated = manager.put(
        path,
        json={
            **data,
            "version": asset["version"],
            "description": "Hồ sơ do chính quản lý phụ trách.",
        },
    )
    assert updated.status_code == 200
    assert (
        manager.post(path + "/withdraw", json={"version": updated.json()["version"]}).status_code
        == 200
    )


def test_withdraw_cancels_approved_loan_and_unsigned_report(env):
    member, manager = env["login"]("an"), env["login"]("ql.hn")
    loan = create(member, request_data(env))
    assert (
        manager.post(f"/api/loans/{loan['id']}/decision", json={"approve": True}).status_code == 200
    )
    env["clock"][0] += timedelta(minutes=11)
    record = report(manager, loan)
    assert confirm(manager, loan, record).status_code == 200
    path = f"/api/assets/{loan['asset_id']}"
    asset = manager.get(path).json()
    assert manager.post(path + "/withdraw", json={"version": asset["version"]}).status_code == 200
    assert member.get(path).status_code == 404 and manager.get(path).status_code == 404
    assert loan["asset_id"] not in [
        a["id"] for a in member.get("/api/assets?page_size=100").json()["items"]
    ]
    assert member.get(f"/api/loans/{loan['id']}").status_code == 404
    with env["sessions"]() as db:
        assert db.get(Loan, loan["id"]) is None
        assert db.get(Handover, record["id"]) is None
    assert member.post("/api/loans", json=request_data(env)).status_code == 404
    assert confirm(member, loan, record).status_code == 404


def test_withdraw_waits_while_someone_is_holding(env):
    member, manager, loan = delivered(env)
    path = f"/api/assets/{loan['asset_id']}"
    asset = manager.get(path).json()
    response = manager.post(path + "/withdraw", json={"version": asset["version"]})
    assert response.status_code == 200 and response.json()["pending"] is True
    assert manager.get(path).status_code == 200
    assert manager.get(path).json()["status"] == "CHO_THU_HOI"
    with env["sessions"]() as db:
        assert not db.get(Asset, loan["asset_id"]).withdrawn


def test_withdraw_keeps_closed_vouchers_and_indicator(env):
    manager = env["login"]("ql.hcm")
    asset_id = env["assets"]["Laptop HP ProBook 450"]
    path = f"/api/assets/{asset_id}"
    asset = manager.get(path).json()
    assert manager.post(path + "/withdraw", json={"version": asset["version"]}).status_code == 200
    reviewer = env["login"]("ql.hn")
    need = reviewer.get("/api/needs?scope=manage").json()["items"][-1]
    linked = reviewer.get(f"/api/needs/{need['id']}").json()["loans"]
    assert linked and reviewer.get(f"/api/loans/{linked[0]['id']}").json()["status"] == "DA_DONG"
    now = env["clock"][0]
    result = reviewer.get(
        "/api/reports/avoidance",
        params={"start": (now - timedelta(days=40)).isoformat(), "end": now.isoformat()},
    ).json()
    assert (result["total"], result["avoided"]) == (4, 2)
