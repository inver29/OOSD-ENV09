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

