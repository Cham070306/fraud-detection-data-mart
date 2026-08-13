# KE HOACH NHIEM VU CHI TIET - PHAN KHAI
# PaySim Fraud Detection Data Mart

---

## MUC LUC

1. [Pham vi cong viec](#1-pham-vi-cong-viec)
2. [Nhung gi da co san tu nhanh Hung](#2-nhung-gi-da-co-san-tu-nhanh-hung)
3. [Danh sach file ban giao day du](#3-danh-sach-file-ban-giao-day-du)
4. [Ke hoach theo ngay](#4-ke-hoach-theo-ngay)
5. [Phu thuoc giua cac file](#5-phu-thuoc-giua-cac-file)
6. [Checklist hoan thanh](#6-checklist-hoan-thanh)

---

## 1. Pham vi cong viec

### 1.1. Tu sheet Phan cong (Excel)

| Muc | Mo ta | File ban giao |
|-----|-------|---------------|
| 2. Kho du lieu, SQL va ETL | Thiet ke staging/dim/fact/audit/bi, DDL, ETL chunk, reject, batch log, reconciliation | configs/, sql/, src/common/, src/etl/, scripts/, tests/ |

### 1.2. Tu sheet Luong cong viec (Excel) - Khai lam tat ca

| Ma CV | Giai doan | Cong viec | Ket qua ban giao |
|-------|-----------|-----------|-------------------|
| EDA-01 | Khao sat PaySim | Profile 6.362.620 dong/11 cot; null, trung, domain, mat can bang, insight | Data dictionary, profiling report |
| DW-01 | Thiet ke Kimball | Process, grain, dimensions/facts, bus matrix, star schema, **ERD** | Grain, bus matrix, ERD |
| SQL-01 | Xay dung SQL Server | Tao stg/dim/fact/audit/bi, PK/FK, surrogate key, index, view | DDL chay lai tu dau |
| ETL-01 | ETL va Data Quality | Chunking, chuan hoa, lookup, dim truoc fact, reject, batch log, reconciliation | Pipeline va bao cao DQ |

### 1.3. Tom tat

Khai phu trach tron bo chuoi: **Khao sat du lieu -> Thiet ke DW/ERD -> SQL -> ETL/DQ -> Test**

---

## 2. Nhung gi da co san tu nhanh Hung

| File | Noi dung | Khai dung de lam gi |
|------|----------|---------------------|
| docs/requirements/project_charter.md | Pham vi, muc tieu, kien truc tong the | Hieu yeu cau de thiet ke DW dung |
| docs/requirements/business_requirements.md | 8 cau hoi nghiep vu | Map cau hoi -> view BI |
| docs/requirements/kpi_dictionary.md | Dinh nghia KPI | Dam bao view tra dung KPI |
| docs/design/bus_matrix.md | 7 dim, 3 fact, grain, star schema text ERD | Dung lam co so viet DDL |
| docs/design/decision_policy.md | Risk level, threshold, action mapping | Seed DimRiskPolicy |
| configs/risk_policy.yaml | LOW/MEDIUM/HIGH/CRITICAL config | Doc trong ETL de map risk |
| README.md | Huong dan setup | Bo sung phan ETL/DW |

---

## 3. Danh sach file ban giao day du

### 3.1. Khao sat du lieu (EDA-01)

| STT | File | Bat buoc | Mo ta |
|-----|------|----------|-------|
| 1 | notebooks/01_data_profiling.ipynb | Co | Profile toan bo 6.362.620 dong, 11 cot |
| 2 | notebooks/02_eda_fraud.ipynb | Co | Phan tich fraud pattern, imbalance, insight |
| 3 | docs/data/data_dictionary.xlsx | Co | Dinh nghia tung cot, kieu, domain, vi du |
| 4 | docs/data/profiling_summary.csv | Co | Thong ke: count, null, distinct, min, max, mean |
| 5 | docs/data/data_insights.md | Co | Cac insight chinh anh huong DW va BI |

### 3.2. Thiet ke Kimball + ERD (DW-01)

| STT | File | Bat buoc | Mo ta |
|-----|------|----------|-------|
| 6 | docs/design/star_schema.md | Co | Mo ta grain, dimension, fact, mapping CSV->DW |
| 7 | docs/design/erd.png hoac erd.md | Co | So do ERD voi PK/FK/surrogate key |
| 8 | docs/design/bus_matrix.md | Cap nhat | Bo sung/cap nhat neu can tu goc do ky thuat |

### 3.3. SQL Server / Data Warehouse (SQL-01)

| STT | File | Bat buoc | Mo ta |
|-----|------|----------|-------|
| 9 | sql/00_create_database.sql | Co | Tao DB FraudDW |
| 10 | sql/01_create_schemas.sql | Co | Tao schema stg, dim, fact, audit, bi |
| 11 | sql/02_create_staging_tables.sql | Co | Tao stg.TransactionRaw voi metadata |
| 12 | sql/03_create_dimensions.sql | Co | 7 dimension tables voi surrogate key |
| 13 | sql/04_create_fact_tables.sql | Co | 3 fact tables |
| 14 | sql/05_create_constraints_indexes.sql | Co | PK, FK, unique, check, index |
| 15 | sql/06_create_bi_views.sql | Co | 5 BI views dung ten chuan |
| 16 | sql/07_seed_dimensions.sql | Co | Seed DimTransactionType, DimAmountBand, DimTime, DimDate, DimRiskPolicy |
| 17 | sql/08_validation_queries.sql | Co | Row count, amount sum, orphan FK, duplicate check |

### 3.4. ETL va Data Quality (ETL-01)

| STT | File | Bat buoc | Mo ta |
|-----|------|----------|-------|
| 18 | src/common/config.py | Co | Doc env/yaml, chunk size, DB settings |
| 19 | src/common/database.py | Co | Connection SQL Server, execute/query helpers |
| 20 | src/common/logger.py | Co | Logging file + console theo batch |
| 21 | src/etl/extract.py | Co | Doc CSV theo chunk, validate header |
| 22 | src/etl/transform.py | Co | Ep kieu, chuan hoa, tao cot phu, tach valid/reject |
| 23 | src/etl/validate.py | Co | Rule validation: domain, kieu, null, pattern |
| 24 | src/etl/load_dimensions.py | Co | Upsert DimAccount, load DimDate/DimTime |
| 25 | src/etl/load_facts.py | Co | Lookup surrogate key, insert FactTransaction |
| 26 | src/etl/reconciliation.py | Co | Doi soat row count, amount sum, fraud count, FK |
| 27 | src/etl/run_etl.py | Co | Orchestration: extract->validate->transform->load->reconcile |
| 28 | scripts/run_etl.ps1 | Co | Script chay ETL tu command line |

### 3.5. Test

| STT | File | Bat buoc | Mo ta |
|-----|------|----------|-------|
| 29 | tests/test_transform.py | Co | Test ep kieu, amount band, hour/day mapping |
| 30 | tests/test_data_quality.py | Co | Test invalid type, fraud flag, negative amount |
| 31 | tests/test_etl_reconciliation.py | Co | Test count reconciliation, reject handling |
| 32 | tests/sql/test_star_schema.sql | Co | Test PK/FK, orphan key, unique, view chay duoc |

**TONG CONG: 32 file bat buoc ban giao**

---

## 4. Ke hoach theo ngay

### Ngay 1: Khao sat PaySim + Data Dictionary

| Buoi | Cong viec | File output |
|------|-----------|-------------|
| Sang | Doc CSV, thong ke tong quan, kiem tra null/duplicate/domain | notebooks/01_data_profiling.ipynb |
| Chieu | Phan tich fraud pattern, imbalance, balance behavior | notebooks/02_eda_fraud.ipynb |
| Toi | Chot data dictionary va profiling summary | docs/data/data_dictionary.xlsx, docs/data/profiling_summary.csv |

**Ket thuc ngay 1:** Hieu ro du lieu, co data dictionary, co profiling summary

### Ngay 2: Thiet ke DW + ERD + SQL DDL (phan 1)

| Buoi | Cong viec | File output |
|------|-----------|-------------|
| Sang | Chot grain, mapping CSV->DW, viet star schema doc | docs/design/star_schema.md |
| Chieu | Ve ERD, viet data insights | docs/design/erd.md, docs/data/data_insights.md |
| Toi | Viet sql/00 -> sql/03 (database, schemas, staging, dimensions) | sql/00-03 |

**Ket thuc ngay 2:** Co thiet ke DW hoan chinh, ERD, 4 file SQL dau tien

### Ngay 3: SQL DDL (phan 2) + Seed + Views

| Buoi | Cong viec | File output |
|------|-----------|-------------|
| Sang | Viet sql/04 (fact tables) va sql/05 (constraints, indexes) | sql/04, sql/05 |
| Chieu | Viet sql/06 (BI views) va sql/07 (seed dimensions) | sql/06, sql/07 |
| Toi | Viet sql/08 (validation queries), test chay toan bo DDL | sql/08 |

**Ket thuc ngay 3:** Toan bo 9 file SQL hoan thanh, chay duoc tu dau den cuoi

### Ngay 4: ETL - Extract + Transform + Validate

| Buoi | Cong viec | File output |
|------|-----------|-------------|
| Sang | Viet config.py, database.py, logger.py | src/common/* |
| Chieu | Viet extract.py (chunk reader) va validate.py (rules) | src/etl/extract.py, validate.py |
| Toi | Viet transform.py (ep kieu, cot phu, tach valid/reject) | src/etl/transform.py |

**Ket thuc ngay 4:** Doc duoc CSV, validate, transform thanh cong

### Ngay 5: ETL - Load + Reconciliation

| Buoi | Cong viec | File output |
|------|-----------|-------------|
| Sang | Viet load_dimensions.py (upsert DimAccount, load dim khac) | src/etl/load_dimensions.py |
| Chieu | Viet load_facts.py (lookup key, insert fact) | src/etl/load_facts.py |
| Toi | Viet reconciliation.py va run_etl.py, scripts/run_etl.ps1 | src/etl/reconciliation.py, run_etl.py, scripts/run_etl.ps1 |

**Ket thuc ngay 5:** Pipeline ETL chay duoc end-to-end

### Ngay 6: Test + Review + Chuan bi PR

| Buoi | Cong viec | File output |
|------|-----------|-------------|
| Sang | Viet test_transform.py va test_data_quality.py | tests/test_transform.py, test_data_quality.py |
| Chieu | Viet test_etl_reconciliation.py va test_star_schema.sql | tests/test_etl_reconciliation.py, tests/sql/test_star_schema.sql |
| Toi | Chay toan bo test, review lai tat ca file, chuan bi PR | Bang chung chay thu |

**Ket thuc ngay 6:** Toan bo 32 file hoan thanh, test pass, san sang nop PR

---

## 5. Phu thuoc giua cac file

`
[Nguon: nhanh Hung]
    docs/design/bus_matrix.md -----> co so thiet ke
    docs/design/decision_policy.md -> seed DimRiskPolicy
    configs/risk_policy.yaml ------> ETL doc de map risk

[Giai doan 1: Khao sat]
    CSV PaySim
      |
      v
    notebooks/01_data_profiling.ipynb
      |
      v
    notebooks/02_eda_fraud.ipynb
      |
      v
    docs/data/data_dictionary.xlsx
    docs/data/profiling_summary.csv
    docs/data/data_insights.md

[Giai doan 2: Thiet ke]
    data_dictionary + bus_matrix
      |
      v
    docs/design/star_schema.md
      |
      v
    docs/design/erd.md (hoac erd.png)

[Giai doan 3: SQL]
    star_schema.md + erd
      |
      v
    sql/00 -> sql/01 -> sql/02 -> sql/03 -> sql/04 -> sql/05 -> sql/06 -> sql/07 -> sql/08
    (phai chay theo dung thu tu nay)

[Giai doan 4-5: ETL]
    sql/* (database phai co truoc)
      |
      v
    src/common/config.py (doc truoc tien)
      |
      v
    src/common/database.py (phu thuoc config)
      |
      v
    src/common/logger.py
      |
      v
    src/etl/extract.py (phu thuoc config)
      |
      v
    src/etl/validate.py (doc lap)
      |
      v
    src/etl/transform.py (phu thuoc validate)
      |
      v
    src/etl/load_dimensions.py (phu thuoc database + transform)
      |
      v
    src/etl/load_facts.py (phu thuoc load_dimensions)
      |
      v
    src/etl/reconciliation.py (phu thuoc load_facts)
      |
      v
    src/etl/run_etl.py (goi tat ca module tren)
      |
      v
    scripts/run_etl.ps1 (goi run_etl.py)

[Giai doan 6: Test]
    tests/test_transform.py (phu thuoc transform.py)
    tests/test_data_quality.py (phu thuoc validate.py)
    tests/test_etl_reconciliation.py (phu thuoc reconciliation.py)
    tests/sql/test_star_schema.sql (phu thuoc sql/*)
`

---

## 6. Checklist hoan thanh

### 6.1. Khao sat (EDA-01)
- [ ] Co data dictionary day du 11 cot
- [ ] Co profiling summary voi count, null, distinct, min, max
- [ ] Co insight ve fraud pattern, imbalance, balance behavior
- [ ] Notebook chay duoc tu dau den cuoi

### 6.2. Thiet ke (DW-01)
- [ ] Co star schema document ro grain, dimension, fact
- [ ] Co ERD voi PK/FK/surrogate key
- [ ] Mapping CSV->DW ro rang
- [ ] Nhat quan voi bus_matrix.md cua Hung

### 6.3. SQL (SQL-01)
- [ ] 9 file SQL chay duoc theo thu tu tu 00 den 08
- [ ] 7 dimension co surrogate key
- [ ] 3 fact co FK dung
- [ ] 5 BI views tra duoc du lieu
- [ ] Seed data day du
- [ ] Validation queries pass

### 6.4. ETL (ETL-01)
- [ ] Doc CSV theo chunk (khong load ca file 493MB)
- [ ] Validate domain, null, kieu du lieu
- [ ] Transform: ep kieu, cot phu, tach valid/reject
- [ ] Nap dim truoc, fact sau
- [ ] Co reject log
- [ ] Co batch log (source rows, valid rows, reject rows, thoi gian)
- [ ] Reconciliation pass: row count + amount sum khop

### 6.5. Test
- [ ] test_transform.py pass
- [ ] test_data_quality.py pass
- [ ] test_etl_reconciliation.py pass
- [ ] test_star_schema.sql pass

### 6.6. Tong the
- [ ] Du 32 file ban giao
- [ ] Khong commit CSV goc vao repo
- [ ] Khong viet trung logic giua scripts/ va src/
- [ ] Co the demo luong CSV -> Staging -> DW -> BI Views
- [ ] San sang tao Pull Request vao develop

---

## Lich su thay doi

| Phien ban | Ngay | Nguoi | Noi dung |
|-----------|------|-------|----------|
| v1.0 | 2026-08-10 | Khai | Khoi tao ke hoach nhiem vu chi tiet |
