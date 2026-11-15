from datetime import datetime

from sqlalchemy import Boolean, FetchedValue, ForeignKey, Integer, Unicode
from sqlalchemy.dialects.mssql import DATETIMEOFFSET, ROWVERSION, UNIQUEIDENTIFIER
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Unit(Base):
    __tablename__ = "DonVi"
    id: Mapped[int] = mapped_column("MaDonVi", primary_key=True)
    name: Mapped[str] = mapped_column("TenDonVi", Unicode(150))
    address: Mapped[str | None] = mapped_column("DiaChi", Unicode(300))
    active: Mapped[bool] = mapped_column("HoatDong", Boolean, default=True)


class User(Base):
    __tablename__ = "NguoiDung"
    id: Mapped[int] = mapped_column("MaNguoiDung", primary_key=True)
    unit_id: Mapped[int] = mapped_column("MaDonVi", ForeignKey("DonVi.MaDonVi"))
    username: Mapped[str] = mapped_column("TenDangNhap", Unicode(100))
    name: Mapped[str] = mapped_column("HoTen", Unicode(150))
    email: Mapped[str] = mapped_column("Email", Unicode(254))
    password_hash: Mapped[str] = mapped_column("MatKhauBam", Unicode(255))
    active: Mapped[bool] = mapped_column("HoatDong", Boolean, default=True)
    unit: Mapped[Unit] = relationship(lazy="joined")
    grants: Mapped[list["Grant"]] = relationship(lazy="selectin", cascade="all, delete-orphan")

    @property
    def roles(self) -> list[str]:
        return [grant.role for grant in self.grants]


class Grant(Base):
    __tablename__ = "PhanQuyen"
    id: Mapped[int] = mapped_column("MaPhanQuyen", primary_key=True)
    user_id: Mapped[int] = mapped_column("MaNguoiDung", ForeignKey("NguoiDung.MaNguoiDung"))
    role: Mapped[str] = mapped_column("VaiTro", Unicode(20))


class Category(Base):
    __tablename__ = "LoaiTaiSan"
    id: Mapped[int] = mapped_column("MaLoaiTaiSan", primary_key=True)
    name: Mapped[str] = mapped_column("TenLoaiTaiSan", Unicode(150))
    active: Mapped[bool] = mapped_column("HoatDong", Boolean, default=True)


class Location(Base):
    __tablename__ = "DiaDiem"
    id: Mapped[int] = mapped_column("MaDiaDiem", primary_key=True)
    unit_id: Mapped[int] = mapped_column("MaDonVi", ForeignKey("DonVi.MaDonVi"))
    name: Mapped[str] = mapped_column("TenDiaDiem", Unicode(150))
    description: Mapped[str | None] = mapped_column("MoTa", Unicode(500))
    active: Mapped[bool] = mapped_column("HoatDong", Boolean, default=True)


class Asset(Base):
    __tablename__ = "TaiSan"
    id: Mapped[int] = mapped_column("MaTaiSan", primary_key=True)
    name: Mapped[str] = mapped_column("TenTaiSan", Unicode(200))
    category_id: Mapped[int] = mapped_column("MaLoaiTaiSan", ForeignKey("LoaiTaiSan.MaLoaiTaiSan"))
    unit_id: Mapped[int] = mapped_column("MaDonVi", ForeignKey("DonVi.MaDonVi"))
    location_id: Mapped[int] = mapped_column("MaDiaDiem", ForeignKey("DiaDiem.MaDiaDiem"))
    custodian_id: Mapped[int] = mapped_column(
        "MaNguoiPhuTrach", ForeignKey("NguoiDung.MaNguoiDung")
    )
    description: Mapped[str | None] = mapped_column("DacTinh", Unicode(1000))
    image_path: Mapped[str | None] = mapped_column("DuongDanAnh", Unicode(500))
    condition: Mapped[str] = mapped_column("TinhTrang", Unicode(500))
    status: Mapped[str] = mapped_column("TrangThai", Unicode(20), default="CHO_DUYET")
    withdrawn: Mapped[bool] = mapped_column("DaThuHoi", Boolean, default=False)
    version: Mapped[bytes] = mapped_column(
        "PhienBan",
        ROWVERSION,
        server_default=FetchedValue(),
        server_onupdate=FetchedValue(),
    )
    category: Mapped[Category] = relationship(lazy="joined")
    unit: Mapped[Unit] = relationship(lazy="joined")
    location: Mapped[Location] = relationship(lazy="joined")
    custodian: Mapped[User] = relationship(lazy="joined")


class Policy(Base):
    __tablename__ = "ChinhSachMuon"
    id: Mapped[int] = mapped_column("MaChinhSachMuon", primary_key=True)
    name: Mapped[str] = mapped_column("TenChinhSachMuon", Unicode(150))
    max_days: Mapped[int] = mapped_column("SoNgayMuonToiDa", Integer)
    buffer_hours: Mapped[int] = mapped_column("GioDuPhong", Integer, default=0)
    pickup_hours: Mapped[int] = mapped_column("GioChoNhan", Integer)
    effective_from: Mapped[datetime] = mapped_column("HieuLucTu", DATETIMEOFFSET(0))


class Need(Base):
    __tablename__ = "NhuCauMuaMoi"
    id: Mapped[int] = mapped_column("MaNhuCauMuaMoi", primary_key=True)
    unit_id: Mapped[int] = mapped_column("MaDonVi", ForeignKey("DonVi.MaDonVi"))
    creator_id: Mapped[int] = mapped_column("MaNguoiLap", ForeignKey("NguoiDung.MaNguoiDung"))
    category_id: Mapped[int] = mapped_column("MaLoaiTaiSan", ForeignKey("LoaiTaiSan.MaLoaiTaiSan"))
    purpose: Mapped[str] = mapped_column("MucDich", Unicode(1000))
    start_at: Mapped[datetime] = mapped_column("BatDau", DATETIMEOFFSET(0))
    end_at: Mapped[datetime] = mapped_column("KetThuc", DATETIMEOFFSET(0))
    alternative: Mapped[str] = mapped_column("PhuongAnNeuKhongMuon", Unicode(20))
    evidence_path: Mapped[str | None] = mapped_column("DuongDanCanCu", Unicode(500))
    purchased: Mapped[bool | None] = mapped_column("DaMuaMoi", Boolean)
    status: Mapped[str] = mapped_column("TrangThai", Unicode(20), default="NHAP")
    created_at: Mapped[datetime] = mapped_column("TaoLuc", DATETIMEOFFSET(0))
    creator: Mapped[User] = relationship(lazy="joined")
    unit: Mapped[Unit] = relationship(lazy="joined")
    category: Mapped[Category] = relationship(lazy="joined")
    verification: Mapped["Verification | None"] = relationship(lazy="joined", uselist=False)


class Verification(Base):
    __tablename__ = "XacMinhNhuCau"
    id: Mapped[int] = mapped_column("MaXacMinhNhuCau", primary_key=True)
    need_id: Mapped[int] = mapped_column(
        "MaNhuCauMuaMoi", ForeignKey("NhuCauMuaMoi.MaNhuCauMuaMoi")
    )
    verifier_id: Mapped[int] = mapped_column("MaNguoiXacMinh", ForeignKey("NguoiDung.MaNguoiDung"))
    verified_at: Mapped[datetime] = mapped_column("XacMinhLuc", DATETIMEOFFSET(0))
    intended_purchase: Mapped[bool] = mapped_column("DuDinhMua", Boolean)
    purpose_met: Mapped[bool] = mapped_column("DapUngMucDich", Boolean)
    conclusion: Mapped[str] = mapped_column("KetLuan", Unicode(1000))
    evidence_path: Mapped[str | None] = mapped_column("DuongDanCanCu", Unicode(500))
    verifier: Mapped[User] = relationship(lazy="joined")


class Loan(Base):
    __tablename__ = "PhieuMuon"
    id: Mapped[int] = mapped_column("MaPhieuMuon", primary_key=True)
    asset_id: Mapped[int] = mapped_column("MaTaiSan", ForeignKey("TaiSan.MaTaiSan"))
    borrower_id: Mapped[int] = mapped_column("MaNguoiMuon", ForeignKey("NguoiDung.MaNguoiDung"))
    borrower_unit_id: Mapped[int] = mapped_column("MaDonViMuon", ForeignKey("DonVi.MaDonVi"))
    need_id: Mapped[int | None] = mapped_column(
        "MaNhuCauMuaMoi", ForeignKey("NhuCauMuaMoi.MaNhuCauMuaMoi")
    )
    policy_id: Mapped[int] = mapped_column(
        "MaChinhSachMuon", ForeignKey("ChinhSachMuon.MaChinhSachMuon")
    )
    start_at: Mapped[datetime] = mapped_column("BatDau", DATETIMEOFFSET(0))
    end_at: Mapped[datetime] = mapped_column("KetThuc", DATETIMEOFFSET(0))
    purpose: Mapped[str] = mapped_column("MucDichMuon", Unicode(1000))
    status: Mapped[str] = mapped_column("TrangThai", Unicode(20), default="CHO_DUYET")
    approver_id: Mapped[int | None] = mapped_column(
        "MaNguoiDuyet", ForeignKey("NguoiDung.MaNguoiDung")
    )
    reason: Mapped[str | None] = mapped_column("LyDoXuLy", Unicode(500))
    created_at: Mapped[datetime] = mapped_column("TaoLuc", DATETIMEOFFSET(0))
    decided_at: Mapped[datetime | None] = mapped_column("DuyetLuc", DATETIMEOFFSET(0))
    pickup_deadline: Mapped[datetime | None] = mapped_column("HanNhan", DATETIMEOFFSET(0))
    buffer_hours: Mapped[int | None] = mapped_column("GioDuPhongApDung", Integer)
    handed_at: Mapped[datetime | None] = mapped_column("GiaoLuc", DATETIMEOFFSET(0))
    returned_at: Mapped[datetime | None] = mapped_column("TraLuc", DATETIMEOFFSET(0))
    request_id: Mapped[str] = mapped_column("MaYeuCau", UNIQUEIDENTIFIER(as_uuid=False))
    asset: Mapped[Asset] = relationship(lazy="joined")
    borrower: Mapped[User] = relationship(foreign_keys=[borrower_id], lazy="joined")
    borrower_unit: Mapped[Unit] = relationship(lazy="joined")
    approver: Mapped[User | None] = relationship(foreign_keys=[approver_id], lazy="joined")
    policy: Mapped[Policy] = relationship(lazy="joined")
    reports: Mapped[list["Handover"]] = relationship(lazy="selectin")


class Handover(Base):
    __tablename__ = "BienBanGiaoNhan"
    id: Mapped[int] = mapped_column("MaBienBanGiaoNhan", primary_key=True)
    loan_id: Mapped[int] = mapped_column("MaPhieuMuon", ForeignKey("PhieuMuon.MaPhieuMuon"))
    kind: Mapped[str] = mapped_column("Loai", Unicode(10))
    content: Mapped[str] = mapped_column("NoiDung", Unicode(1000))
    condition: Mapped[str] = mapped_column("TinhTrang", Unicode(500))
    evidence_path: Mapped[str | None] = mapped_column("DuongDanChungTu", Unicode(500))
    giver_id: Mapped[int] = mapped_column("MaBenGiao", ForeignKey("NguoiDung.MaNguoiDung"))
    receiver_id: Mapped[int] = mapped_column("MaBenNhan", ForeignKey("NguoiDung.MaNguoiDung"))
    giver_confirmed_at: Mapped[datetime | None] = mapped_column("GiaoXacNhanLuc", DATETIMEOFFSET(0))
    receiver_confirmed_at: Mapped[datetime | None] = mapped_column(
        "NhanXacNhanLuc", DATETIMEOFFSET(0)
    )
    status: Mapped[str] = mapped_column("TrangThai", Unicode(20), default="NHAP")
    version: Mapped[int] = mapped_column("PhienBan", Integer, default=1)
    giver: Mapped[User] = relationship(foreign_keys=[giver_id], lazy="joined")
    receiver: Mapped[User] = relationship(foreign_keys=[receiver_id], lazy="joined")


class LifecycleEvent(Base):
    __tablename__ = "SuKienVongDoi"
    id: Mapped[int] = mapped_column("MaSuKienVongDoi", primary_key=True)
    asset_id: Mapped[int] = mapped_column("MaTaiSan", ForeignKey("TaiSan.MaTaiSan"))
    actor_id: Mapped[int | None] = mapped_column("MaNguoiGhi", ForeignKey("NguoiDung.MaNguoiDung"))
    created_at: Mapped[datetime] = mapped_column("GhiLuc", DATETIMEOFFSET(0))
    kind: Mapped[str] = mapped_column("Loai", Unicode(30))
    content: Mapped[str] = mapped_column("NoiDung", Unicode(1000))
    basis: Mapped[str | None] = mapped_column("CanCu", Unicode(1000))
    decision: Mapped[str | None] = mapped_column("QuyetDinh", Unicode(20))
    actor: Mapped[User | None] = relationship(lazy="joined")
    asset: Mapped[Asset] = relationship(lazy="joined")


class WithdrawalNotice(Base):
    __tablename__ = "ThongBaoThuHoi"
    id: Mapped[int] = mapped_column("MaThongBao", primary_key=True)
    recipient_id: Mapped[int] = mapped_column("MaNguoiNhan", ForeignKey("NguoiDung.MaNguoiDung"))
    # Keep a snapshot even after the undelivered loan is deleted.
    loan_id: Mapped[int] = mapped_column("MaPhieuMuon", Integer)
    asset_name: Mapped[str] = mapped_column("TenTaiSan", Unicode(200))
    reason: Mapped[str] = mapped_column("LyDo", Unicode(500))
    created_at: Mapped[datetime] = mapped_column("TaoLuc", DATETIMEOFFSET(0))
    read_at: Mapped[datetime | None] = mapped_column("DocLuc", DATETIMEOFFSET(0))
