# Kế hoạch kiểm thử — PaySim Fraud Detection Data Mart

## 1. Mục tiêu

Kế hoạch này xác nhận dữ liệu đi đúng chuỗi CSV → staging → dimensions/facts → ML
scoring → alerts → API/Streamlit. Power BI được kiểm thử trong tài liệu bàn giao riêng.

## 2. Phân công

| Nhóm kiểm thử | Thực hiện | Kiểm chứng |
|---|---|---|
| Dữ liệu nguồn, EDA | TV3 Data Analyst | TV2 Data Engineer |
| DDL, ETL, reconciliation, idempotency | TV2 Data Engineer | TV1 BA/Lead |
| Feature, model, threshold, scoring | TV4 ML Engineer | TV3 Data Analyst |
| Nạp score/alert vào SQL | TV2 + TV4 | TV5 BI/App Dev |
| API, Streamlit, feedback | TV5 BI/App Dev | TV1 BA/Lead |
| Nghiệm thu end-to-end | Cả nhóm | TV1 điều phối |

## 3. Điều kiện trước kiểm thử

Máy kiểm thử cần Python 3.11+, SQL Server 2019+, ODBC Driver 17 và file PaySim
trong `data/raw`. Chạy kiểm tra trước:

```powershell
python scripts/preflight.py
```

## 4. Test cases

| ID | Nội dung | Lệnh/bằng chứng | Kỳ vọng |
|---|---|---|---|
| T01 | Unit test ETL/ML | `python -m pytest -q` | Không có test fail |
| T02 | Tạo database | `.\scripts\setup_database.ps1` | 7 dim, 3 fact, BI/audit objects |
| T03 | Full ETL | `.\scripts\run_etl.ps1` | Batch SUCCESS hoặc SUCCESS_WARN |
| T04 | Row reconciliation | `python scripts/run_validation.py` | 6.362.620 fact; 8.213 fraud |
| T05 | Date/time mapping | validation + pytest | 0 mapping error |
| T06 | FK integrity | `sql/08_validation_queries.sql` | 0 orphan |
| T07 | Business duplicates | validation SQL | 0 duplicate group |
| T08 | ETL re-run | chạy ETL lần hai | Fact count không tăng |
| T09 | Train model | `scripts/train_model.ps1` | Có `.joblib` và metadata |
| T10 | Score từ SQL | `.\scripts\score_transactions.ps1 -FromSql` | 6.362.620 score rows trong CSV |
| T11 | Load ML results | `scripts/load_ml_results.ps1` | reconciliation PASS |
| T12 | ML SQL validation | `python scripts/run_validation.py --require-ml` | 6.362.620 score; 8.218 alert |
| T13 | Feedback | Streamlit/API cập nhật một alert | Status và analyst fields đổi đúng |

## 5. Trình tự nghiệm thu

```powershell
python scripts/preflight.py
python -m pytest -q
.\scripts\setup_database.ps1
.\scripts\run_etl.ps1
python scripts/run_validation.py
.\scripts\train_model.ps1 -InputCsv data\raw\PS_20174392719_1491204439457_log.csv
.\scripts\score_transactions.ps1 -FromSql
.\scripts\load_ml_results.ps1
python scripts/run_validation.py --require-ml
.\scripts\run_dashboard.ps1 -Api
```

Lưu output lệnh, ảnh SQL validation và timestamp của batch làm bằng chứng nghiệm thu.

## 6. Tiêu chí dừng

Không demo end-to-end nếu reconciliation FAIL, có orphan/duplicate, score không khớp
TransactionKey hoặc số alert khác nguồn scoring. Metric gần hoàn hảo phải luôn được ghi
chú là kết quả trên dữ liệu PaySim mô phỏng.
