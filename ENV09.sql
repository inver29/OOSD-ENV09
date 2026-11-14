-- ENV-09: chia se va tai su dung tai san giua cac don vi.
-- Script tao moi; khong xoa hay ghi de co so du lieu dang co.
CREATE DATABASE ENV09;
GO
USE ENV09;
GO

CREATE TABLE DonVi (
    MaDonVi INT IDENTITY(1,1) NOT NULL,
    TenDonVi NVARCHAR(150) NOT NULL,
    DiaChi NVARCHAR(300) NULL,
    HoatDong BIT NOT NULL DEFAULT 1,
    CONSTRAINT PK_DonVi PRIMARY KEY (MaDonVi)
);
GO

CREATE TABLE NguoiDung (
    MaNguoiDung INT IDENTITY(1,1) NOT NULL,
    MaDonVi INT NOT NULL,
    TenDangNhap NVARCHAR(100) NOT NULL,
    HoTen NVARCHAR(150) NOT NULL,
    Email NVARCHAR(254) NOT NULL,
    MatKhauBam NVARCHAR(255) NOT NULL,
    HoatDong BIT NOT NULL DEFAULT 1,
    CONSTRAINT PK_NguoiDung PRIMARY KEY (MaNguoiDung),
    CONSTRAINT FK_NguoiDung_MaDonVi FOREIGN KEY (MaDonVi)
        REFERENCES DonVi(MaDonVi),
    CONSTRAINT UQ_NguoiDung_1 UNIQUE (TenDangNhap),
    CONSTRAINT UQ_NguoiDung_2 UNIQUE (Email)
);
GO

CREATE TABLE PhanQuyen (
    MaPhanQuyen INT IDENTITY(1,1) NOT NULL,
    MaNguoiDung INT NOT NULL,
    VaiTro NVARCHAR(20) NOT NULL,
    CONSTRAINT PK_PhanQuyen PRIMARY KEY (MaPhanQuyen),
    CONSTRAINT FK_PhanQuyen_MaNguoiDung FOREIGN KEY (MaNguoiDung)
        REFERENCES NguoiDung(MaNguoiDung),
    CONSTRAINT UQ_PhanQuyen_NguoiDung UNIQUE (MaNguoiDung),
    CONSTRAINT CK_PhanQuyen_VaiTro CHECK (
        VaiTro IN (N'THANH_VIEN', N'QUAN_LY', N'QUAN_TRI'))
);
GO

CREATE TABLE LoaiTaiSan (
    MaLoaiTaiSan INT IDENTITY(1,1) NOT NULL,
    TenLoaiTaiSan NVARCHAR(150) NOT NULL,
    HoatDong BIT NOT NULL DEFAULT 1,
    CONSTRAINT PK_LoaiTaiSan PRIMARY KEY (MaLoaiTaiSan)
);
GO

CREATE TABLE DiaDiem (
    MaDiaDiem INT IDENTITY(1,1) NOT NULL,
    MaDonVi INT NOT NULL,
    TenDiaDiem NVARCHAR(150) NOT NULL,
    MoTa NVARCHAR(500) NULL,
    HoatDong BIT NOT NULL DEFAULT 1,
    CONSTRAINT PK_DiaDiem PRIMARY KEY (MaDiaDiem),
    CONSTRAINT FK_DiaDiem_MaDonVi FOREIGN KEY (MaDonVi)
        REFERENCES DonVi(MaDonVi)
);
GO

CREATE TABLE TaiSan (
    MaTaiSan INT IDENTITY(1,1) NOT NULL,
    TenTaiSan NVARCHAR(200) NOT NULL,
    MaLoaiTaiSan INT NOT NULL,
    MaDonVi INT NOT NULL,
    MaDiaDiem INT NOT NULL,
    MaNguoiPhuTrach INT NOT NULL,
    DacTinh NVARCHAR(1000) NULL,
    DuongDanAnh NVARCHAR(500) NULL,
    TinhTrang NVARCHAR(500) NOT NULL,
    TrangThai NVARCHAR(20) NOT NULL DEFAULT N'CHO_DUYET',
    DaThuHoi BIT NOT NULL DEFAULT 0,
    PhienBan ROWVERSION NOT NULL,
    CONSTRAINT PK_TaiSan PRIMARY KEY (MaTaiSan),
    CONSTRAINT FK_TaiSan_MaLoaiTaiSan FOREIGN KEY (MaLoaiTaiSan)
        REFERENCES LoaiTaiSan(MaLoaiTaiSan),
    CONSTRAINT FK_TaiSan_MaDonVi FOREIGN KEY (MaDonVi)
        REFERENCES DonVi(MaDonVi),
    CONSTRAINT FK_TaiSan_MaDiaDiem FOREIGN KEY (MaDiaDiem)
        REFERENCES DiaDiem(MaDiaDiem),
    CONSTRAINT FK_TaiSan_MaNguoiPhuTrach FOREIGN KEY (MaNguoiPhuTrach)
        REFERENCES NguoiDung(MaNguoiDung),
    CONSTRAINT CK_TaiSan_TrangThai CHECK (
        TrangThai IN (N'CHO_DUYET', N'TU_CHOI', N'CHO_CHIA_SE', N'BAO_TRI', N'CHO_THU_HOI'))
);
GO

CREATE TABLE ChinhSachMuon (
    MaChinhSachMuon INT IDENTITY(1,1) NOT NULL,
    TenChinhSachMuon NVARCHAR(150) NOT NULL,
    SoNgayMuonToiDa INT NOT NULL,
    GioDuPhong INT NOT NULL DEFAULT 0,
    GioChoNhan INT NOT NULL,
    HieuLucTu DATETIMEOFFSET(0) NOT NULL,
    CONSTRAINT PK_ChinhSachMuon PRIMARY KEY (MaChinhSachMuon),
    CONSTRAINT UQ_ChinhSachMuon_1 UNIQUE (HieuLucTu),
    CONSTRAINT CK_ChinhSachMuon_ThoiHan CHECK (
        SoNgayMuonToiDa > 0 AND GioDuPhong >= 0 AND GioChoNhan > 0)
);
GO

CREATE TABLE NhuCauMuaMoi (
    MaNhuCauMuaMoi INT IDENTITY(1,1) NOT NULL,
    MaDonVi INT NOT NULL,
    MaNguoiLap INT NOT NULL,
    MaLoaiTaiSan INT NOT NULL,
    MucDich NVARCHAR(1000) NOT NULL,
    BatDau DATETIMEOFFSET(0) NOT NULL,
    KetThuc DATETIMEOFFSET(0) NOT NULL,
    PhuongAnNeuKhongMuon NVARCHAR(20) NOT NULL,
    DuongDanCanCu NVARCHAR(500) NULL,
    DaMuaMoi BIT NULL,
    TrangThai NVARCHAR(20) NOT NULL DEFAULT N'NHAP',
    TaoLuc DATETIMEOFFSET(0) NOT NULL DEFAULT SYSDATETIMEOFFSET(),
    CONSTRAINT PK_NhuCauMuaMoi PRIMARY KEY (MaNhuCauMuaMoi),
    CONSTRAINT FK_NhuCauMuaMoi_MaDonVi FOREIGN KEY (MaDonVi)
        REFERENCES DonVi(MaDonVi),
    CONSTRAINT FK_NhuCauMuaMoi_MaNguoiLap FOREIGN KEY (MaNguoiLap)
        REFERENCES NguoiDung(MaNguoiDung),
    CONSTRAINT FK_NhuCauMuaMoi_MaLoaiTaiSan FOREIGN KEY (MaLoaiTaiSan)
        REFERENCES LoaiTaiSan(MaLoaiTaiSan),
    CONSTRAINT CK_NhuCauMuaMoi_ThoiGian CHECK (
        BatDau < KetThuc),
    CONSTRAINT CK_NhuCauMuaMoi_PhuongAn CHECK (
        PhuongAnNeuKhongMuon IN (N'MUA_MOI', N'HOAN_NHU_CAU')),
    CONSTRAINT CK_NhuCauMuaMoi_TrangThai CHECK (
        TrangThai IN (N'NHAP', N'CHO_XAC_MINH', N'DA_XAC_MINH', N'TU_CHOI'))
);
GO

CREATE TABLE XacMinhNhuCau (
    MaXacMinhNhuCau INT IDENTITY(1,1) NOT NULL,
    MaNhuCauMuaMoi INT NOT NULL,
    MaNguoiXacMinh INT NOT NULL,
    XacMinhLuc DATETIMEOFFSET(0) NOT NULL DEFAULT SYSDATETIMEOFFSET(),
    DuDinhMua BIT NOT NULL,
    DapUngMucDich BIT NOT NULL,
    KetLuan NVARCHAR(1000) NOT NULL,
    DuongDanCanCu NVARCHAR(500) NULL,
    CONSTRAINT PK_XacMinhNhuCau PRIMARY KEY (MaXacMinhNhuCau),
    CONSTRAINT FK_XacMinhNhuCau_MaNhuCauMuaMoi FOREIGN KEY (MaNhuCauMuaMoi)
        REFERENCES NhuCauMuaMoi(MaNhuCauMuaMoi),
    CONSTRAINT FK_XacMinhNhuCau_MaNguoiXacMinh FOREIGN KEY (MaNguoiXacMinh)
        REFERENCES NguoiDung(MaNguoiDung),
    CONSTRAINT UQ_XacMinhNhuCau_1 UNIQUE (MaNhuCauMuaMoi)
);
GO

CREATE TABLE PhieuMuon (
    MaPhieuMuon INT IDENTITY(1,1) NOT NULL,
    MaTaiSan INT NOT NULL,
    MaNguoiMuon INT NOT NULL,
    MaDonViMuon INT NOT NULL,
    MaNhuCauMuaMoi INT NULL,
    MaChinhSachMuon INT NOT NULL,
    BatDau DATETIMEOFFSET(0) NOT NULL,
    KetThuc DATETIMEOFFSET(0) NOT NULL,
    MucDichMuon NVARCHAR(1000) NOT NULL,
    TrangThai NVARCHAR(20) NOT NULL DEFAULT N'CHO_DUYET',
    MaNguoiDuyet INT NULL,
    LyDoXuLy NVARCHAR(500) NULL,
    TaoLuc DATETIMEOFFSET(0) NOT NULL DEFAULT SYSDATETIMEOFFSET(),
    DuyetLuc DATETIMEOFFSET(0) NULL,
    HanNhan DATETIMEOFFSET(0) NULL,
    GioDuPhongApDung INT NULL,
    GiaoLuc DATETIMEOFFSET(0) NULL,
    TraLuc DATETIMEOFFSET(0) NULL,
    MaYeuCau UNIQUEIDENTIFIER NOT NULL,
    CONSTRAINT PK_PhieuMuon PRIMARY KEY (MaPhieuMuon),
    CONSTRAINT FK_PhieuMuon_MaTaiSan FOREIGN KEY (MaTaiSan)
        REFERENCES TaiSan(MaTaiSan),
    CONSTRAINT FK_PhieuMuon_MaNguoiMuon FOREIGN KEY (MaNguoiMuon)
        REFERENCES NguoiDung(MaNguoiDung),
    CONSTRAINT FK_PhieuMuon_MaDonViMuon FOREIGN KEY (MaDonViMuon)
        REFERENCES DonVi(MaDonVi),
    CONSTRAINT FK_PhieuMuon_MaNhuCauMuaMoi FOREIGN KEY (MaNhuCauMuaMoi)
        REFERENCES NhuCauMuaMoi(MaNhuCauMuaMoi),
    CONSTRAINT FK_PhieuMuon_MaChinhSachMuon FOREIGN KEY (MaChinhSachMuon)
        REFERENCES ChinhSachMuon(MaChinhSachMuon),
    CONSTRAINT FK_PhieuMuon_MaNguoiDuyet FOREIGN KEY (MaNguoiDuyet)
        REFERENCES NguoiDung(MaNguoiDung),
    CONSTRAINT UQ_PhieuMuon_1 UNIQUE (MaYeuCau),
    CONSTRAINT CK_PhieuMuon_ThoiGian CHECK (
        BatDau < KetThuc),
    CONSTRAINT CK_PhieuMuon_NguoiDuyet CHECK (
        MaNguoiDuyet IS NULL OR MaNguoiDuyet <> MaNguoiMuon),
    CONSTRAINT CK_PhieuMuon_TrangThai CHECK (
        TrangThai IN (N'CHO_DUYET', N'DA_DUYET', N'TU_CHOI', N'DA_HUY', N'HET_HAN_NHAN', N'DANG_MUON', N'CHO_XAC_NHAN_TRA', N'DA_DONG')),
    CONSTRAINT CK_PhieuMuon_DuPhong CHECK (
        GioDuPhongApDung IS NULL OR GioDuPhongApDung >= 0),
    CONSTRAINT CK_PhieuMuon_DaDuyet CHECK (
        TrangThai NOT IN (N'DA_DUYET', N'DANG_MUON', N'CHO_XAC_NHAN_TRA', N'DA_DONG') OR (MaNguoiDuyet IS NOT NULL AND DuyetLuc IS NOT NULL AND HanNhan IS NOT NULL AND GioDuPhongApDung IS NOT NULL)),
    CONSTRAINT CK_PhieuMuon_HanNhan CHECK (
        HanNhan IS NULL OR (HanNhan > BatDau AND HanNhan <= KetThuc)),
    CONSTRAINT CK_PhieuMuon_Giao CHECK (
        GiaoLuc IS NULL OR (GiaoLuc >= BatDau AND HanNhan IS NOT NULL AND GiaoLuc < HanNhan)),
    CONSTRAINT CK_PhieuMuon_Tra CHECK (
        TraLuc IS NULL OR (GiaoLuc IS NOT NULL AND TraLuc >= GiaoLuc)),
    CONSTRAINT CK_PhieuMuon_DangMuon CHECK (
        TrangThai NOT IN (N'DANG_MUON', N'CHO_XAC_NHAN_TRA', N'DA_DONG') OR GiaoLuc IS NOT NULL),
    CONSTRAINT CK_PhieuMuon_DaDong CHECK (
        TrangThai <> N'DA_DONG' OR TraLuc IS NOT NULL)
);
GO

CREATE TABLE BienBanGiaoNhan (
    MaBienBanGiaoNhan INT IDENTITY(1,1) NOT NULL,
    MaPhieuMuon INT NOT NULL,
    Loai NVARCHAR(10) NOT NULL,
    NoiDung NVARCHAR(1000) NOT NULL,
    TinhTrang NVARCHAR(500) NOT NULL,
    DuongDanChungTu NVARCHAR(500) NULL,
    MaBenGiao INT NOT NULL,
    MaBenNhan INT NOT NULL,
    GiaoXacNhanLuc DATETIMEOFFSET(0) NULL,
    NhanXacNhanLuc DATETIMEOFFSET(0) NULL,
    TrangThai NVARCHAR(20) NOT NULL DEFAULT N'NHAP',
    PhienBan INT NOT NULL DEFAULT 1,
    CONSTRAINT PK_BienBanGiaoNhan PRIMARY KEY (MaBienBanGiaoNhan),
    CONSTRAINT FK_BienBanGiaoNhan_MaPhieuMuon FOREIGN KEY (MaPhieuMuon)
        REFERENCES PhieuMuon(MaPhieuMuon),
    CONSTRAINT FK_BienBanGiaoNhan_MaBenGiao FOREIGN KEY (MaBenGiao)
        REFERENCES NguoiDung(MaNguoiDung),
    CONSTRAINT FK_BienBanGiaoNhan_MaBenNhan FOREIGN KEY (MaBenNhan)
        REFERENCES NguoiDung(MaNguoiDung),
    CONSTRAINT UQ_BienBanGiaoNhan_1 UNIQUE (MaPhieuMuon, Loai),
    CONSTRAINT CK_BienBanGiaoNhan_Loai CHECK (
        Loai IN (N'GIAO', N'TRA')),
    CONSTRAINT CK_BienBanGiaoNhan_HaiBen CHECK (
        MaBenGiao <> MaBenNhan),
    CONSTRAINT CK_BienBanGiaoNhan_TrangThai CHECK (
        TrangThai IN (N'NHAP', N'CHO_XAC_NHAN', N'HOAN_TAT', N'DA_HUY')),
    CONSTRAINT CK_BienBanGiaoNhan_PhienBan CHECK (
        PhienBan > 0),
    CONSTRAINT CK_BienBanGiaoNhan_HoanTat CHECK (
        TrangThai <> N'HOAN_TAT' OR (GiaoXacNhanLuc IS NOT NULL AND NhanXacNhanLuc IS NOT NULL))
);
GO

CREATE TABLE SuKienVongDoi (
    MaSuKienVongDoi INT IDENTITY(1,1) NOT NULL,
    MaTaiSan INT NOT NULL,
    MaNguoiGhi INT NULL,
    GhiLuc DATETIMEOFFSET(0) NOT NULL DEFAULT SYSDATETIMEOFFSET(),
    Loai NVARCHAR(30) NOT NULL,
    NoiDung NVARCHAR(1000) NOT NULL,
    CanCu NVARCHAR(1000) NULL,
    QuyetDinh NVARCHAR(20) NULL,
    CONSTRAINT PK_SuKienVongDoi PRIMARY KEY (MaSuKienVongDoi),
    CONSTRAINT FK_SuKienVongDoi_MaTaiSan FOREIGN KEY (MaTaiSan)
        REFERENCES TaiSan(MaTaiSan),
    CONSTRAINT FK_SuKienVongDoi_MaNguoiGhi FOREIGN KEY (MaNguoiGhi)
        REFERENCES NguoiDung(MaNguoiDung),
    CONSTRAINT CK_SuKienVongDoi_Loai CHECK (
        Loai IN (N'CAP_NHAT', N'SU_CO', N'XU_LY', N'DANH_GIA')),
    CONSTRAINT CK_SuKienVongDoi_QuyetDinh CHECK (
        QuyetDinh IS NULL OR QuyetDinh IN (N'TIEP_TUC', N'BAO_TRI', N'THU_HOI')),
    CONSTRAINT CK_SuKienVongDoi_DanhGia CHECK (
        (Loai = N'DANH_GIA' AND QuyetDinh IS NOT NULL) OR (Loai <> N'DANH_GIA' AND QuyetDinh IS NULL))
);
GO

-- Chi muc phuc vu tra cuu va kiem tra lich.
CREATE INDEX IX_PhieuMuon_Lich
    ON PhieuMuon(MaTaiSan, TrangThai, BatDau, KetThuc);
GO
CREATE INDEX IX_PhieuMuon_NhuCau
    ON PhieuMuon(MaNhuCauMuaMoi);
GO
CREATE INDEX IX_TaiSan_TraCuu
    ON TaiSan(MaDonVi, MaLoaiTaiSan, TrangThai);
GO
CREATE INDEX IX_SuKien_TaiSan
    ON SuKienVongDoi(MaTaiSan, GhiLuc);
GO

-- MaPhieuMuon is a snapshot because withdrawal deletes the original loan.
CREATE TABLE dbo.ThongBaoThuHoi (
    MaThongBao INT IDENTITY(1,1) NOT NULL,
    MaNguoiNhan INT NOT NULL,
    MaPhieuMuon INT NOT NULL,
    TenTaiSan NVARCHAR(200) NOT NULL,
    LyDo NVARCHAR(500) NOT NULL,
    TaoLuc DATETIMEOFFSET(0) NOT NULL,
    DocLuc DATETIMEOFFSET(0) NULL,
    CONSTRAINT PK_ThongBaoThuHoi PRIMARY KEY (MaThongBao),
    CONSTRAINT FK_ThongBaoThuHoi_MaNguoiNhan FOREIGN KEY (MaNguoiNhan)
        REFERENCES dbo.NguoiDung(MaNguoiDung),
    CONSTRAINT UQ_ThongBaoThuHoi_Phieu UNIQUE (MaPhieuMuon)
);
CREATE INDEX IX_ThongBaoThuHoi_NguoiNhan ON dbo.ThongBaoThuHoi(MaNguoiNhan, MaThongBao);
GO
