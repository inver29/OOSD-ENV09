-- ENV-09: chia se va tai su dung tai san giua cac don vi.
-- Chay toan bo tap lenh trong SSMS khi tao database ENV09 lan dau.
CREATE DATABASE ENV09;
GO
USE ENV09;
GO

CREATE TABLE dbo.DonVi (
    MaDonVi INT IDENTITY(1,1) NOT NULL,
    TenDonVi NVARCHAR(150) NOT NULL,
    DiaChi NVARCHAR(300) NULL,
    HoatDong BIT NOT NULL DEFAULT 1,
    CONSTRAINT PK_DonVi PRIMARY KEY (MaDonVi)
);
GO

CREATE TABLE dbo.NguoiDung (
    MaNguoiDung INT IDENTITY(1,1) NOT NULL,
    MaDonVi INT NOT NULL,
    TenDangNhap NVARCHAR(100) NOT NULL,
    HoTen NVARCHAR(150) NOT NULL,
    Email NVARCHAR(254) NOT NULL,
    MatKhauBam NVARCHAR(255) NOT NULL,
    HoatDong BIT NOT NULL DEFAULT 1,
    CONSTRAINT PK_NguoiDung PRIMARY KEY (MaNguoiDung),
    CONSTRAINT FK_NguoiDung_MaDonVi FOREIGN KEY (MaDonVi)
        REFERENCES dbo.DonVi(MaDonVi),
    CONSTRAINT UQ_NguoiDung_1 UNIQUE (TenDangNhap),
    CONSTRAINT UQ_NguoiDung_2 UNIQUE (Email)
);
GO

CREATE TABLE dbo.PhanQuyen (
    MaPhanQuyen INT IDENTITY(1,1) NOT NULL,
    MaNguoiDung INT NOT NULL,
    VaiTro NVARCHAR(20) NOT NULL,
    CONSTRAINT PK_PhanQuyen PRIMARY KEY (MaPhanQuyen),
    CONSTRAINT FK_PhanQuyen_MaNguoiDung FOREIGN KEY (MaNguoiDung)
        REFERENCES dbo.NguoiDung(MaNguoiDung),
    CONSTRAINT UQ_PhanQuyen_NguoiDung UNIQUE (MaNguoiDung),
    CONSTRAINT CK_PhanQuyen_VaiTro CHECK (
        VaiTro IN (N'THANH_VIEN', N'QUAN_LY', N'QUAN_TRI'))
);
GO

CREATE TABLE dbo.LoaiTaiSan (
    MaLoaiTaiSan INT IDENTITY(1,1) NOT NULL,
    TenLoaiTaiSan NVARCHAR(150) NOT NULL,
    HoatDong BIT NOT NULL DEFAULT 1,
    CONSTRAINT PK_LoaiTaiSan PRIMARY KEY (MaLoaiTaiSan)
);
GO

CREATE TABLE dbo.DiaDiem (
    MaDiaDiem INT IDENTITY(1,1) NOT NULL,
    MaDonVi INT NOT NULL,
    TenDiaDiem NVARCHAR(150) NOT NULL,
    MoTa NVARCHAR(500) NULL,
    HoatDong BIT NOT NULL DEFAULT 1,
    CONSTRAINT PK_DiaDiem PRIMARY KEY (MaDiaDiem),
    CONSTRAINT FK_DiaDiem_MaDonVi FOREIGN KEY (MaDonVi)
        REFERENCES dbo.DonVi(MaDonVi)
);
GO

CREATE TABLE dbo.TaiSan (
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
        REFERENCES dbo.LoaiTaiSan(MaLoaiTaiSan),
    CONSTRAINT FK_TaiSan_MaDonVi FOREIGN KEY (MaDonVi)
        REFERENCES dbo.DonVi(MaDonVi),
    CONSTRAINT FK_TaiSan_MaDiaDiem FOREIGN KEY (MaDiaDiem)
        REFERENCES dbo.DiaDiem(MaDiaDiem),
    CONSTRAINT FK_TaiSan_MaNguoiPhuTrach FOREIGN KEY (MaNguoiPhuTrach)
        REFERENCES dbo.NguoiDung(MaNguoiDung),
    CONSTRAINT CK_TaiSan_TrangThai CHECK (
        TrangThai IN (N'CHO_DUYET', N'TU_CHOI', N'CHO_CHIA_SE', N'BAO_TRI', N'CHO_THU_HOI'))
);
GO

CREATE TABLE dbo.ChinhSachMuon (
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

CREATE TABLE dbo.NhuCauMuaMoi (
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
        REFERENCES dbo.DonVi(MaDonVi),
    CONSTRAINT FK_NhuCauMuaMoi_MaNguoiLap FOREIGN KEY (MaNguoiLap)
        REFERENCES dbo.NguoiDung(MaNguoiDung),
    CONSTRAINT FK_NhuCauMuaMoi_MaLoaiTaiSan FOREIGN KEY (MaLoaiTaiSan)
        REFERENCES dbo.LoaiTaiSan(MaLoaiTaiSan),
    CONSTRAINT CK_NhuCauMuaMoi_ThoiGian CHECK (
        BatDau < KetThuc),
    CONSTRAINT CK_NhuCauMuaMoi_PhuongAn CHECK (
        PhuongAnNeuKhongMuon IN (N'MUA_MOI', N'HOAN_NHU_CAU')),
    CONSTRAINT CK_NhuCauMuaMoi_TrangThai CHECK (
        TrangThai IN (N'NHAP', N'CHO_XAC_MINH', N'DA_XAC_MINH', N'TU_CHOI'))
);
GO

CREATE TABLE dbo.XacMinhNhuCau (
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
        REFERENCES dbo.NhuCauMuaMoi(MaNhuCauMuaMoi),
    CONSTRAINT FK_XacMinhNhuCau_MaNguoiXacMinh FOREIGN KEY (MaNguoiXacMinh)
        REFERENCES dbo.NguoiDung(MaNguoiDung),
    CONSTRAINT UQ_XacMinhNhuCau_1 UNIQUE (MaNhuCauMuaMoi)
);
GO

CREATE TABLE dbo.PhieuMuon (
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
        REFERENCES dbo.TaiSan(MaTaiSan),
    CONSTRAINT FK_PhieuMuon_MaNguoiMuon FOREIGN KEY (MaNguoiMuon)
        REFERENCES dbo.NguoiDung(MaNguoiDung),
    CONSTRAINT FK_PhieuMuon_MaDonViMuon FOREIGN KEY (MaDonViMuon)
        REFERENCES dbo.DonVi(MaDonVi),
    CONSTRAINT FK_PhieuMuon_MaNhuCauMuaMoi FOREIGN KEY (MaNhuCauMuaMoi)
        REFERENCES dbo.NhuCauMuaMoi(MaNhuCauMuaMoi),
    CONSTRAINT FK_PhieuMuon_MaChinhSachMuon FOREIGN KEY (MaChinhSachMuon)
        REFERENCES dbo.ChinhSachMuon(MaChinhSachMuon),
    CONSTRAINT FK_PhieuMuon_MaNguoiDuyet FOREIGN KEY (MaNguoiDuyet)
        REFERENCES dbo.NguoiDung(MaNguoiDung),
    CONSTRAINT UQ_PhieuMuon_1 UNIQUE (MaYeuCau),
    CONSTRAINT CK_PhieuMuon_ThoiGian CHECK (
        BatDau < KetThuc),
    CONSTRAINT CK_PhieuMuon_NguoiDuyet CHECK (
        MaNguoiDuyet IS NULL OR MaNguoiDuyet <> MaNguoiMuon),
    CONSTRAINT CK_PhieuMuon_TrangThai CHECK (
        TrangThai IN (N'CHO_DUYET', N'CHO_BAN_GIAO', N'TU_CHOI', N'DA_HUY', N'HET_HAN_NHAN', N'DANG_MUON', N'CHO_XAC_NHAN_TRA', N'DA_HOAN_TRA')),
    CONSTRAINT CK_PhieuMuon_DuPhong CHECK (
        GioDuPhongApDung IS NULL OR GioDuPhongApDung >= 0),
    CONSTRAINT CK_PhieuMuon_DaDuyet CHECK (
        TrangThai NOT IN (N'CHO_BAN_GIAO', N'DANG_MUON', N'CHO_XAC_NHAN_TRA', N'DA_HOAN_TRA') OR (MaNguoiDuyet IS NOT NULL AND DuyetLuc IS NOT NULL AND HanNhan IS NOT NULL AND GioDuPhongApDung IS NOT NULL)),
    CONSTRAINT CK_PhieuMuon_HanNhan CHECK (
        HanNhan IS NULL OR (HanNhan > BatDau AND HanNhan <= KetThuc)),
    CONSTRAINT CK_PhieuMuon_Giao CHECK (
        GiaoLuc IS NULL OR (GiaoLuc >= BatDau AND HanNhan IS NOT NULL AND GiaoLuc < HanNhan)),
    CONSTRAINT CK_PhieuMuon_Tra CHECK (
        TraLuc IS NULL OR (GiaoLuc IS NOT NULL AND TraLuc >= GiaoLuc)),
    CONSTRAINT CK_PhieuMuon_DangMuon CHECK (
        TrangThai NOT IN (N'DANG_MUON', N'CHO_XAC_NHAN_TRA', N'DA_HOAN_TRA') OR GiaoLuc IS NOT NULL),
    CONSTRAINT CK_PhieuMuon_DaDong CHECK (
        TrangThai <> N'DA_HOAN_TRA' OR TraLuc IS NOT NULL)
);
GO

CREATE TABLE dbo.BienBanGiaoNhan (
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
        REFERENCES dbo.PhieuMuon(MaPhieuMuon),
    CONSTRAINT FK_BienBanGiaoNhan_MaBenGiao FOREIGN KEY (MaBenGiao)
        REFERENCES dbo.NguoiDung(MaNguoiDung),
    CONSTRAINT FK_BienBanGiaoNhan_MaBenNhan FOREIGN KEY (MaBenNhan)
        REFERENCES dbo.NguoiDung(MaNguoiDung),
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

CREATE TABLE dbo.SuKienVongDoi (
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
        REFERENCES dbo.TaiSan(MaTaiSan),
    CONSTRAINT FK_SuKienVongDoi_MaNguoiGhi FOREIGN KEY (MaNguoiGhi)
        REFERENCES dbo.NguoiDung(MaNguoiDung),
    CONSTRAINT CK_SuKienVongDoi_Loai CHECK (
        Loai IN (N'CAP_NHAT', N'SU_CO', N'XU_LY', N'DANH_GIA')),
    CONSTRAINT CK_SuKienVongDoi_QuyetDinh CHECK (
        QuyetDinh IS NULL OR QuyetDinh IN (N'TIEP_TUC', N'BAO_TRI', N'THU_HOI')),
    CONSTRAINT CK_SuKienVongDoi_DanhGia CHECK (
        (Loai = N'DANH_GIA' AND QuyetDinh IS NOT NULL) OR (Loai <> N'DANH_GIA' AND QuyetDinh IS NULL))
);
GO

-- Luu ma phieu muon de tra cuu sau khi phieu goc bi xoa luc thu hoi.
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
GO

-- Chi muc phuc vu tra cuu va kiem tra lich.
CREATE INDEX IX_PhieuMuon_Lich
    ON dbo.PhieuMuon(MaTaiSan, TrangThai, BatDau, KetThuc);
GO
CREATE INDEX IX_PhieuMuon_NhuCau
    ON dbo.PhieuMuon(MaNhuCauMuaMoi);
GO
CREATE INDEX IX_TaiSan_TraCuu
    ON dbo.TaiSan(MaDonVi, MaLoaiTaiSan, TrangThai);
GO
CREATE INDEX IX_SuKien_TaiSan
    ON dbo.SuKienVongDoi(MaTaiSan, GhiLuc);
GO
CREATE INDEX IX_ThongBaoThuHoi_NguoiNhan ON dbo.ThongBaoThuHoi(MaNguoiNhan, MaThongBao);
GO

-- NANG CAP DATABASE CU
-- Backend tu chon cac batch nay khi database da co cau truc ENV09.

-- Bo sung dia chi, giu nguyen cac dong va lien ket hien co.
IF COL_LENGTH(N'dbo.DonVi', N'DiaChi') IS NULL
BEGIN
    ALTER TABLE dbo.DonVi ADD DiaChi NVARCHAR(300) NULL;
END;
GO

-- Tai san moi cho quan ly chi nhanh duyet. Thu hoi an ho so, giu lien ket phieu cu.
IF COL_LENGTH(N'dbo.TaiSan', N'DaThuHoi') IS NULL
    EXEC(N'ALTER TABLE dbo.TaiSan ADD DaThuHoi BIT NOT NULL CONSTRAINT DF_TaiSan_DaThuHoi DEFAULT 0');

IF EXISTS (SELECT 1 FROM sys.check_constraints
           WHERE parent_object_id = OBJECT_ID(N'dbo.TaiSan')
             AND name = N'CK_TaiSan_TrangThai' AND definition LIKE N'%NHAP%')
BEGIN
    ALTER TABLE dbo.TaiSan DROP CONSTRAINT CK_TaiSan_TrangThai;
    UPDATE dbo.TaiSan SET TrangThai = N'CHO_DUYET' WHERE TrangThai = N'NHAP';
    ALTER TABLE dbo.TaiSan WITH CHECK ADD CONSTRAINT CK_TaiSan_TrangThai CHECK (
        TrangThai IN (N'CHO_DUYET', N'TU_CHOI', N'CHO_CHIA_SE', N'TAM_NGUNG', N'BAO_TRI', N'NGUNG_SU_DUNG'));

    DECLARE @AssetDefault SYSNAME;
    SELECT @AssetDefault = d.name FROM sys.default_constraints d
    JOIN sys.columns c ON c.object_id = d.parent_object_id AND c.column_id = d.parent_column_id
    WHERE d.parent_object_id = OBJECT_ID(N'dbo.TaiSan') AND c.name = N'TrangThai';
    IF @AssetDefault IS NOT NULL
    BEGIN
        DECLARE @DropDefault NVARCHAR(500) = N'ALTER TABLE dbo.TaiSan DROP CONSTRAINT ' + QUOTENAME(@AssetDefault);
        EXEC(@DropDefault);
    END;
    ALTER TABLE dbo.TaiSan ADD CONSTRAINT DF_TaiSan_TrangThai DEFAULT N'CHO_DUYET' FOR TrangThai;
END;
GO

-- Bo yeu cau bat buoc CanCu khi danh gia; giu nguyen du lieu lich su.
IF OBJECT_ID(N'dbo.SuKienVongDoi', N'U') IS NOT NULL
BEGIN
    IF EXISTS (
        SELECT 1 FROM sys.check_constraints
        WHERE parent_object_id = OBJECT_ID(N'dbo.SuKienVongDoi')
            AND name = N'CK_SuKienVongDoi_DanhGia'
            AND definition LIKE N'%CanCu%'
    )
        ALTER TABLE dbo.SuKienVongDoi DROP CONSTRAINT CK_SuKienVongDoi_DanhGia;

    IF NOT EXISTS (
        SELECT 1 FROM sys.check_constraints
        WHERE parent_object_id = OBJECT_ID(N'dbo.SuKienVongDoi')
            AND name = N'CK_SuKienVongDoi_DanhGia'
    )
        ALTER TABLE dbo.SuKienVongDoi WITH CHECK
        ADD CONSTRAINT CK_SuKienVongDoi_DanhGia CHECK (
            (Loai = N'DANH_GIA' AND QuyetDinh IS NOT NULL)
            OR (Loai <> N'DANH_GIA' AND QuyetDinh IS NULL)
        );
END;
GO

-- Chi dung Mua moi / Hoan cho phuong an moi.
-- Neu database cu con phuong an khac, giu rang buoc cu de bao toan ho so lich su.
IF OBJECT_ID(N'dbo.NhuCauMuaMoi', N'U') IS NOT NULL
    AND NOT EXISTS (
        SELECT 1 FROM dbo.NhuCauMuaMoi
        WHERE PhuongAnNeuKhongMuon NOT IN (N'MUA_MOI', N'HOAN_NHU_CAU')
    )
BEGIN
    IF EXISTS (
        SELECT 1 FROM sys.check_constraints
        WHERE parent_object_id = OBJECT_ID(N'dbo.NhuCauMuaMoi')
            AND name = N'CK_NhuCauMuaMoi_PhuongAn'
            AND definition LIKE N'%THUE_NGOAI%'
    )
        ALTER TABLE dbo.NhuCauMuaMoi DROP CONSTRAINT CK_NhuCauMuaMoi_PhuongAn;

    IF NOT EXISTS (
        SELECT 1 FROM sys.check_constraints
        WHERE parent_object_id = OBJECT_ID(N'dbo.NhuCauMuaMoi')
            AND name = N'CK_NhuCauMuaMoi_PhuongAn'
    )
        ALTER TABLE dbo.NhuCauMuaMoi WITH CHECK
        ADD CONSTRAINT CK_NhuCauMuaMoi_PhuongAn
            CHECK (PhuongAnNeuKhongMuon IN (N'MUA_MOI', N'HOAN_NHU_CAU'));
END;
GO

-- Rut gon trang thai; khong xoa phieu hay du lieu lich su khi nang cap.
IF EXISTS (SELECT 1 FROM sys.check_constraints
    WHERE parent_object_id = OBJECT_ID(N'dbo.TaiSan')
      AND name = N'CK_TaiSan_TrangThai'
      AND (definition LIKE N'%TAM_NGUNG%' OR definition LIKE N'%NGUNG_SU_DUNG%'))
BEGIN
    ALTER TABLE dbo.TaiSan DROP CONSTRAINT CK_TaiSan_TrangThai;
    UPDATE dbo.TaiSan SET TrangThai = N'BAO_TRI' WHERE TrangThai = N'TAM_NGUNG';
    UPDATE a SET
        TrangThai = CASE WHEN EXISTS (
            SELECT 1 FROM dbo.PhieuMuon p WHERE p.MaTaiSan = a.MaTaiSan
              AND p.TrangThai IN (N'DANG_MUON', N'CHO_XAC_NHAN_TRA')
        ) THEN N'CHO_THU_HOI' ELSE N'BAO_TRI' END,
        DaThuHoi = CASE WHEN EXISTS (
            SELECT 1 FROM dbo.PhieuMuon p WHERE p.MaTaiSan = a.MaTaiSan
              AND p.TrangThai IN (N'DANG_MUON', N'CHO_XAC_NHAN_TRA')
        ) THEN 0 ELSE 1 END
    FROM dbo.TaiSan a WHERE a.TrangThai = N'NGUNG_SU_DUNG';
    ALTER TABLE dbo.TaiSan WITH CHECK ADD CONSTRAINT CK_TaiSan_TrangThai CHECK (
        TrangThai IN (N'CHO_DUYET', N'TU_CHOI', N'CHO_CHIA_SE', N'BAO_TRI', N'CHO_THU_HOI'));
END;

IF EXISTS (SELECT 1 FROM sys.check_constraints
    WHERE parent_object_id = OBJECT_ID(N'dbo.SuKienVongDoi')
      AND name = N'CK_SuKienVongDoi_QuyetDinh' AND definition LIKE N'%NGUNG_SU_DUNG%')
BEGIN
    ALTER TABLE dbo.SuKienVongDoi DROP CONSTRAINT CK_SuKienVongDoi_QuyetDinh;
    UPDATE dbo.SuKienVongDoi SET QuyetDinh = N'THU_HOI' WHERE QuyetDinh = N'NGUNG_SU_DUNG';
    ALTER TABLE dbo.SuKienVongDoi WITH CHECK ADD CONSTRAINT CK_SuKienVongDoi_QuyetDinh CHECK (
        QuyetDinh IS NULL OR QuyetDinh IN (N'TIEP_TUC', N'BAO_TRI', N'THU_HOI'));
END;
GO

-- Keep legacy grants until the administrator selects one role for each account.
IF OBJECT_ID(N'dbo.PhanQuyen', N'U') IS NOT NULL
    AND NOT EXISTS (
        SELECT 1 FROM dbo.PhanQuyen GROUP BY MaNguoiDung HAVING COUNT(*) > 1
    )
    AND NOT EXISTS (
        SELECT 1 FROM sys.key_constraints
        WHERE parent_object_id = OBJECT_ID(N'dbo.PhanQuyen')
            AND name = N'UQ_PhanQuyen_NguoiDung'
    )
BEGIN
    ALTER TABLE dbo.PhanQuyen ADD CONSTRAINT UQ_PhanQuyen_NguoiDung UNIQUE (MaNguoiDung);
END;
GO

-- MaPhieuMuon is a snapshot. The original loan is deleted on withdrawal.
IF OBJECT_ID(N'dbo.ThongBaoThuHoi', N'U') IS NULL
BEGIN
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
END;
GO

-- Chay trong database ENV09 dang su dung de doi ma trang thai phieu muon.
IF EXISTS (
    SELECT 1
    FROM sys.check_constraints
    WHERE parent_object_id = OBJECT_ID(N'dbo.PhieuMuon')
      AND name = N'CK_PhieuMuon_TrangThai'
      AND (definition LIKE N'%DA_DUYET%' OR definition LIKE N'%DA_DONG%')
)
BEGIN
    DECLARE @OwnTransaction BIT = 0;
    IF @@TRANCOUNT = 0
    BEGIN
        BEGIN TRANSACTION;
        SET @OwnTransaction = 1;
    END;

    BEGIN TRY
        ALTER TABLE dbo.PhieuMuon DROP CONSTRAINT
            CK_PhieuMuon_TrangThai, CK_PhieuMuon_DaDuyet, CK_PhieuMuon_DangMuon, CK_PhieuMuon_DaDong;

        UPDATE dbo.PhieuMuon
        SET TrangThai = CASE TrangThai
            WHEN N'DA_DUYET' THEN N'CHO_BAN_GIAO'
            WHEN N'DA_DONG' THEN N'DA_HOAN_TRA'
        END
        WHERE TrangThai IN (N'DA_DUYET', N'DA_DONG');

        ALTER TABLE dbo.PhieuMuon WITH CHECK ADD
            CONSTRAINT CK_PhieuMuon_TrangThai CHECK (
                TrangThai IN (N'CHO_DUYET', N'CHO_BAN_GIAO', N'TU_CHOI', N'DA_HUY',
                    N'HET_HAN_NHAN', N'DANG_MUON', N'CHO_XAC_NHAN_TRA', N'DA_HOAN_TRA')),
            CONSTRAINT CK_PhieuMuon_DaDuyet CHECK (
                TrangThai NOT IN (N'CHO_BAN_GIAO', N'DANG_MUON', N'CHO_XAC_NHAN_TRA', N'DA_HOAN_TRA')
                OR (MaNguoiDuyet IS NOT NULL AND DuyetLuc IS NOT NULL
                    AND HanNhan IS NOT NULL AND GioDuPhongApDung IS NOT NULL)),
            CONSTRAINT CK_PhieuMuon_DangMuon CHECK (
                TrangThai NOT IN (N'DANG_MUON', N'CHO_XAC_NHAN_TRA', N'DA_HOAN_TRA')
                OR GiaoLuc IS NOT NULL),
            CONSTRAINT CK_PhieuMuon_DaDong CHECK (
                TrangThai <> N'DA_HOAN_TRA' OR TraLuc IS NOT NULL);

        IF @OwnTransaction = 1 COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @OwnTransaction = 1 AND XACT_STATE() <> 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

