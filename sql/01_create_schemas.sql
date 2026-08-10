/* =============================================================
   01_create_schemas.sql
   Tao cac schema: stg, dim, fact, audit, bi
   ============================================================= */

USE FraudDW;
GO

IF SCHEMA_ID(N'stg')   IS NULL EXEC('CREATE SCHEMA stg');
IF SCHEMA_ID(N'dim')   IS NULL EXEC('CREATE SCHEMA dim');
IF SCHEMA_ID(N'fact')  IS NULL EXEC('CREATE SCHEMA fact');
IF SCHEMA_ID(N'audit') IS NULL EXEC('CREATE SCHEMA audit');
IF SCHEMA_ID(N'bi')    IS NULL EXEC('CREATE SCHEMA bi');
GO

PRINT 'Da tao 5 schema: stg, dim, fact, audit, bi';
GO
