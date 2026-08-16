# PaySim Fraud Detection Data Mart - ML Pipeline

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

## Cài đặt

### Yêu cầu

- Python 3.11 hoặc 3.12.
- Windows PowerShell hoặc terminal tương đương.
- Khuyến nghị RAM 16 GB nếu xử lý toàn bộ PaySim.

### Tạo môi trường

```powershell
git clone --branch Hoang https://github.com/Cham070306/fraud-detection-data-mart.git
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

## Trạng thái nhánh

- Nhánh triển khai: `Hoang`.
- Model candidate: `v1.0.0`.
- ML test: 13/13 PASS.
- Scoring toàn bộ PaySim: hoàn thành cục bộ.
- SQL Server integration: chờ thông tin schema/kết nối.
