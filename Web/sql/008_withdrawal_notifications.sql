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
