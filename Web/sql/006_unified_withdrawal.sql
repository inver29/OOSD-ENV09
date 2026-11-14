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
