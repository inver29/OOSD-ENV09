-- Bo sung dia chi, giu nguyen cac dong va lien ket hien co.
IF COL_LENGTH(N'dbo.DonVi', N'DiaChi') IS NULL
BEGIN
    ALTER TABLE dbo.DonVi ADD DiaChi NVARCHAR(300) NULL;
END;
