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
