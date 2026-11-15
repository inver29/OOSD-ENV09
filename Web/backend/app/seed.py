"""Dữ liệu giả định phục vụ trình diễn; chỉ thêm vào database chưa có người dùng."""

from datetime import timedelta
from uuid import uuid4

from sqlalchemy import func, select

from . import domain
from .models import (
    Asset,
    Category,
    Grant,
    Handover,
    LifecycleEvent,
    Loan,
    Location,
    Need,
    Policy,
    Unit,
    User,
    Verification,
)
from .security import hash_password


def proof_pdf(path):
    stream = b"BT /F1 16 Tf 50 760 Td (ENV09 - DEMO PURCHASE REQUEST) Tj 0 -30 Td /F1 11 Tf (One device required for an internal training session.) Tj 0 -20 Td (Plan recorded before borrowing. Illustrative data only.) Tj ET"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    output, offsets = b"%PDF-1.4\n", [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output += f"{index} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(output)
    output += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    output += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    output += f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    path.write_bytes(output)


def seed_demo(db, config, include_images=True):
    if db.scalar(select(func.count()).select_from(User)):
        print("Đã có tài khoản: giữ nguyên dữ liệu, bỏ qua seed demo.")
        return
    if len(config.demo_password.strip()) < 8:
        raise ValueError("Đặt APP_DEMO_PASSWORD ít nhất 8 ký tự trước khi nạp dữ liệu demo.")
    stamp = domain.now()
    units = [
        Unit(name=name, address=address, active=True)
        for name, address in (
            ("Chi nhánh Hà Nội", "120 Trần Duy Hưng, Hà Nội"),
            ("Chi nhánh TP. Hồ Chí Minh", "36 Nguyễn Thị Minh Khai, TP. Hồ Chí Minh"),
            ("Chi nhánh Đà Nẵng", "18 Nguyễn Văn Linh, Đà Nẵng"),
        )
    ]
    categories = [
        Category(name=name, active=True)
        for name in (
            "Máy tính & màn hình",
            "Thiết bị trình chiếu",
            "Máy ảnh & ghi hình",
            "Thiết bị văn phòng",
        )
    ]
    db.add_all(units + categories)
    db.flush()
    locations = [
        Location(
            unit_id=u.id,
            name="Kho thiết bị",
            description="Tầng 2, Bộ phận hành chính",
            active=True,
        )
        for u in units
    ]
    db.add_all(locations)
    password_hash = hash_password(config.demo_password)
    definitions = [
        ("admin", "Quản trị hệ thống", 0, ["QUAN_TRI"]),
        ("ql.hn", "Minh - Quản lý Hà Nội", 0, ["QUAN_LY"]),
        ("ql.hcm", "Linh - Quản lý TP. HCM", 1, ["QUAN_LY"]),
        ("ql.dn", "Huy - Quản lý Đà Nẵng", 2, ["QUAN_LY"]),
        ("an", "Nguyễn An", 1, ["THANH_VIEN"]),
        ("binh", "Trần Bình", 2, ["THANH_VIEN"]),
        ("chi", "Lê Chi", 0, ["THANH_VIEN"]),
    ]
    users = {}
    for username, name, unit, roles in definitions:
        user = User(
            unit_id=units[unit].id,
            username=username,
            name=name,
            email=f"{username}@env09.example",
            password_hash=password_hash,
            active=True,
            grants=[Grant(role=role) for role in roles],
        )
        db.add(user)
        users[username] = user
    policy = Policy(
        name="Chính sách chia sẻ nội bộ",
        max_days=14,
        buffer_hours=2,
        pickup_hours=24,
        effective_from=stamp - timedelta(days=365),
    )
    db.add(policy)
    db.flush()
    specifications = [
        (
            "Máy chiếu Epson EB-X49",
            1,
            0,
            "3.600 lumen, HDMI, kèm túi và dây nguồn",
            "CHO_CHIA_SE",
        ),
        (
            "Màn hình Dell 24 inch",
            0,
            0,
            "Full HD, HDMI / DisplayPort, kèm chân đế",
            "CHO_CHIA_SE",
        ),
        (
            "Laptop Lenovo ThinkPad E14",
            0,
            0,
            "Core i5, RAM 16 GB, SSD 512 GB",
            "CHO_CHIA_SE",
        ),
        (
            "Máy ảnh Canon EOS M50",
            2,
            0,
            "Ống kính 15–45 mm, 2 pin, thẻ nhớ 64 GB",
            "CHO_CHIA_SE",
        ),
        (
            "Máy in Brother HL-L2321D",
            3,
            0,
            "In laser đen trắng, in hai mặt",
            "BAO_TRI",
        ),
        ("Webcam Logitech C920", 2, 0, "Ghi hình Full HD, cổng USB", "CHO_DUYET"),
        (
            "Laptop HP ProBook 450",
            0,
            1,
            "Core i5, RAM 16 GB, SSD 256 GB",
            "CHO_CHIA_SE",
        ),
        (
            "Máy chiếu BenQ MW550",
            1,
            1,
            "3.600 lumen, kèm điều khiển và HDMI",
            "CHO_CHIA_SE",
        ),
        ("Máy scan Canon LiDE 300", 3, 1, "Quét A4, kết nối USB", "CHO_CHIA_SE"),
        ("Màn hình LG 27 inch", 0, 2, "IPS, QHD, kèm dây HDMI", "CHO_CHIA_SE"),
        ("Máy ảnh Sony ZV-E10", 2, 2, "Ống kính kit, pin và bộ sạc", "CHO_CHIA_SE"),
        ("Máy in HP LaserJet", 3, 2, "Đang chờ kiểm tra bộ phận kéo giấy", "BAO_TRI"),
    ]
    assets = []
    managers = [users["ql.hn"], users["ql.hcm"], users["ql.dn"]]
    for name, category, unit, description, status in specifications:
        asset = Asset(
            name=name,
            category_id=categories[category].id,
            unit_id=units[unit].id,
            location_id=locations[unit].id,
            custodian_id=managers[unit].id,
            description=description,
            condition="Hoạt động tốt, đủ phụ kiện." if status not in {"BAO_TRI"} else description,
            status=status,
        )
        db.add(asset)
        assets.append(asset)
    db.flush()
    for asset in assets:
        db.add(
            LifecycleEvent(
                asset_id=asset.id,
                actor_id=asset.custodian_id,
                created_at=stamp - timedelta(days=70),
                kind="CAP_NHAT",
                content="Đăng ký tài sản trong bộ dữ liệu minh họa.",
            )
        )

    def loan(asset, borrower, start, end, status, need=None):
        manager = next(m for m in managers if m.unit_id == asset.unit_id)
        item = Loan(
            asset_id=asset.id,
            borrower_id=borrower.id,
            borrower_unit_id=borrower.unit_id,
            need_id=need.id if need else None,
            policy_id=policy.id,
            start_at=start,
            end_at=end,
            purpose="Sử dụng cho buổi đào tạo nội bộ.",
            status=status,
            created_at=start - timedelta(days=2),
            request_id=str(uuid4()),
        )
        if status != "CHO_DUYET":
            item.approver_id, item.decided_at = manager.id, start - timedelta(days=1)
            item.pickup_deadline, item.buffer_hours = (
                min(start + timedelta(hours=24), end),
                2,
            )
        if status in domain.HOLDING | {"DA_HOAN_TRA"}:
            item.handed_at = start + timedelta(minutes=10)
        if status == "DA_HOAN_TRA":
            item.returned_at = end - timedelta(hours=1)
        db.add(item)
        db.flush()
        if item.handed_at:
            db.add(
                Handover(
                    loan_id=item.id,
                    kind="GIAO",
                    content="Đã kiểm tra hiện vật và đủ phụ kiện.",
                    condition="Đạt",
                    giver_id=manager.id,
                    receiver_id=borrower.id,
                    giver_confirmed_at=item.handed_at,
                    receiver_confirmed_at=item.handed_at,
                    status="HOAN_TAT",
                    version=1,
                )
            )
        if item.returned_at:
            db.add(
                Handover(
                    loan_id=item.id,
                    kind="TRA",
                    content="Đã nhận trả, thiết bị hoạt động tốt.",
                    condition="Đạt",
                    giver_id=borrower.id,
                    receiver_id=manager.id,
                    giver_confirmed_at=item.returned_at,
                    receiver_confirmed_at=item.returned_at,
                    status="HOAN_TAT",
                    version=1,
                )
            )
        return item

    loan(
        assets[0],
        users["an"],
        stamp + timedelta(days=2),
        stamp + timedelta(days=4),
        "CHO_DUYET",
    )
    loan(
        assets[1],
        users["an"],
        stamp - timedelta(hours=1),
        stamp + timedelta(days=2),
        "CHO_BAN_GIAO",
    )
    loan(
        assets[2],
        users["binh"],
        stamp - timedelta(days=1),
        stamp + timedelta(days=1),
        "DANG_MUON",
    )
    loan(
        assets[3],
        users["an"],
        stamp - timedelta(days=2),
        stamp - timedelta(hours=1),
        "CHO_XAC_NHAN_TRA",
    )

    config.storage_dir.mkdir(parents=True, exist_ok=True)
    proof = f"{users['chi'].id}-{uuid4().hex}.pdf"
    proof_pdf(config.storage_dir / proof)
    for index in range(4):
        start = stamp - timedelta(days=30 - index * 5)
        end = start + timedelta(days=2)
        need = Need(
            unit_id=units[0].id,
            creator_id=users["chi"].id,
            category_id=categories[0].id,
            purpose=f"Trang bị máy tính cho đợt đào tạo số {index + 1}.",
            start_at=start,
            end_at=end,
            alternative="MUA_MOI",
            evidence_path=proof,
            purchased=index == 2,
            status="DA_XAC_MINH",
            created_at=start - timedelta(days=5),
        )
        db.add(need)
        db.flush()
        loan(assets[6], users["chi"], start, end, "DA_HOAN_TRA", need)
        db.add(
            Verification(
                need_id=need.id,
                verifier_id=users["ql.hn"].id,
                verified_at=end + timedelta(days=1),
                intended_purchase=True,
                purpose_met=index < 2,
                conclusion="Đã đối chiếu nhu cầu ban đầu và kết quả sử dụng thiết bị.",
                evidence_path=proof,
            )
        )
    db.flush()
    if include_images:
        from .demo_assets import apply_demo_images

        apply_demo_images(db, config)
    print(
        "Đã thêm dữ liệu minh họa: 7 tài khoản, 12 tài sản, 4 nhu cầu và các phiếu mượn liên quan."
    )
