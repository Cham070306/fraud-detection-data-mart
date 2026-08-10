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

**Kết quả mong đợi:**
- Staging: 6.362.620 dòng loaded
- Fact_Transaction: 6.362.620 dòng
- Reconciliation: PASS ✅

### Bước 5: Train mô hình ML

```powershell
.\scripts\train_model.ps1
```

**Kết quả mong đợi:**
- Model file lưu tại `models/`
- Recall ≥ 0.80, F2-Score ≥ 0.70

### Bước 6: Chấm điểm giao dịch

```powershell
.\scripts\score_transactions.ps1
```

**Kết quả mong đợi:**
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
