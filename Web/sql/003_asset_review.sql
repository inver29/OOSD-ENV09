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
