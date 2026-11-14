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
