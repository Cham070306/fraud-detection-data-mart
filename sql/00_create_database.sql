/* =============================================================
   00_create_database.sql
   PaySim Fraud Detection Data Mart
   Tao database FraudDW
   Tac gia: Khai (TV2)
   ============================================================= */

USE master;
GO

IF DB_ID(N'FraudDW') IS NULL
BEGIN
    CREATE DATABASE FraudDW;
    PRINT 'Database FraudDW da duoc tao.';
END
ELSE
    PRINT 'Database FraudDW da ton tai, bo qua buoc tao.';
GO

ALTER DATABASE FraudDW SET RECOVERY SIMPLE;
GO

USE FraudDW;
GO
