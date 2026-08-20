# PaySim Fraud Detection Data Mart 🔍

> **Đồ án môn Data Warehouse** — Phát hiện gian lận giao dịch tài chính sử dụng dataset PaySim với kiến trúc Kimball Star Schema, Machine Learning và Business Intelligence Dashboard.

---

## 📋 Tổng quan Dự án

| Mục | Chi tiết |
|-----|---------|
| **Dataset** | [PaySim Synthetic Financial Dataset](https://www.kaggle.com/datasets/ealaxi/paysim1) (Kaggle) |
| **Quy mô** | 6.362.620 giao dịch, ~493 MB |
| **Số giao dịch gian lận** | 8.213 (tỷ lệ ~0.13%) |
| **Kiến trúc Data Mart** | Kimball Star Schema (Bottom-Up) |
| **Database** | SQL Server 2019+ |
| **Ngôn ngữ** | Python 3.11+ |
| **ML Framework** | scikit-learn, LightGBM |
| **BI Tool** | Power BI, Streamlit |

---

## 🏗️ Kiến trúc Hệ thống

```
CSV (PaySim.csv ~493MB)
      │ chunk load (50K rows/batch)
      ▼
┌─────────────────────────────────────────┐
│         STAGING LAYER                   │
│  stg.raw_paysim (SQL Server)            │
└─────────────────┬───────────────────────┘
                  │ ETL: Transform + Validate
                  ▼
┌─────────────────────────────────────────┐
│         DATA MART (Star Schema)         │
│  7 Dimensions + 3 Facts + BI Views      │
└──────────┬───────────────┬──────────────┘
           │               │
           ▼               ▼
  ┌──────────────┐   ┌──────────────────┐
  │  ML PIPELINE │   │  BI DASHBOARD    │
  │  Feature Eng │   │  Power BI 5 trang│
  │  Train Model │   │  Streamlit App   │
  │  Score + Alert│  └──────────────────┘
  └──────────────┘
```

---

## 👥 Thành viên Nhóm

| Vai trò | Phân công |
|---------|-----------|
| **TV1 — BA/Lead** | Tài liệu yêu cầu, Bus Matrix, KPI Dictionary, Decision Policy, README, Báo cáo tổng hợp |
| **TV2 — Data Engineer** | SQL Schema, ETL Pipeline, Data Quality, Reconciliation |
| **TV3 — Data Analyst** | Data Profiling, EDA, Data Dictionary |
| **TV4 — ML Engineer** | Feature Engineering, Train Model, Threshold Tuning, Scoring |
| **TV5 — BI/App Dev** | Power BI Dashboard (5 trang), Streamlit Alert Queue App |

> Tên thật các thành viên xem tại [docs/requirements/project_charter.md](docs/requirements/project_charter.md)

---

## 📁 Cấu trúc Thư mục

```
fraud-detection-data-mart/
├── configs/
│   ├── logging.yaml            # Cấu hình logging
│   ├── model.yaml              # Hyperparameter và cấu hình mô hình ML
│   └── risk_policy.yaml        # Ngưỡng phân loại rủi ro (LOW/MEDIUM/HIGH/CRITICAL)
│
├── dashboard/
│   ├── powerbi/                # File .pbix Power BI
│   └── streamlit/              # Streamlit Alert Queue App
│       ├── app.py
│       ├── pages/
│       │   ├── 1_Overview.py
│       │   ├── 2_Alert_Queue.py
│       │   ├── 3_Model_Performance.py
│       │   └── 4_Operations.py
│       └── components/
│
├── data/
│   ├── raw/                    # ⚠️ KHÔNG commit lên Git (xem .gitignore)
│   ├── interim/                # Dữ liệu trung gian
│   └── processed/              # Feature matrix đã xử lý
│
├── docs/
│   ├── requirements/
│   │   ├── project_charter.md          # ← TV1 bàn giao
│   │   ├── business_requirements.md    # ← TV1 bàn giao
│   │   └── kpi_dictionary.md           # ← TV1 bàn giao
│   ├── design/
│   │   ├── bus_matrix.md               # ← TV1 bàn giao
│   │   └── decision_policy.md          # ← TV1 bàn giao
│   └── reports/                        # ← TV1 tổng hợp báo cáo
│
├── models/                     # Metadata & model card (không lưu file .pkl lớn)
│
├── notebooks/
│   ├── 01_data_understanding.ipynb     # TV3: khám phá & hiểu dữ liệu thô
│   ├── 02_eda.ipynb                    # TV3: phân tích gian lận (EDA)
│   ├── 03_data_quality.ipynb           # TV3: kiểm tra chất lượng dữ liệu
│   ├── 04_model_experiments.ipynb      # TV4: thử nghiệm & huấn luyện mô hình
│   └── 05_threshold_analysis.ipynb     # TV4: tối ưu ngưỡng phân loại
│
├── scripts/                    # Entry-point chạy pipeline (PowerShell)
│   ├── setup_database.ps1      # Bước 1: Tạo Database & Schema
│   ├── run_etl.ps1             # Bước 2: Chạy ETL
│   ├── train_model.ps1         # Bước 3: Train mô hình
│   ├── score_transactions.ps1  # Bước 4: Chấm điểm giao dịch
│   └── run_dashboard.ps1       # Bước 5: Khởi động Streamlit
│
├── sql/                        # SQL DDL & DML scripts
│   ├── 00_create_database.sql
│   ├── 01_create_schemas.sql
│   ├── 02_create_staging_tables.sql
│   ├── 03_create_dimensions.sql
│   ├── 04_create_fact_tables.sql
│   ├── 05_create_constraints_indexes.sql
│   ├── 06_create_bi_views.sql
│   ├── 07_seed_dimensions.sql
│   └── 08_validation_queries.sql
│
├── src/                        # Python source code
│   ├── api/                    # FastAPI scoring service
│   ├── common/                 # Database connector, config loader, logger
│   ├── decision/               # Risk policy engine, alert generator
│   ├── etl/                    # Extract, Transform, Load, Reconciliation
│   ├── features/               # Feature engineering
│   └── models/                 # Train, evaluate, score, threshold selection
│
├── tests/                      # Unit & Integration tests
│   ├── test_transform.py
│   ├── test_data_quality.py
│   ├── test_etl_reconciliation.py
│   ├── test_model_pipeline.py
│   └── test_risk_policy.py
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Chi tiết triển khai ML

> **Phần triển khai của TV4 - ML Engineer:** xây dựng feature, huấn luyện và so sánh mô hình, chọn threshold, chấm điểm gian lận, phân tầng rủi ro và sinh cảnh báo cho 6.362.620 giao dịch PaySim.

---

## Tổng quan

| Hạng mục | Chi tiết |
|---|---|
| **Dataset** | PaySim Synthetic Financial Dataset |
| **Quy mô** | 6.362.620 giao dịch, khoảng 493 MB |
| **Giao dịch gian lận** | 8.213 giao dịch, khoảng 0,13% |
| **Bài toán** | Phân loại mất cân bằng và ưu tiên giao dịch cần điều tra |
| **Mô hình** | Business Rule Baseline, Logistic Regression, Random Forest |
| **Model được chọn** | Random Forest v1.0.0 |
| **Threshold** | 0,32 - chọn trên validation set |
| **Công nghệ** | Python, pandas, scikit-learn, joblib, pytest |
| **Đầu ra** | FraudScore, PredictedFraud, RiskLevel, RecommendedAction và Alert |

> PaySim là dữ liệu mô phỏng. Kết quả của dự án phục vụ học tập và minh họa kiến trúc Data Mart, không phải bằng chứng rằng mô hình sẵn sàng sử dụng trong ngân hàng thực tế.

---

## Phạm vi nhánh `Hoang`

Nhánh này phụ trách luồng Machine Learning:

```text
PaySim CSV / Data Mart
        |
        v
Feature Engineering
        |
        v
Chia Train - Validation - Test theo step
        |
        v
Baseline Rule + Logistic Regression + Random Forest
        |
        v
Chọn threshold trên Validation
        |
        v
FraudScore + PredictedFraud
        |
        v
RiskLevel + RecommendedAction + FactAlert candidate
```

Nguyên tắc quan trọng:

- Không dùng `isFraud` làm feature; đây chỉ là nhãn mục tiêu.
- Loại `isFlaggedFraud`, khóa giao dịch và các trường sinh sau giao dịch khỏi feature.
- Fit preprocessing/model trên train; chọn model và threshold trên validation.
- Test set chỉ dùng để đánh giá cuối.
- Risk policy được tách khỏi model để có thể thay đổi mà không train lại.
- Khóa chống trùng của score/alert là `(TransactionKey, ModelVersion)`.

---

## Kết quả chính thức v1.0.0

### Chia dữ liệu theo thời gian

| Tập dữ liệu | Step | Số dòng | Fraud | Mục đích |
|---|---:|---:|---:|---|
| Train | 1-520 | 6.082.007 | 5.781 | Fit preprocessing và model |
| Validation | 521-631 | 191.147 | 1.180 | So sánh model, chọn threshold |
| Test | 632-743 | 89.466 | 1.252 | Đánh giá cuối |

### So sánh trên validation

| Model | PR-AUC | Precision | Recall | F2 | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| Business Rule Baseline | 0,024149 | 0,030893 | 0,981356 | 0,137191 | 36.326 | 22 |
| Logistic Regression | 0,846412 | 0,640127 | 0,851695 | 0,798887 | 565 | 175 |
| **Random Forest** | **0,999997** | **0,996622** | **1,000000** | **0,999322** | **4** | **0** |

Random Forest được fit trên 500.000 dòng có kiểm soát, giữ toàn bộ fraud trong train và lấy mẫu deterministic từ lớp non-fraud. Validation và test vẫn được đánh giá đầy đủ.

### Kết quả test cuối

| Chỉ số | Kết quả |
|---|---:|
| PR-AUC | 0,999999 |
| Precision | 0,999201 |
| Recall | 0,999201 |
| F2-score | 0,999201 |
| True Negative / False Positive | 88.213 / 1 |
| False Negative / True Positive | 1 / 1.251 |
| Fraud amount capture rate | 99,981267% |

Threshold `0,32` là đề xuất kỹ thuật. Ngưỡng vận hành cuối cùng cần được chủ sở hữu risk policy phê duyệt theo chi phí FP/FN và năng lực xử lý alert.

---

## Cấu trúc phần ML

```text
fraud-detection-data-mart/
|-- configs/
|   `-- risk_policy.yaml                 # LOW/MEDIUM/HIGH/CRITICAL
|-- docs/
|   |-- integration/sql-handoff.md       # Hợp đồng bàn giao sang SQL Server
|   `-- reports/model-report.md          # Báo cáo kết quả model
|-- models/
|   |-- model_card.md                    # Phạm vi, giới hạn và rollback
|   |-- registry.json                    # Phiên bản model và SHA-256
|   |-- *_metadata.json                  # Metrics, split, feature, parameters
|   `-- *_features.json                  # Danh sách feature
|-- notebooks/
|   |-- 04_model_experiments.ipynb       # So sánh model và kết quả chính
|   `-- 05_threshold_analysis.ipynb      # Phân tích threshold
|-- scripts/
|   |-- train_model.py / .ps1            # Entry point huấn luyện
|   |-- score_transactions.py / .ps1     # Entry point scoring theo chunk
|   |-- register_model.py                # Đăng ký model và hash
|   |-- generate_evaluation_artifacts.py # Tạo bảng/biểu đồ đánh giá
|   |-- execute_notebooks.py             # Chạy và kiểm tra notebook
|   `-- export_alerts.py                 # Xuất FactAlert candidate
|-- src/
|   |-- features/                        # Feature engineering chống leakage
|   |-- training/                        # Train, evaluate, threshold, registry
|   |-- scoring/                         # Scoring và idempotency
|   `-- decision/                        # Risk policy, alert, action
|-- tests/                               # Unit tests ML/risk/registry
|-- pytest.ini
|-- requirements.txt
`-- README.md
```

---

## 🚀 Hướng dẫn Cài đặt & Chạy

### Yêu cầu Hệ thống

| Thành phần | Phiên bản tối thiểu |
|-----------|---------------------|
| Python | 3.11+ |
| SQL Server | 2019+ (hoặc SQL Server Express) |
| RAM | 8 GB (khuyến nghị 16 GB) |
| Dung lượng ổ đĩa | 5 GB trống |
| OS | Windows 10/11 hoặc Ubuntu 20.04+ |

### Bước 0: Clone repository và cài đặt thư viện

```powershell
# Clone repo
git clone https://github.com/Cham070306/fraud-detection-data-mart.git
cd fraud-detection-data-mart

# Tạo virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Cài đặt dependencies
pip install -r requirements.txt
```

### Bước 1: Cấu hình môi trường

Tạo file `.env` ở thư mục gốc của dự án với nội dung bên dưới, sau đó chỉnh sửa cho đúng môi trường của bạn:

```powershell
# Tạo file .env mới và mở bằng trình soạn thảo (lưu ý: KHÔNG commit .env lên Git)
notepad .env
```

Nội dung `.env` (điền giá trị thực của bạn vào các dòng có `#` hướng dẫn):
```env
# --- SQL Server Connection ---
DB_SERVER=localhost                    # Tên server hoặc IP (ví dụ: localhost\SQLEXPRESS)
DB_PORT=1433                           # Cổng SQL Server mặc định
DB_NAME=FraudDW                        # Tên database (tạo tự động bởi 00_create_database.sql)
DB_USER=sa                             # Username SQL Server
DB_PASSWORD=YourPassword123!           # Mật khẩu SQL Server — THAY BẰNG GIÁ TRỊ THỰC
DB_DRIVER=ODBC Driver 18 for SQL Server

# --- Paths ---
DATA_RAW_PATH=data/raw/PaySim.csv
DATA_PROCESSED_PATH=data/processed/
MODEL_OUTPUT_PATH=models/
LOG_PATH=logs/

# --- ETL Config ---
ETL_CHUNK_SIZE=50000                   # Số dòng đọc mỗi chunk (tránh tràn RAM)
ETL_LOG_LEVEL=INFO                     # Mức log: DEBUG | INFO | WARNING | ERROR

# --- ML Config ---
RANDOM_STATE=42                        # Seed cho tính tái tạo kết quả
TEST_SIZE=0.2                          # Tỷ lệ tập test (20%)
```

### Bước 2: Tải dataset PaySim

```powershell
# Tải từ Kaggle (cần cài kaggle CLI)
pip install kaggle
kaggle datasets download -d ealaxi/paysim1 -p data\raw --unzip

# Hoặc copy thủ công file CSV vào:
# data\raw\PaySim.csv (hoặc PS_20174392719_1491208443941_log.csv)
```

### Bước 3: Khởi tạo Database SQL Server

```powershell
.\scripts\setup_database.ps1
```

Script này chạy tuần tự các file SQL từ `00_create_database.sql` đến `07_seed_dimensions.sql`.

### Bước 4: Chạy ETL Pipeline

```powershell
.\scripts\run_etl.ps1
```

Hoặc chạy trực tiếp Python:
```powershell
python -m src.etl.run_etl
```

**Kết quả kỳ vọng:**
- Staging: 6.362.620 dòng loaded
- FactTransaction: 6.362.620 dòng
- Reconciliation: PASS ✅

### Bước 5: Train mô hình ML

```powershell
.\scripts\train_model.ps1
```

**Kết quả kỳ vọng:**
- Model file lưu tại `models/`
- Recall ≥ 0.80, F2-Score ≥ 0.70

### Bước 6: Chấm điểm giao dịch

```powershell
.\scripts\score_transactions.ps1
```

**Kết quả kỳ vọng:**
- `FactModelScore`: 6.362.620 records
- `FactAlert`: ~vài nghìn records (HIGH + CRITICAL)

### Bước 7: Khởi động Dashboard

```powershell
# Streamlit Alert Queue App
.\scripts\run_dashboard.ps1

# Hoặc trực tiếp
streamlit run dashboard\streamlit\app.py
```

Truy cập: `http://localhost:8501`

---

## 📊 Tài liệu Tham khảo

| Tài liệu | Mô tả |
|---------|-------|
| [Project Charter](docs/requirements/project_charter.md) | Phạm vi, stakeholders, mục tiêu dự án |
| [Business Requirements](docs/requirements/business_requirements.md) | 8 câu hỏi nghiệp vụ & yêu cầu chức năng |
| [KPI Dictionary](docs/requirements/kpi_dictionary.md) | Định nghĩa và công thức tất cả KPI |
| [Bus Matrix & Star Schema](docs/design/bus_matrix.md) | Thiết kế Data Mart Kimball |
| [Decision Policy](docs/design/decision_policy.md) | Quy tắc phân loại rủi ro & ra quyết định |

---

## ⚠️ Lưu ý Quan trọng

> [!CAUTION]
> **KHÔNG commit các file sau lên Git:**
> - `data/raw/PaySim.csv` (~493 MB)
> - `.env` (chứa credentials SQL Server)
> - `configs/database.yaml` (chứa thông tin kết nối)
> - `models/*.pkl` nếu kích thước lớn

> [!NOTE]
> **Thay đổi ngưỡng Risk Policy:** Chỉ cần sửa `configs/risk_policy.yaml` và chạy lại `score_transactions.ps1` — không cần train lại mô hình.

---

## 📄 License

[MIT License](LICENSE) — Đây là đồ án học thuật, không dùng cho mục đích thương mại.

---

## 📝 Lịch sử Thay đổi

| Phiên bản | Ngày | Người cập nhật | Nội dung thay đổi |
|-----------|------|----------------|-------------------|
| v1.0 | 2026-08-09 | TV1 | Khởi tạo README |
| v1.1 | 2026-08-10 | TV1 | Fix R1: sửa tên bảng `Fact_Transaction` → `FactTransaction` (đồng bộ Bus Matrix); thêm mục Lịch sử Thay đổi |

---

## Kiểm thử và vận hành ML

### Yêu cầu

- Python 3.11 hoặc 3.12.
- Windows PowerShell hoặc terminal tương đương.
- Khuyến nghị RAM 16 GB nếu xử lý toàn bộ PaySim.

### Tạo môi trường

```powershell
git clone --branch develop https://github.com/Cham070306/fraud-detection-data-mart.git
cd fraud-detection-data-mart

python -m venv .venv-ml
.\.venv-ml\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
$env:PYTHONPATH = "."
```

Đặt CSV PaySim cục bộ trong `data/raw/` hoặc truyền đường dẫn trực tiếp khi chạy. Không commit file dữ liệu lớn lên GitHub.

---

## Chạy kiểm thử

```powershell
python -m pytest tests -v
git diff --check
```

Trạng thái nghiệm thu gần nhất: **13/13 test PASS**.

Test bao phủ:

- Feature không chứa target hoặc khóa giao dịch.
- Không có NaN/infinity sau feature engineering.
- Category mới/null khi scoring.
- Probability/FraudScore nằm trong `[0,1]`.
- Giữ đúng thứ tự `TransactionKey`.
- Lưu/nạp model cho kết quả tái lập.
- Biên LOW/MEDIUM/HIGH/CRITICAL.
- Chỉ HIGH/CRITICAL sinh alert.
- Chống trùng score và alert.
- Phát hiện model bị sửa sau khi đăng ký hash.

---

## Huấn luyện model

### Python

```powershell
python -m scripts.train_model `
  --input "data/raw/PS_20174392719_1491204439457_log.csv" `
  --output-dir models `
  --version 1.0.0
```

### PowerShell wrapper

```powershell
.\scripts\train_model.ps1 `
  -InputCsv "data/raw/PS_20174392719_1491204439457_log.csv" `
  -Version "1.0.0"
```

Artifact tạo cục bộ:

- `models/fraud_model_v1.0.0.joblib`
- `models/fraud_model_v1.0.0_metadata.json`
- `models/fraud_model_v1.0.0_features.json`

File `.joblib` được bỏ qua bởi Git vì có thể lớn; metadata, feature list và model card được commit để truy vết.

---

## Chấm điểm giao dịch

```powershell
.\scripts\score_transactions.ps1 `
  -InputCsv "data/raw/PS_20174392719_1491204439457_log.csv" `
  -Version "1.0.0" `
  -OutputCsv "output/model_scoring_full_v1.0.0.csv"
```

Scoring chạy theo chunk 200.000 dòng để hạn chế sử dụng RAM.

Các cột đầu ra chính:

| Cột | Ý nghĩa |
|---|---|
| `TransactionKey` | Khóa giao dịch để đối chiếu |
| `FraudScore` | Điểm/xác suất gian lận từ 0 đến 1 |
| `PredictedFraud` | Nhãn dự đoán theo model threshold |
| `RiskLevel` | LOW, MEDIUM, HIGH hoặc CRITICAL |
| `AlertLevel` | Mức cảnh báo hoặc NONE |
| `AlertStatus` | Trạng thái ban đầu NEW/NONE |
| `RecommendedAction` | Hành động đề xuất |
| `ModelVersion` | Phiên bản model |
| `PolicyVersion` | Phiên bản risk policy |

Kết quả scoring cục bộ v1.0.0:

- 6.362.620 dòng.
- 8.401 giao dịch được dự đoán fraud.
- LOW: 6.354.165; MEDIUM: 237; HIGH: 46; CRITICAL: 8.172.
- 8.218 cảnh báo HIGH + CRITICAL.
- Không trùng `(TransactionKey, ModelVersion)`.

Các CSV scoring/alert lớn nằm trong `output/` cục bộ và không được commit lên GitHub.

---

## Tài liệu bàn giao

| Tài liệu | Nội dung |
|---|---|
| [Model Report](docs/reports/model-report.md) | Split, model comparison, threshold, metrics và giới hạn |
| [Model Card](models/model_card.md) | Intended use, risk, rollback và phiên bản |
| [SQL Handoff](docs/integration/sql-handoff.md) | Schema cột, khóa chống trùng và yêu cầu tích hợp |
| [Model Experiments](notebooks/04_model_experiments.ipynb) | Notebook kết quả thử nghiệm |
| [Threshold Analysis](notebooks/05_threshold_analysis.ipynb) | Notebook phân tích threshold |

---

## Phần chưa tích hợp

Pipeline ML độc lập trên CSV đã hoàn thành. Các mục sau cần phối hợp với Data Engineer/Business Owner:

- Ghi thật vào `FactModelScore` và `FactAlert` trên SQL Server.
- Kiểm tra foreign key, batch, idempotency và reconciliation trong database.
- Chốt chi phí False Positive/False Negative và công suất xử lý alert.
- Phê duyệt threshold/risk policy cho bản release chung.

---

## Lưu ý an toàn

> [!CAUTION]
> Không commit các file sau:
> - CSV PaySim và dữ liệu trong `data/raw/`, `data/processed/`.
> - File scoring/alert lớn trong `output/`.
> - Model binary `models/*.joblib`.
> - `.env`, mật khẩu hoặc chuỗi kết nối SQL Server.
> - `.vendor`, virtual environment, cache Python/Jupyter.

> [!NOTE]
> Có thể thay đổi ngưỡng LOW/MEDIUM/HIGH/CRITICAL trong `configs/risk_policy.yaml` mà không cần train lại model. Tuy nhiên mọi thay đổi policy phải tăng `PolicyVersion` và được kiểm thử lại.

---

## Trạng thái tích hợp

- Mã nguồn ML từ nhánh `Hoang` đã được tích hợp vào `develop`.
- Model candidate: `v1.0.0`.
- ML test: 13/13 PASS.
- Scoring toàn bộ PaySim: hoàn thành cục bộ.
- SQL Server integration: chờ thông tin schema/kết nối.
