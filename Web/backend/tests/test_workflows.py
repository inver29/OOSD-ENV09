from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from uuid import uuid4

from sqlalchemy import func, select

from backend.app.models import Asset, Handover, LifecycleEvent, Loan, Need
from backend.app.services.loans import expire_due


def request_data(env, asset=None, **extra):
    start = env["clock"][0] + timedelta(minutes=10)
    return dict(
        asset_id=asset or env["assets"]["Máy chiếu Epson EB-X49"],
        start_at=start.isoformat(),
        end_at=(start + timedelta(hours=2)).isoformat(),
        purpose="Sử dụng cho buổi đào tạo thử nghiệm.",
        request_id=str(uuid4()),
        **extra,
    )


def create(client, data):
    response = client.post("/api/loans", json=data)
    assert response.status_code == 201, response.text
    return response.json()


def approve(manager, loan):
    response = manager.post(f"/api/loans/{loan['id']}/decision", json={"approve": True})
    assert response.status_code == 200, response.text


def report(manager, loan, kind="GIAO", condition="Đạt", version=None):
    response = manager.post(
        f"/api/loans/{loan['id']}/reports",
        json={
            "kind": kind,
            "condition": condition,
            "content": "Đã kiểm tra hiện vật và các phụ kiện.",
            "version": version,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def confirm(client, loan, record, version=None):
    return client.post(
        f"/api/loans/{loan['id']}/reports/{record['id']}/confirm",
        json={"version": version or record["version"]},
    )


def delivered(env):
    member, manager = env["login"]("an"), env["login"]("ql.hn")
    loan = create(member, request_data(env))
    approve(manager, loan)
    env["clock"][0] += timedelta(minutes=11)
    record = report(manager, loan)
    assert confirm(manager, loan, record).status_code == 200
    assert confirm(member, loan, record).status_code == 200
    return member, manager, loan


def test_auth_csrf_and_logout(env):
    member = env["login"]("an")
    headers = dict(member.headers)
    member.headers.pop("X-CSRF-Token")
    assert member.post("/api/loans", json=request_data(env)).status_code == 403
    member.headers.update(headers)
    assert member.get("/api/admin/users").status_code == 403
    admin = env["login"]("admin")
    asset_id = env["assets"]["Máy chiếu Epson EB-X49"]
    assert admin.get(f"/api/assets/{asset_id}/events").status_code == 403
    assert admin.post("/api/files", files={"file": ("proof.pdf", b"%PDF-1.4", "application/pdf")}).status_code == 403
    assert member.post("/api/auth/logout").status_code == 200
    assert member.get("/api/auth/me").status_code == 401


def test_admin_has_no_dashboard_and_unit_address_round_trip(env):
    admin = env["login"]("admin")
    assert admin.get("/api/dashboard").status_code == 403
    bad = admin.post("/api/admin/catalog/units", json={"name": "Đơn vị kiểm thử"})
    assert bad.status_code == 400
    payload = {
        "name": "Đơn vị kiểm thử",
        "address": "25 đường Số 4, Thành phố kiểm thử",
        "active": True,
    }
    created = admin.post("/api/admin/catalog/units", json=payload)
    assert created.status_code == 201 and created.json()["address"] == payload["address"]
    payload["address"] = "36 đường Số 8, Thành phố kiểm thử"
    updated = admin.put(f"/api/admin/catalog/units/{created.json()['id']}", json=payload)
    assert updated.status_code == 200 and updated.json()["address"] == payload["address"]
    member = env["login"]("an")
    asset = member.get(f"/api/assets/{env['assets']['Máy chiếu Epson EB-X49']}").json()
    assert asset["unit_address"] == "120 Trần Duy Hưng, Hà Nội"


def test_origin_and_password_validation(env):
    client = env["login"]("an")
    assert (
        client.post(
            "/api/loans",
            json=request_data(env),
            headers={"Origin": "https://foreign.example"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/auth/password",
            json={"current_password": "wrong", "new_password": "NewPassword123!"},
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/auth/password",
            json={
                "current_password": env["config"].demo_password,
                "new_password": "NewPassword123!",
            },
        ).status_code
        == 200
    )
    assert client.get("/api/auth/me").status_code == 401


def test_cross_unit_and_permissions(env):
    member, other, manager = (
        env["login"]("an"),
        env["login"]("binh"),
        env["login"]("ql.dn"),
    )
    own = env["assets"]["Máy chiếu BenQ MW550"]
    assert member.post("/api/loans", json=request_data(env, own)).status_code == 400
    loan = create(member, request_data(env))
    assert other.get(f"/api/loans/{loan['id']}").status_code == 404
    assert (
        manager.post(f"/api/loans/{loan['id']}/decision", json={"approve": True}).status_code == 403
    )
    assert (
        member.post(f"/api/loans/{loan['id']}/decision", json={"approve": True}).status_code == 403
    )
    borrowing_manager = env["login"]("ql.hcm")
    lending_manager = env["login"]("ql.hn")
    manager_loan = create(borrowing_manager, request_data(env))
    decision = f"/api/loans/{manager_loan['id']}/decision"
    assert borrowing_manager.post(decision, json={"approve": True}).status_code == 403
    assert manager.post(decision, json={"approve": True}).status_code == 403
    approve(lending_manager, manager_loan)


def test_idempotent_request_and_pending_does_not_reserve(env):
    member = env["login"]("an")
    data = request_data(env)
    first, repeated = create(member, data), create(member, data)
    assert first["id"] == repeated["id"]
    second = create(env["login"]("binh"), request_data(env))
    assert second["id"] != first["id"]
    data["purpose"] = "Thay đổi nội dung với cùng mã yêu cầu"
    assert member.post("/api/loans", json=data).status_code == 409


def test_two_concurrent_approvals_only_one_reservation(env):
    first = create(env["login"]("an"), request_data(env))
    second = create(env["login"]("binh"), request_data(env))
    managers = [env["login"]("ql.hn"), env["login"]("ql.hn")]
    barrier = Barrier(2)

    def decide(index):
        barrier.wait(timeout=10)
        return (
            managers[index]
            .post(
                f"/api/loans/{[first, second][index]['id']}/decision",
                json={"approve": True},
            )
            .status_code
        )

    with ThreadPoolExecutor(2) as executor:
        results = list(executor.map(decide, (0, 1)))
    assert sorted(results) == [200, 409]
    statuses = [
        env["login"](username).get(f"/api/loans/{loan['id']}").json()
        for username, loan in (("an", first), ("binh", second))
    ]
    assert sorted(row["status"] for row in statuses) == ["DA_DUYET", "TU_CHOI"]
    assert (
        next(row for row in statuses if row["status"] == "TU_CHOI")["reason"]
        == "Đã có người khác mượn tài sản này"
    )
    with env["sessions"]() as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(Loan)
                .where(Loan.id.in_([first["id"], second["id"]]), Loan.status == "DA_DUYET")
            )
            == 1
        )


def test_refusal_requires_reason_and_cancel_releases_schedule(env):
    member, manager = env["login"]("an"), env["login"]("ql.hn")
    loan = create(member, request_data(env))
    assert (
        manager.post(f"/api/loans/{loan['id']}/decision", json={"approve": False}).status_code
        == 400
    )
    approve(manager, loan)
    assert (
        member.post(
            f"/api/loans/{loan['id']}/cancel",
            json={"reason": "Không còn nhu cầu sử dụng."},
        ).status_code
        == 200
    )
    second = create(member, request_data(env))
    approve(manager, second)


def test_pickup_expiry_clears_only_undelivered(env):
    member, manager = env["login"]("an"), env["login"]("ql.hn")
    loan = create(member, request_data(env))
    approve(manager, loan)
    env["clock"][0] += timedelta(hours=3)
    expire_due(env["sessions"])
    assert member.get(f"/api/loans/{loan['id']}").json()["status"] == "HET_HAN_NHAN"
    with env["sessions"]() as db:
        holding = db.scalar(select(Loan).where(Loan.status == "CHO_XAC_NHAN_TRA"))
        assert holding.status == "CHO_XAC_NHAN_TRA"


def test_cannot_deliver_early_and_stale_record_confirmation(env):
    member, manager = env["login"]("an"), env["login"]("ql.hn")
    loan = create(member, request_data(env))
    approve(manager, loan)
    assert (
        manager.post(
            f"/api/loans/{loan['id']}/reports",
            json={
                "kind": "GIAO",
                "condition": "Đạt",
                "content": "Đủ phụ kiện theo phiếu.",
            },
        ).status_code
        == 409
    )
    env["clock"][0] += timedelta(minutes=11)
    first = report(manager, loan)
    assert confirm(manager, loan, first).status_code == 200
    edited = report(manager, loan, version=first["version"])
    assert edited["version"] == first["version"] + 1
    assert edited["giver_confirmed_at"] is None and edited["receiver_confirmed_at"] is None
    assert confirm(member, loan, first).status_code == 409
    assert confirm(member, loan, edited).status_code == 200
    assert member.get(f"/api/loans/{loan['id']}").json()["status"] == "DA_DUYET"
    assert confirm(manager, loan, edited).status_code == 200
    assert member.get(f"/api/loans/{loan['id']}").json()["status"] == "DANG_MUON"


def test_damaged_return_closes_and_pauses_atomically(env):
    member, manager, loan = delivered(env)
    assert member.post(f"/api/loans/{loan['id']}/return").status_code == 200
    record = report(manager, loan, "TRA", "Hư hỏng")
    assert confirm(member, loan, record).status_code == 200
    assert member.get(f"/api/loans/{loan['id']}").json()["status"] == "CHO_XAC_NHAN_TRA"
    assert confirm(manager, loan, record).status_code == 200
    with env["sessions"]() as db:
        assert db.get(Loan, loan["id"]).status == "DA_DONG"
        assert db.get(Asset, loan["asset_id"]).status == "BAO_TRI"
        assert db.scalar(
            select(LifecycleEvent.id).where(
                LifecycleEvent.asset_id == loan["asset_id"],
                LifecycleEvent.kind == "SU_CO",
            )
        )
    assert (
        manager.post(
            f"/api/loans/{loan['id']}/reports",
            json={
                "kind": "TRA",
                "condition": "Đạt",
                "content": "Cố sửa biên bản đã hoàn tất",
                "version": 1,
            },
        ).status_code
        == 409
    )
    assert (
        member.post(
            f"/api/loans/{loan['id']}/cancel",
            json={"reason": "Cố hủy sau khi bàn giao"},
        ).status_code
        == 409
    )


def test_late_return_blocks_new_approval(env):
    member, manager, loan = delivered(env)
    env["clock"][0] += timedelta(hours=3)
    assert member.get(f"/api/loans/{loan['id']}").json()["overdue"] is True
    data = request_data(env)
    assert member.post("/api/loans", json=data).status_code == 409
    assert member.get(f"/api/loans/{loan['id']}").json()["status"] == "DANG_MUON"


def test_normal_return_retains_buffer_then_accepts(env):
    member, manager, loan = delivered(env)
    member.post(f"/api/loans/{loan['id']}/return")
    record = report(manager, loan, "TRA")
    confirm(member, loan, record)
    confirm(manager, loan, record)
    assert member.post("/api/loans", json=request_data(env)).status_code == 409
    env["clock"][0] += timedelta(hours=2)
    assert member.post("/api/loans", json=request_data(env)).status_code == 201


def test_asset_version_and_scope(env):
    manager, outsider = env["login"]("ql.hn"), env["login"]("an")
    asset_id = env["assets"]["Webcam Logitech C920"]
    a = manager.get(f"/api/assets/{asset_id}").json()
    assert outsider.get(f"/api/assets/{asset_id}").status_code == 404
    data = dict(
        name=a["name"],
        category_id=a["category_id"],
        location_id=a["location_id"],
        custodian_id=a["custodian_id"],
        condition="Đã kiểm tra hoạt động ổn định",
        version=a["version"],
    )
    assert manager.put(f"/api/assets/{asset_id}", json=data).status_code == 200
    assert manager.put(f"/api/assets/{asset_id}", json=data).status_code == 409


def test_lifecycle_requires_receipt_and_evaluation(env):
    member, manager, loan = delivered(env)
    response = member.post(
        f"/api/assets/{loan['asset_id']}/events",
        json={"kind": "SU_CO", "content": "Thiết bị mất tín hiệu khi hoạt động."},
    )
    assert response.status_code == 201
    decision = dict(
        kind="DANH_GIA",
        content="Đã kiểm tra lại hiện vật",
        basis="Biên bản kiểm tra của bộ phận kỹ thuật",
        decision="TIEP_TUC",
        condition="Đã khắc phục, hoạt động tốt",
    )
    assert manager.post(f"/api/assets/{loan['asset_id']}/events", json=decision).status_code == 409


def test_indicator_distinct_and_zero_denominator(env):
    manager = env["login"]("ql.hn")
    now = env["clock"][0]
    params = {"start": (now - timedelta(days=40)).isoformat(), "end": now.isoformat()}
    result = manager.get("/api/reports/avoidance", params=params).json()
    assert (result["total"], result["avoided"], result["rate"]) == (4, 2, 50.0)
    empty = manager.get(
        "/api/reports/avoidance",
        params={
            "start": (now + timedelta(days=50)).isoformat(),
            "end": (now + timedelta(days=60)).isoformat(),
        },
    ).json()
    assert empty["total"] == 0 and empty["rate"] is None


def test_outcome_correction_requires_reverification(env):
    creator, manager = env["login"]("chi"), env["login"]("ql.hn")
    need = creator.get("/api/needs").json()["items"][-1]
    response = creator.post(f"/api/needs/{need['id']}/outcome", json={"purchased": True})
    assert response.status_code == 200 and response.json()["status"] == "CHO_XAC_MINH"
    payload = dict(
        accepted=True,
        intended_purchase=True,
        purpose_met=True,
        conclusion="Đã đối chiếu lại với kết quả mua mới cập nhật.",
    )
    assert manager.post(f"/api/needs/{need['id']}/verify", json=payload).status_code == 200
    with env["sessions"]() as db:
        assert db.get(Need, need["id"]).purchased is True


def test_need_cannot_be_added_manually_and_no_self_verification(env):
    from backend.tests.test_withdrawal_flow import completed_booking

    member, _, loan = completed_booking(env, username="ql.hcm")
    own = loan["need_id"]
    verify = dict(
        accepted=True,
        intended_purchase=True,
        purpose_met=True,
        conclusion="Nội dung kết luận thử tự xác minh",
    )
    assert member.post(f"/api/needs/{own}/verify", json=verify).status_code == 403
    assert member.post("/api/needs", json={}).status_code == 405


def test_attachment_permissions_and_type(env):
    member, stranger = env["login"]("an"), env["login"]("binh")
    assert (
        member.post(
            "/api/files", files={"file": ("bad.png", b"fake image", "image/png")}
        ).status_code
        == 400
    )
    response = member.post(
        "/api/files",
        files={"file": ("proof.pdf", b"%PDF-1.4\nExample test proof", "application/pdf")},
    )
    assert response.status_code == 201
    name = response.json()["filename"]
    assert member.get(f"/api/files/{name}").status_code == 200
    assert stranger.get(f"/api/files/{name}").status_code == 403
    assert member.get("/api/files/..%2F.env").status_code in {404, 400}


def test_admin_cannot_remove_own_privilege_or_referenced_catalog(env):
    admin = env["login"]("admin")
    user = next(u for u in admin.get("/api/admin/users").json() if u["username"] == "admin")
    payload = {k: user[k] for k in ("username", "name", "email", "unit_id", "active")}
    payload["roles"] = ["THANH_VIEN"]
    assert admin.put(f"/api/admin/users/{user['id']}", json=payload).status_code == 400
    lookups = admin.get("/api/lookups").json()
    assert admin.delete(f"/api/admin/catalog/units/{user['unit_id']}").status_code == 409
    location = lookups["locations"][0]
    assert (
        admin.post(
            "/api/admin/catalog/locations",
            json={"name": "Phòng họp mới", "unit_id": location["unit_id"]},
        ).status_code
        == 201
    )
    new_user = dict(
        username="single.role",
        name="Tài khoản kiểm tra vai trò",
        email="single.role@env09.example",
        unit_id=user["unit_id"],
        password="SingleRole!2026",
        roles=["THANH_VIEN", "QUAN_LY"],
    )
    assert admin.post("/api/admin/users", json=new_user).status_code == 422
    new_user["roles"] = []
    assert admin.post("/api/admin/users", json=new_user).status_code == 422
    new_user["roles"] = ["THANH_VIEN"]
    created = admin.post("/api/admin/users", json=new_user)
    assert created.status_code == 201, created.text
    new_user["roles"] = ["QUAN_LY"]
    changed = admin.put(f"/api/admin/users/{created.json()['id']}", json=new_user)
    assert changed.status_code == 200, changed.text
    assert changed.json()["roles"] == ["QUAN_LY"]


def test_member_submission_manager_approval_and_type_history(env):
    member, manager = env["login"]("an"), env["login"]("ql.hcm")
    lookups = member.get("/api/lookups").json()
    unit = member.get("/api/auth/me").json()["user"]["unit_id"]
    data = dict(
        name="Thiết bị mới từ thành viên",
        category_id=lookups["categories"][0]["id"],
        location_id=next(x["id"] for x in lookups["locations"] if x["unit_id"] == unit),
        condition="Hoạt động tốt, đủ phụ kiện",
    )
    response = member.post("/api/assets", json=data)
    assert response.status_code == 201, response.text
    asset = response.json()
    assert asset["status"] == "CHO_DUYET"
    review = dict(approve=True, version=asset["version"])
    assert member.post(f"/api/assets/{asset['id']}/review", json=review).status_code == 403
    assert manager.post(f"/api/assets/{asset['id']}/review", json=review).status_code == 200
    historical = member.get(f"/api/assets/{env['assets']['Laptop HP ProBook 450']}").json()
    data.update(
        name=historical["name"],
        version=historical["version"],
        category_id=next(
            c["id"] for c in lookups["categories"] if c["id"] != historical["category_id"]
        ),
    )
    assert manager.put(f"/api/assets/{historical['id']}", json=data).status_code == 409


def test_approved_item_is_hidden_for_every_period_until_cancelled(env):
    member, manager = env["login"]("an"), env["login"]("ql.hn")
    data = request_data(env)
    loan = create(member, data)
    params = dict(start=data["start_at"], end=data["end_at"], page_size=100)
    assert loan["asset_id"] in [
        a["id"] for a in member.get("/api/assets", params=params).json()["items"]
    ]
    approve(manager, loan)
    assert loan["asset_id"] not in [
        a["id"] for a in member.get("/api/assets", params=params).json()["items"]
    ]
    start = env["clock"][0] + timedelta(minutes=10, hours=4)
    params.update(start=start.isoformat(), end=(start + timedelta(hours=1)).isoformat())
    response = member.get("/api/assets", params=params)
    assert response.status_code == 200, response.text
    assert loan["asset_id"] not in [a["id"] for a in response.json()["items"]]
    assert (
        member.post(
            f"/api/loans/{loan['id']}/cancel", json={"reason": "Đổi lịch sử dụng tài sản."}
        ).status_code
        == 200
    )
    assert loan["asset_id"] in [
        a["id"] for a in member.get("/api/assets", params=params).json()["items"]
    ]


def test_linked_need_keeps_original_counterfactual(env):
    member = env["login"]("an")
    asset = member.get(f"/api/assets/{env['assets']['Máy chiếu Epson EB-X49']}").json()
    start = env["clock"][0] + timedelta(minutes=5)
    payload = dict(
        category_id=asset["category_id"],
        purpose="Nhu cầu máy chiếu cho lớp đào tạo",
        start_at=start.isoformat(),
        end_at=(start + timedelta(hours=3)).isoformat(),
        alternative="HOAN_NHU_CAU",
    )
    booking = request_data(env)
    booking["new_need"] = payload
    loan = create(member, booking)
    need = {"id": loan["need_id"]}
    assert need["id"] is not None
    verifier = env["login"]("ql.hcm")
    assert verifier.get(f"/api/loans/{loan['id']}").status_code == 200
    assert (
        verifier.post(f"/api/loans/{loan['id']}/decision", json={"approve": True}).status_code
        == 403
    )
    payload["alternative"] = "MUA_MOI"
    assert member.put(f"/api/needs/{need['id']}", json=payload).status_code == 405


def test_evaluation_resolves_affected_pending_vouchers(env):
    manager = env["login"]("ql.hn")
    asset_id = env["assets"]["Máy chiếu Epson EB-X49"]
    assert (
        manager.post(
            f"/api/assets/{asset_id}/events",
            json={"kind": "SU_CO", "content": "Cần kiểm tra kỹ thuật trước khi cho mượn."},
        ).status_code
        == 201
    )
    assert (
        manager.post(
            f"/api/assets/{asset_id}/state",
            json=dict(
                status="CHO_CHIA_SE", reason="Cố mở lại không đánh giá", version="0000000000000000"
            ),
        ).status_code
        == 404
    )
    decision = dict(
        kind="DANH_GIA",
        content="Đã kiểm tra và xử lý nguồn phát.",
        basis="Biên bản kiểm tra kỹ thuật.",
        decision="TIEP_TUC",
        condition="Hoạt động ổn định, đầy đủ phụ kiện.",
    )
    assert manager.post(f"/api/assets/{asset_id}/events", json=decision).status_code == 409
    decision["cancel_pending"] = True
    response = manager.post(f"/api/assets/{asset_id}/events", json=decision)
    assert response.status_code == 201 and response.json()["status"] == "CHO_CHIA_SE"
    with env["sessions"]() as db:
        assert not db.scalar(
            select(Loan.id).where(
                Loan.asset_id == asset_id, Loan.status.in_({"CHO_DUYET", "DA_DUYET"})
            )
        )


def test_concurrent_two_party_confirmation_completes_once(env):
    member, manager = env["login"]("an"), env["login"]("ql.hn")
    loan = create(member, request_data(env))
    approve(manager, loan)
    env["clock"][0] += timedelta(minutes=11)
    record = report(manager, loan)
    barrier = Barrier(2)

    def perform(client):
        barrier.wait(timeout=10)
        return confirm(client, loan, record).status_code

    with ThreadPoolExecutor(2) as executor:
        assert list(executor.map(perform, [member, manager])) == [200, 200]
    with env["sessions"]() as db:
        assert db.get(Loan, loan["id"]).status == "DANG_MUON"
        assert (
            db.scalar(
                select(func.count())
                .select_from(Handover)
                .where(Handover.loan_id == loan["id"], Handover.status == "HOAN_TAT")
            )
            == 1
        )


def test_policy_changes_are_versioned_by_new_policy(env):
    admin, member = env["login"]("admin"), env["login"]("an")
    payload = dict(
        name="Chính sách kiểm thử",
        max_days=2,
        buffer_hours=1,
        pickup_hours=2,
        effective_from=(env["clock"][0] - timedelta(minutes=1)).isoformat(),
    )
    created = admin.post("/api/admin/policies", json=payload)
    assert created.status_code == 201, created.text
    policy = created.json()
    payload["max_days"] = 3
    assert admin.put(f"/api/admin/policies/{policy['id']}", json=payload).status_code == 200
    loan = create(member, request_data(env))
    assert loan["policy"]["max_days"] == 3 and loan["policy"]["buffer_hours"] == 1
    payload["max_days"] = 4
    assert admin.put(f"/api/admin/policies/{policy['id']}", json=payload).status_code == 409
    assert admin.delete(f"/api/admin/policies/{policy['id']}").status_code == 409
    assert member.get(f"/api/loans/{loan['id']}").json()["policy"]["max_days"] == 3


def test_maintenance_inspection_and_removed_retirement_keep_history(env):
    manager = env["login"]("ql.hn")
    asset_id = env["assets"]["Webcam Logitech C920"]
    pending = manager.get(f"/api/assets/{asset_id}").json()
    assert (
        manager.post(
            f"/api/assets/{asset_id}/review", json={"approve": True, "version": pending["version"]}
        ).status_code
        == 200
    )
    payload = dict(
        kind="DANH_GIA",
        content="Đã kiểm tra hiện vật và ghi nhận kết quả.",
        basis="Biên bản kiểm tra thiết bị nội bộ.",
        decision="BAO_TRI",
    )
    response = manager.post(f"/api/assets/{asset_id}/events", json=payload)
    assert response.status_code == 201 and response.json()["status"] == "BAO_TRI"
    payload.update(decision="TIEP_TUC", condition="Đã sửa chữa, hoạt động ổn định.")
    response = manager.post(f"/api/assets/{asset_id}/events", json=payload)
    assert response.status_code == 201 and response.json()["status"] == "CHO_CHIA_SE"
    payload["decision"] = "NGUNG_SU_DUNG"
    response = manager.post(f"/api/assets/{asset_id}/events", json=payload)
    assert response.status_code == 422
    payload["decision"] = "TIEP_TUC"
    assert manager.post(f"/api/assets/{asset_id}/events", json=payload).status_code == 201
    history = manager.get(f"/api/assets/{asset_id}/events").json()
    assert sum(e["kind"] == "DANH_GIA" for e in history) == 3
