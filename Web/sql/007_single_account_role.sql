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
