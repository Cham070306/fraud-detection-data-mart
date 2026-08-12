# Runbook: Huong dan Setup va Chay Pipeline ETL
# PaySim Fraud Detection Data Mart - Phan Khai (TV2)

---

## 1. Yeu cau he thong

| Thanh phan | Phien ban | Ghi chu |
|-----------|-----------|---------|
| Python | 3.11+ | Da test tren 3.12 |
| SQL Server | 2019+ hoac Express | Hoac LocalDB |
| ODBC Driver | SQL Server 17+ | Kiem tra bang `python -c "import pyodbc; print(pyodbc.drivers())"` |
| Power BI Desktop | Moi nhat | Chi cho TV5 (Dashboard) |

## 2. Cai dat

### 2.1. Clone repository
```powershell
git clone https://github.com/Cham070306/fraud-detection-data-mart.git
cd fraud-detection-data-mart
git checkout Khai
```

### 2.2. Cai Python dependencies
```powershell
python -m pip install -r requirements.txt
```

### 2.3. Dat file CSV PaySim
- Tai file `PS_20174392719_1491204439457_log.csv` (~493 MB)
- Dat vao `data/raw/` (KHONG commit len Git)
- Link: xem file Excel phan cong

### 2.4. Cau hinh database
- Copy `.env.example` thanh `.env` va cap nhat:
  ```
  FRAUD_DB_SERVER=localhost
  FRAUD_DB_NAME=FraudDW
  FRAUD_DB_USER=
  FRAUD_DB_PASSWORD=
  ```
- Hoac copy `configs/app.yaml.example` thanh `configs/app.yaml`

## 3. Tao Database

### 3.1. Chay SQL scripts theo thu tu
Mo SSMS hoac Azure Data Studio, ket noi SQL Server va chay:

```
sql/00_create_database.sql    -- Tao database FraudDW
sql/01_create_schemas.sql     -- Tao 5 schema: stg, dim, fact, audit, bi
sql/02_create_staging_tables.sql  -- Tao staging + 3 bang audit
sql/03_create_dimensions.sql  -- Tao 7 dimension tables
sql/04_create_fact_tables.sql -- Tao 3 fact tables
sql/05_create_constraints_indexes.sql  -- PK/FK/index
sql/06_create_bi_views.sql    -- 5 BI views
sql/07_seed_dimensions.sql    -- Seed DimDate, DimTime, DimTransactionType, DimAmountBand, DimRiskPolicy, DimAccount(UNKNOWN), DimModelVersion
sql/08_validation_queries.sql -- Kiem tra row count, amount, orphan
```

### 3.2. Kiem tra sau khi chay
```sql
SELECT COUNT(*) FROM dim.DimDate;           -- 31 dong
SELECT COUNT(*) FROM dim.DimTime;           -- 24 dong
SELECT COUNT(*) FROM dim.DimTransactionType; -- 5 dong
SELECT COUNT(*) FROM dim.DimAmountBand;     -- 6 dong
SELECT COUNT(*) FROM dim.DimRiskPolicy;     -- 4 dong
SELECT COUNT(*) FROM dim.DimModelVersion;   -- 1 dong
SELECT COUNT(*) FROM dim.DimAccount;        -- 1 dong (UNKNOWN)
```

## 4. Chay ETL Pipeline

### 4.1. Cach 1: Chay bang PowerShell script
```powershell
.\scripts\run_etl.ps1
```

### 4.2. Cach 2: Chay bang Python truc tiep
```powershell
python -m src.etl.run_etl
```

### 4.3. ETL se lam gi
1. Init batch log trong `audit.ETLBatchLog`
2. Doc CSV theo chunk (200.000 dong/chunk)
3. Load tung chunk vao `stg.TransactionRaw`
4. Validate: kiem tra domain, kieu du lieu, gia tri
5. Transform: tinh DateKey, TimeKey, BandCode, BalanceDropOrig
6. Load dimensions: upsert DimAccount
7. Load fact: insert vao FactTransaction
8. Ghi reject vao `audit.RejectLog`
9. Reconciliation: doi soat row count, amount, fraud count
10. Finalize batch log

### 4.4. Ket qua mong doi
```
Source rows:   6.362.620
Valid rows:    6.362.620 (khong co reject vi du lieu PaySim sach)
Fact rows:    6.362.620
Fraud count:  8.213
Amount sum:   ~1.144.392.944.759.77
Status:       SUCCESS
```

## 5. Kiem tra sau ETL

### 5.1. Chay validation queries
```sql
-- File: sql/08_validation_queries.sql
-- Kiem tra row count
SELECT 'fact.FactTransaction' AS T, COUNT_BIG(*) AS Cnt FROM fact.FactTransaction;
-- Ket qua mong doi: 6.362.620

-- Kiem tra fraud count
SELECT IsFraud, COUNT_BIG(*) AS Cnt FROM fact.FactTransaction GROUP BY IsFraud;
-- Ket qua mong doi: 0=6.354.407, 1=8.213

-- Kiem tra batch log
SELECT * FROM audit.ETLBatchLog;
-- Status = SUCCESS

-- Kiem tra reconciliation
SELECT * FROM audit.ReconciliationLog;
-- Status = PASS
```

### 5.2. Kiem tra BI views
```sql
SELECT TOP 10 * FROM bi.vw_TransactionSummary;
SELECT TOP 10 * FROM bi.vw_FraudAnalysis;
SELECT TOP 10 * FROM bi.vw_ETLQuality;
```

## 6. Chay Tests

### 6.1. Tests khong can DB
```powershell
python -m pytest tests/ -v
```
Ket qua mong doi: 9 passed

### 6.2. Tests SQL (can DB)
Mo SSMS va chay `tests/sql/test_star_schema.sql`

## 7. Xử ly loi thuong gap

| Loi | Nguyen nhan | Cach xu ly |
|-----|-------------|-----------|
| ModuleNotFoundError: pyodbc | Chua cai pyodbc | `pip install pyodbc` |
| ODBC Driver not found | Chua cai ODBC driver | Tai tu Microsoft |
| Login failed | Sai thong tin DB | Kiem tra .env hoac app.yaml |
| File CSV khong tim thay | CSV chua dat dung thu muc | Dat vao `data/raw/` |
| Memory error | File qua lon | Giam chunk_size trong app.yaml |

## 8. Cau truc file ban giao

```
docs/data/data_dictionary.xlsx     -- Dinh nghia 11 cot
docs/data/profiling_summary.csv    -- Thong ke tong quan
docs/data/data_insights.md         -- Insight chinh
docs/design/star_schema.md         -- Thiet ke ky thuat
docs/design/erd.md                 -- ERD
notebooks/01_data_profiling.ipynb  -- Profile notebook
notebooks/02_eda_fraud.ipynb       -- EDA notebook
sql/00..08                         -- 9 SQL scripts
src/common/config.py               -- Cau hinh
src/common/database.py             -- DB connection
src/common/logger.py               -- Logging
src/etl/extract.py                 -- Doc CSV
src/etl/validate.py                -- Validation rules
src/etl/transform.py               -- Transform logic
src/etl/load_dimensions.py         -- Load dim
src/etl/load_facts.py              -- Load fact
src/etl/reconciliation.py          -- Doi soat
src/etl/run_etl.py                 -- Orchestration
scripts/run_etl.ps1                -- Entry point
tests/test_*.py                    -- 4 test files (9 tests)
tests/sql/test_star_schema.sql     -- SQL test
```
