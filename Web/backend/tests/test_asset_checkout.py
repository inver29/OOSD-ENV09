from base64 import b64decode
from datetime import timedelta

from sqlalchemy import select

from backend.app.models import Loan
from backend.app.services.loans import expire_due
from backend.tests.test_asset_review import new_asset
from backend.tests.test_workflows import approve, confirm, create, report, request_data


def test_corrupt_png_is_rejected_and_same_origin_document_preview_is_allowed(env):
    member = env["login"]("an")
    bad = b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a9qkAAAAASUVORK5CYII="
    )
    assert (
        member.post("/api/files", files={"file": ("broken.png", bad, "image/png")}).status_code
        == 400
    )
    uploaded = member.post(
        "/api/files", files={"file": ("proof.pdf", b"%PDF-1.4\nExample proof", "application/pdf")}
    )
    assert uploaded.status_code == 201
    document = member.get(uploaded.json()["url"])
    assert document.status_code == 200 and document.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert member.get("/api/dashboard").headers["X-Frame-Options"] == "DENY"


def shared_ids(client):
    return {a["id"] for a in client.get("/api/assets?page_size=100").json()["items"]}


def test_creator_is_fixed_custodian_and_manager_creation_auto_approves(env):
    manager, member = env["login"]("ql.hcm"), env["login"]("an")
    asset, payload = new_asset(manager)
    assert asset["custodian_id"] == env["users"]["ql.hcm"]
    assert asset["status"] == "CHO_CHIA_SE"
    assert asset["id"] in shared_ids(env["login"]("chi"))
    assert (
        manager.post(
            "/api/assets", json={**payload, "custodian_id": env["users"]["an"]}
        ).status_code
        == 403
    )
    assert (
        manager.put(
            f"/api/assets/{asset['id']}",
            json={**payload, "version": asset["version"], "custodian_id": env["users"]["an"]},
        ).status_code
        == 403
    )
    assert (
        manager.get(f"/api/assets/{asset['id']}").json()["custodian_id"] == env["users"]["ql.hcm"]
    )
    own, data = new_asset(member)
    assert own["status"] == "CHO_DUYET" and own["custodian_id"] == env["users"]["an"]
    assert (
        member.post(
            "/api/assets", json={**data, "custodian_id": env["users"]["ql.hcm"]}
        ).status_code
        == 403
    )


def test_approval_rejects_every_other_pending_request_with_exact_reason(env):
    member, other, manager = env["login"]("an"), env["login"]("binh"), env["login"]("ql.hn")
    first = create(member, request_data(env))
    later = request_data(env)
    later["start_at"] = (env["clock"][0] + timedelta(days=3)).isoformat()
    later["end_at"] = (env["clock"][0] + timedelta(days=4)).isoformat()
    second = create(other, later)
    different = create(member, request_data(env, env["assets"]["Máy ảnh Sony ZV-E10"]))
    approve(manager, first)
    rejected = other.get(f"/api/loans/{second['id']}").json()
    assert (
        rejected["status"] == "TU_CHOI"
        and rejected["reason"] == "Đã có người khác mượn tài sản này"
    )
    assert rejected["decided_at"] and rejected["approver_name"]
    assert member.get(f"/api/loans/{different['id']}").json()["status"] == "CHO_DUYET"
    assert (
        member.post(
            f"/api/loans/{first['id']}/cancel", json={"reason": "Không còn nhu cầu dùng."}
        ).status_code
        == 200
    )
    assert other.get(f"/api/loans/{second['id']}").json()["status"] == "TU_CHOI"


def test_asset_phase_tracks_signatures_and_blocks_old_booking_links(env):
    member, other, manager = env["login"]("an"), env["login"]("binh"), env["login"]("ql.hn")
    loan = create(member, request_data(env))
    asset_path = f"/api/assets/{loan['asset_id']}"
    assert loan["asset_id"] in shared_ids(member)
    approve(manager, loan)
    assert loan["asset_id"] not in shared_ids(member)
    assert member.get(asset_path).json()["status"] == "CHO_BAN_GIAO"
    own = manager.get("/api/assets?scope=own&status=CHO_BAN_GIAO&page_size=100").json()["items"]
    assert loan["asset_id"] in {a["id"] for a in own}
    assert other.post("/api/loans", json=request_data(env)).status_code == 409
    env["clock"][0] += timedelta(minutes=11)
    record = report(manager, loan)
    assert confirm(manager, loan, record).status_code == 200
    assert member.get(asset_path).json()["status"] == "CHO_BAN_GIAO"
    assert confirm(member, loan, record).status_code == 200
    assert member.get(asset_path).json()["status"] == "DA_DUOC_MUON"
    assert loan["asset_id"] not in shared_ids(member)
    own = manager.get("/api/assets?scope=own&status=DA_DUOC_MUON&page_size=100").json()["items"]
    assert loan["asset_id"] in {a["id"] for a in own}
    assert (
        member.post(
            f"/api/loans/{loan['id']}/return",
            json={
                "condition": "Đạt",
                "content": "Trả đủ hiện vật và phụ kiện, kiểm tra hoạt động tốt.",
            },
        ).status_code
        == 200
    )
    detail = member.get(f"/api/loans/{loan['id']}").json()
    returned = next(r for r in detail["reports"] if r["kind"] == "TRA")
    assert detail["asset"]["status"] == "DA_DUOC_MUON"
    assert confirm(manager, loan, returned).status_code == 200
    assert member.get(asset_path).json()["status"] == "CHO_CHIA_SE"
    assert loan["asset_id"] in shared_ids(member)


def test_expiry_reopens_item_and_failed_approval_does_not_refuse_others(env):
    member, other = env["login"]("an"), env["login"]("binh")
    first = create(member, request_data(env))
    second = create(other, request_data(env))
    path = f"/api/loans/{first['id']}"
    assert env["login"]("ql.dn").post(path + "/decision", json={"approve": True}).status_code == 403
    assert other.get(f"/api/loans/{second['id']}").json()["status"] == "CHO_DUYET"
    approve(env["login"]("ql.hn"), first)
    env["clock"][0] += timedelta(hours=3)
    expire_due(env["sessions"])
    assert member.get(path).json()["status"] == "HET_HAN_NHAN"
    assert member.get(f"/api/assets/{first['asset_id']}").json()["status"] == "CHO_CHIA_SE"
    assert first["asset_id"] in shared_ids(member)
    with env["sessions"]() as db:
        rejected = db.scalar(select(Loan).where(Loan.id == second["id"]))
        assert rejected.status == "TU_CHOI"


def test_expiry_transition_keeps_asset_and_loan_status_consistent(env):
    member, manager = env["login"]("an"), env["login"]("ql.hn")
    loan = create(member, request_data(env))
    approve(manager, loan)
    env["clock"][0] += timedelta(hours=3)
    # The worker has not marked the voucher expired yet: both surfaces still show waiting.
    path = f"/api/loans/{loan['id']}"
    before = member.get(path).json()
    assert before["status"] == "DA_DUYET" and before["asset"]["status"] == "CHO_BAN_GIAO"
    assert loan["asset_id"] not in shared_ids(member)
    assert member.post("/api/loans", json=request_data(env)).status_code == 409
    record = manager.post(
        path + "/reports",
        json={
            "kind": "GIAO",
            "content": "Đối chiếu hiện vật khi hết hạn nhận.",
            "condition": "Đạt",
            "confirm_self": True,
        },
    )
    assert record.status_code == 409
    expire_due(env["sessions"])
    after = member.get(path).json()
    assert after["status"] == "HET_HAN_NHAN" and after["asset"]["status"] == "CHO_CHIA_SE"
    assert loan["asset_id"] in shared_ids(member)
