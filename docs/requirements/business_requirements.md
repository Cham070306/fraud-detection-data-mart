# Business Requirements
# PaySim Fraud Detection Data Mart

---

## 1. Tóm tắt Nghiệp vụ

Tài liệu này mô tả các yêu cầu nghiệp vụ cho hệ thống **Fraud Detection Data Mart** sử dụng dataset PaySim. Mục tiêu là cung cấp nền tảng dữ liệu và phân tích để trả lời các câu hỏi nghiệp vụ cốt lõi về phát hiện gian lận, đo lường hiệu quả mô hình và hỗ trợ ra quyết định rủi ro.

---

## 2. Tám Câu hỏi Nghiệp vụ Cốt lõi (8 Business Questions)

| # | Câu hỏi Nghiệp vụ | Phân loại | Nguồn trả lời |
|---|-------------------|-----------|-|
| **BQ-01** | Phân bố giao dịch gian lận theo **loại giao dịch** (TRANSFER, CASH_OUT, PAYMENT, DEBIT, CASH_IN) như thế nào? Loại nào chiếm tỷ lệ gian lận cao nhất? | Phân tích Pattern | `fact.FactTransaction` + `dim.DimTransactionType` |
| **BQ-02** | **Thời điểm** nào trong ngày/tuần có mật độ giao dịch gian lận cao nhất? (theo `step` — đơn vị giờ trong 30 ngày) | Phân tích Thời gian | `fact.FactTransaction` + `dim.DimTime` |
| **BQ-03** | **Khoảng giá trị giao dịch** (Amount Band) nào có tỷ lệ gian lận cao nhất? Fraud tập trung ở giao dịch lớn hay nhỏ? | Phân tích Giá trị | `fact.FactTransaction` + `dim.DimAmountBand` |
| **BQ-04** | Tài khoản thực hiện giao dịch gian lận có **pattern số dư bất thường** như thế nào? (oldbalanceOrg → newbalanceOrig sau giao dịch) | Phân tích Pattern | `fact.FactTransaction` + `dim.DimAccount` |
| **BQ-05** | Mô hình ML phát hiện gian lận đạt **Recall và Precision** bao nhiêu? F2-Score (ưu tiên Recall) là bao nhiêu? | Đo lường Mô hình | `fact.FactModelScore` + `dim.DimModelVersion` |
| **BQ-06** | Bao nhiêu phần trăm **tổng thiệt hại tài chính từ gian lận** đã được hệ thống phát hiện và ngăn chặn? (Captured Fraud Loss Rate) | KPI Tài chính | `fact.FactModelScore` + `fact.FactTransaction` *(Tính trên TP của mô hình — dùng FactModelScore thay vì FactAlert vì FactAlert chỉ có HIGH/CRITICAL, sẽ bỏ sót fraud score thấp hơn ngưỡng sinh alert)* |
| **BQ-07** | Số lượng cảnh báo phân bổ theo **mức độ rủi ro** (LOW / MEDIUM / HIGH / CRITICAL) như thế nào? Tỷ lệ False Positive trên từng mức là bao nhiêu? | Vận hành Alert | `fact.FactAlert` + `dim.DimRiskPolicy` |
| **BQ-08** | Pipeline ETL có đảm bảo **tính toàn vẹn dữ liệu** không? Số dòng từ Staging đến Fact có khớp nhau không? (Reconciliation) | Chất lượng Dữ liệu | `stg.raw_paysim` → `fact.FactTransaction` |

---

## 3. Yêu cầu Chức năng (Functional Requirements)

### 3.1 FR-ETL: Pipeline ETL

| ID | Yêu cầu | Mức độ ưu tiên |
|----|---------|----------------|
| FR-ETL-01 | Hệ thống phải đọc file `PaySim.csv` theo chunk (≤ 50.000 dòng/lần) để tránh tràn bộ nhớ. | Must Have |
| FR-ETL-02 | Dữ liệu thô phải được load vào bảng Staging trước khi xử lý. | Must Have |
| FR-ETL-03 | Bước Transform phải validate: kiểu dữ liệu, giá trị không âm cho `amount`, `oldbalance`, `newbalance`. | Must Have |
| FR-ETL-04 | Dimension tables phải được populate trước khi load Fact tables. | Must Have |
| FR-ETL-05 | Sau mỗi lần ETL chạy, hệ thống phải ghi log Reconciliation: tổng dòng input vs. output. | Must Have |
| FR-ETL-06 | Pipeline phải hỗ trợ chạy lại (Idempotent): nếu fail giữa chừng, chạy lại không tạo duplicate. | Should Have |

### 3.2 FR-DM: Data Mart (Star Schema)

| ID | Yêu cầu | Mức độ ưu tiên |
|----|---------|----------------|
| FR-DM-01 | Grain của `FactTransaction` là 1 giao dịch đơn lẻ (1 dòng = 1 giao dịch). | Must Have |
| FR-DM-02 | Phải có 7 bảng Dimension: `DimDate`, `DimTime`, `DimTransactionType`, `DimAccount`, `DimAmountBand`, `DimRiskPolicy`, `DimModelVersion`. | Must Have |
| FR-DM-03 | Phải có 3 bảng Fact: `FactTransaction`, `FactModelScore`, `FactAlert`. | Must Have |
| FR-DM-04 | Tất cả Foreign Key từ Fact đến Dimension phải có Index phù hợp. | Must Have |
| FR-DM-05 | Phải có BI Views cho từng câu hỏi nghiệp vụ chính. | Should Have |

### 3.3 FR-ML: Mô hình Machine Learning

| ID | Yêu cầu | Mức độ ưu tiên |
|----|---------|----------------|
| FR-ML-01 | Mô hình phải được huấn luyện trên dữ liệu từ Data Mart (không phải trực tiếp từ CSV). | Should Have |
| FR-ML-02 | Mô hình phải xuất ra `fraud_score` trong khoảng [0.0, 1.0] cho mỗi giao dịch. | Must Have |
| FR-ML-03 | Ngưỡng phân loại rủi ro phải được đọc từ `configs/risk_policy.yaml` (không hardcode). | Must Have |
| FR-ML-04 | Kết quả scoring phải được lưu vào `FactModelScore` với `ModelVersionKey` tương ứng. | Must Have |
| FR-ML-05 | Mục tiêu tối ưu: **Recall ≥ 0.80** và **F2-Score ≥ 0.70** trên tập test. | Must Have |
| FR-ML-06 | Mô hình đã train phải được lưu kèm metadata (version, date, metrics) vào `DimModelVersion`. | Should Have |

### 3.4 FR-DSS: Hệ thống Hỗ trợ Ra quyết định

| ID | Yêu cầu | Mức độ ưu tiên |
|----|---------|----------------|
| FR-DSS-01 | Hệ thống phải tự động sinh cảnh báo (`FactAlert`) cho các giao dịch có `risk_level` = HIGH hoặc CRITICAL. | Must Have |
| FR-DSS-02 | Mỗi bản ghi trong `FactModelScore` phải có `recommended_action` tương ứng với mức rủi ro: LOW→`ALLOW`, MEDIUM→`STEP_UP_VERIFY`, HIGH→`HOLD_AND_REVIEW`, CRITICAL→`BLOCK_AND_ALERT`. Riêng `FactAlert` (chỉ sinh cho HIGH và CRITICAL) chỉ chứa `HOLD_AND_REVIEW` hoặc `BLOCK_AND_ALERT`. | Must Have |
| FR-DSS-03 | Streamlit Alert Queue phải hiển thị giao dịch nguy hiểm theo thứ tự `fraud_score` giảm dần. | Must Have |
| FR-DSS-04 | Dashboard Power BI phải cập nhật dữ liệu từ SQL Server (DirectQuery hoặc Scheduled Refresh). | Should Have |

### 3.5 FR-BI: Dashboard & Báo cáo

| ID | Trang Dashboard | Nội dung chính |
|----|----------------|----------------|
| FR-BI-01 | **Executive Overview** | Tổng số giao dịch, Fraud Rate, Fraud Amount, Captured Loss Rate |
| FR-BI-02 | **Transaction Analysis** | Phân tích BQ-01, BQ-02, BQ-03, BQ-04 |
| FR-BI-03 | **Model Performance** | Confusion Matrix, Precision, Recall, F2, AUC-PR (BQ-05) |
| FR-BI-04 | **Alert Queue** | Danh sách Alert theo Risk Level, False Positive Rate (BQ-06, BQ-07) |
| FR-BI-05 | **ETL Quality** | Reconciliation Report, row counts, validation errors (BQ-08) |

---

## 4. Yêu cầu Phi chức năng (Non-Functional Requirements)

| ID | Yêu cầu | Tiêu chí đo lường |
|----|---------|-------------------|
| NFR-01 | **Hiệu năng ETL** | Pipeline xử lý 6.362.620 dòng trong < 30 phút trên máy tính thông thường (RAM ≥ 8GB). |
| NFR-02 | **Tính nhất quán dữ liệu** | Row count từ Staging đến Fact chênh lệch 0 dòng (Reconciliation phải pass 100%). |
| NFR-03 | **Khả năng tái tạo (Reproducibility)** | Chạy pipeline từ đầu đến cuối từ README, cho kết quả giống nhau ± 1% (do randomness trong ML). |
| NFR-04 | **Bảo mật thông tin kết nối** | Credentials SQL Server lưu trong `.env` (không commit lên Git). |
| NFR-05 | **Khả năng bảo trì** | Thay đổi ngưỡng Risk Policy chỉ cần sửa `configs/risk_policy.yaml`, không cần sửa code. |
| NFR-06 | **Logging** | Mọi bước ETL và Scoring phải ghi log có timestamp, level (INFO/WARNING/ERROR). |

---

## 5. Ràng buộc Dữ liệu (Data Constraints)

### 5.1 Schema PaySim (nguồn thô)

| Cột | Kiểu dữ liệu | Ý nghĩa | Ràng buộc |
|-----|-------------|---------|-----------|
| `step` | INT | Giờ của giao dịch (1–744, tương đương 30 ngày × 24 giờ) | 1 ≤ step ≤ 744 |
| `type` | VARCHAR | Loại giao dịch | Trong {CASH_IN, CASH_OUT, DEBIT, PAYMENT, TRANSFER} |
| `amount` | DECIMAL(18,2) | Số tiền giao dịch | > 0 |
| `nameOrig` | VARCHAR | ID tài khoản nguồn | Bắt đầu bằng 'C' (Customer) |
| `oldbalanceOrg` | DECIMAL(18,2) | Số dư trước giao dịch (tài khoản nguồn) | ≥ 0 |
| `newbalanceOrig` | DECIMAL(18,2) | Số dư sau giao dịch (tài khoản nguồn) | ≥ 0 |
| `nameDest` | VARCHAR | ID tài khoản đích | Bắt đầu bằng 'C' (Customer) hoặc 'M' (Merchant) |
| `oldbalanceDest` | DECIMAL(18,2) | Số dư trước giao dịch (tài khoản đích) | ≥ 0 |
| `newbalanceDest` | DECIMAL(18,2) | Số dư sau giao dịch (tài khoản đích) | ≥ 0 |
| `isFraud` | BIT | Nhãn gian lận thực tế (Ground Truth) | 0 hoặc 1 |
| `isFlaggedFraud` | BIT | Cờ gian lận của hệ thống gốc PaySim | 0 hoặc 1 |

### 5.2 Quan sát về Dữ liệu Gian lận
- Chỉ 2 loại giao dịch thực sự có gian lận: **TRANSFER** và **CASH_OUT**.
- Giao dịch gian lận thường có `newbalanceOrig = 0` (tài khoản bị rút sạch).
- `isFlaggedFraud` = 1 chỉ với 16 trường hợp — không đáng tin cậy; hệ thống ML sẽ thay thế.

---

## 6. Lịch sử Thay đổi

| Phiên bản | Ngày | Người cập nhật | Nội dung thay đổi |
|-----------|------|----------------|-------------------|
| v1.0 | 2026-08-09 | TV1 | Khởi tạo tài liệu Business Requirements |
| v1.1 | 2026-08-10 | TV1 | Fix B1: FR-DSS-02 phân tách rõ action của FactModelScore (4 mức) vs FactAlert (chỉ HOLD_AND_REVIEW, BLOCK_AND_ALERT); Fix B2: BQ-06 nguồn bảng đồng bộ thành FactModelScore+FactTransaction |
