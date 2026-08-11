# Bus Matrix & Star Schema Design
# PaySim Fraud Detection Data Mart

---

## 1. Tổng quan Thiết kế

Dự án sử dụng phương pháp **Kimball Bottom-Up Data Mart** với kiến trúc **Star Schema**. Đây là thiết kế tập trung vào phân tích gian lận giao dịch tài chính từ dataset PaySim.

| Mục | Chi tiết |
|-----|---------|
| **Phương pháp** | Kimball Dimensional Modeling (Bottom-Up) |
| **Mô hình** | Star Schema |
| **Hệ quản trị CSDL** | SQL Server 2019+ |
| **Grain chính** | 1 giao dịch đơn lẻ (1 dòng CSV = 1 dòng FactTransaction) |
| **Số bảng Dimension** | 7 |
| **Số bảng Fact** | 3 |

---

## 2. Kimball Bus Matrix

Ma trận Bus kết nối **Business Processes** (các quy trình nghiệp vụ) với **Dimensions** (các chiều phân tích).

| Business Process | DimDate | DimTime | DimTransactionType | DimAccount | DimAmountBand | DimRiskPolicy | DimModelVersion |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Giao dịch Tài chính** (FactTransaction) | ✅ | ✅ | ✅ | ✅ | ✅ | | |
| **Chấm điểm ML** (FactModelScore) | ✅ | | | | | ✅ | ✅ |
| **Quản lý Cảnh báo** (FactAlert) | ✅ | | | | | ✅ | |

**Chú giải:**
- ✅ = Dimension có FK **trực tiếp** trong bảng Fact này
- Ô trống = Dimension không có FK trực tiếp (truy cập **gián tiếp** qua JOIN với FactTransaction)

> **Lưu ý thiết kế:** `FactModelScore` và `FactAlert` **không** lưu FK trực tiếp đến `DimTime`, `DimTransactionType`, `DimAccount` để tránh redundancy — các chiều này có thể truy vấn qua `JOIN FactTransaction ON TransactionKey`. Nếu yêu cầu phân tích thường xuyên theo giờ/loại GD/tài khoản mà không cần join, TV2 có thể thêm FK trực tiếp vào giai đoạn sau (Cách A — thảo luận với TV1 trước khi thực hiện).

---

## 3. Định nghĩa Grain (Độ chi tiết dữ liệu)

| Bảng Fact | Grain (Độ chi tiết) | Ví dụ |
|-----------|---------------------|-------|
| **FactTransaction** | 1 dòng = 1 giao dịch tài chính đơn lẻ | Giao dịch TRANSFER 50.000 đơn vị từ C1001 → C2002 tại step 100 |
| **FactModelScore** | 1 dòng = 1 kết quả chấm điểm của 1 mô hình cho 1 giao dịch | Model v1.0 cho giao dịch #12345 điểm fraud_score = 0.92 |
| **FactAlert** | 1 dòng = 1 cảnh báo được sinh ra cho 1 giao dịch | Alert CRITICAL cho giao dịch #12345 với action BLOCK_AND_ALERT |

---

## 4. Thiết kế Chi tiết các Bảng

### 4.1 DIMENSION TABLES

#### DimDate — Chiều Ngày
Chuyển đổi từ cột `step` trong PaySim (1 step = 1 giờ, 744 steps = 30 ngày).

> ⚠️ **Lưu ý về dữ liệu mô phỏng:** Ngày tháng trong DimDate là **ngày giả định** — `StepDay` 1 được map vào ngày bắt đầu tuỳ chỉnh (mặc định: 2023-01-01). Không có timestamp thực trong PaySim. Khi báo cáo, cần nêu rõ đây là phân tích trên dữ liệu mô phỏng.

| Cột | Kiểu | Mô tả |
|-----|------|---------|
| `DateKey` | INT (PK) | Surrogate key (YYYYMMDD format, ví dụ: 20230101) |
| `StepDay` | INT | Ngày thứ mấy trong simulation (1–30) |
| `DayOfWeek` | VARCHAR(10) | Thứ trong tuần (Monday, Tuesday...) — **giả định** dựa trên ngày bắt đầu |
| `DayOfWeekNum` | INT | Số thứ tự ngày trong tuần (1=Mon, 7=Sun) |
| `WeekOfSimulation` | INT | Tuần thứ mấy trong simulation (1–5) |
| `IsWeekend` | BIT | 1 nếu là cuối tuần (DayOfWeekNum ∈ {6, 7}) |

#### DimTime — Chiều Giờ
Phân tích thời điểm trong ngày.

> ⚠️ **Lưu ý về dữ liệu mô phỏng:** PaySim không có timestamp thực — `step` (1–744) là giờ trong simulation 30 ngày. `HourOfDay` = `(step - 1) % 24`. Ngày/giờ trong DimTime là **giả định** để phục vụ phân tích pattern, không phải thời gian thực tế.

| Cột | Kiểu | Mô tả |
|-----|------|---------|
| `TimeKey` | INT (PK) | Surrogate key (0–23, tương ứng với giờ trong ngày) |
| `HourOfDay` | INT | Giờ trong ngày (0–23) |
| `TimeSlot` | VARCHAR(20) | Nhóm giờ theo khoảng **[start, end)**: `LATE_NIGHT` [22,24), `NIGHT` [0,6), `MORNING` [6,12), `AFTERNOON` [12,18), `EVENING` [18,22). Tổng cộng 5 giá trị phân biệt, không trùng tên. |
| `IsPeakHour` | BIT | 1 nếu là giờ cao điểm (tạm định nghĩa: 8–11 và 13–17) — **TODO: TV3 xác nhận sau EDA** |

#### DimTransactionType — Chiều Loại Giao dịch

| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `TransactionTypeKey` | INT (PK) | Surrogate key |
| `TypeCode` | VARCHAR(10) | Mã loại: CASH_IN, CASH_OUT, DEBIT, PAYMENT, TRANSFER |
| `TypeName` | NVARCHAR(50) | Tên đầy đủ tiếng Việt |
| `IsHighRiskType` | BIT | 1 nếu loại này có lịch sử gian lận (TRANSFER, CASH_OUT) |
| `Description` | NVARCHAR(200) | Mô tả nghiệp vụ của loại giao dịch |

#### DimAccount — Chiều Tài khoản

> **Thiết kế:** Dimension này chỉ lưu **thuộc tính tĩnh** của tài khoản (Kimball best practice — dimension không chứa aggregate). Các chỉ số tổng hợp như tổng số giao dịch, số lần fraud được tính từ `FactTransaction` qua BI Views.

| Cột | Kiểu | Mô tả |
|-----|------|---------|
| `AccountKey` | INT (PK) | Surrogate key |
| `AccountID` | VARCHAR(20) | Mã tài khoản gốc (nameOrig / nameDest) |
| `AccountType` | CHAR(1) | 'C' = Customer, 'M' = Merchant |

#### DimAmountBand — Chiều Khoảng Giá trị Giao dịch

| Cột | Kiểu | Mô tả |
|-----|------|---------|
| `AmountBandKey` | INT (PK) | Surrogate key |
| `BandCode` | VARCHAR(10) | Mã khoảng: XS, S, M, L, XL, XXL |
| `BandLabel` | NVARCHAR(50) | Nhãn hiển thị: "< 1K", "1K–10K", "10K–100K"... |
| `LowerBound` | DECIMAL(18,2) | Giới hạn dưới **[inclusive]** |
| `UpperBound` | DECIMAL(18,2) | Giới hạn trên **[exclusive]**, NULL cho khoảng cuối (XXL) |
| `RiskWeight` | DECIMAL(5,2) | **TODO:** Trọng số rủi ro — TV3 xác nhận giá trị sau khi hoàn thành EDA (`02_eda.ipynb`). Tạm set = 1.0 cho tất cả bands. |

**Phân khoảng Amount Band:**

| BandCode | BandLabel | Khoảng Giá trị |
|----------|-----------|----------------|
| XS | Rất nhỏ | amount < 1.000 |
| S | Nhỏ | 1.000 ≤ amount < 10.000 |
| M | Trung bình | 10.000 ≤ amount < 100.000 |
| L | Lớn | 100.000 ≤ amount < 1.000.000 |
| XL | Rất lớn | 1.000.000 ≤ amount < 10.000.000 |
| XXL | Cực lớn | amount ≥ 10.000.000 |

#### DimRiskPolicy — Chiều Chính sách Rủi ro

| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `RiskPolicyKey` | INT (PK) | Surrogate key |
| `PolicyVersion` | VARCHAR(10) | Phiên bản policy, ví dụ: "v1.0" |
| `RiskLevel` | VARCHAR(10) | LOW, MEDIUM, HIGH, CRITICAL |
| `ScoreThresholdMin` | DECIMAL(5,4) | Ngưỡng tối thiểu của fraud_score |
| `ScoreThresholdMax` | DECIMAL(5,4) | Ngưỡng tối đa của fraud_score |
| `RecommendedAction` | VARCHAR(30) | ALLOW, STEP_UP_VERIFY, HOLD_AND_REVIEW, BLOCK_AND_ALERT |
| `EffectiveDate` | DATE | Ngày áp dụng policy |
| `IsActive` | BIT | 1 nếu đang được áp dụng |

#### DimModelVersion — Chiều Phiên bản Mô hình ML

| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `ModelVersionKey` | INT (PK) | Surrogate key |
| `ModelName` | VARCHAR(50) | Tên mô hình: "LightGBM", "RandomForest"... |
| `Version` | VARCHAR(10) | Phiên bản: "v1.0", "v1.1"... |
| `TrainDate` | DATE | Ngày huấn luyện |
| `Precision` | DECIMAL(5,4) | Precision trên test set |
| `Recall` | DECIMAL(5,4) | Recall trên test set |
| `F2Score` | DECIMAL(5,4) | F2-Score trên test set |
| `PrAUC` | DECIMAL(5,4) | PR-AUC trên test set |
| `Threshold` | DECIMAL(5,4) | Ngưỡng phân loại được chọn |
| `IsProduction` | BIT | 1 nếu đang được dùng trong Scoring |
| `ModelFilePath` | NVARCHAR(500) | Đường dẫn tới file model (.pkl) |

---

### 4.2 FACT TABLES

#### FactTransaction — Giao dịch Tài chính

> **Grain:** 1 dòng = 1 giao dịch tài chính đơn lẻ từ PaySim

| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `TransactionKey` | BIGINT (PK) | Surrogate key tự tăng |
| `DateKey` | INT (FK → DimDate) | Khóa ngoại chiều Ngày |
| `TimeKey` | INT (FK → DimTime) | Khóa ngoại chiều Giờ |
| `TransactionTypeKey` | INT (FK → DimTransactionType) | Khóa ngoại chiều Loại GD |
| `OrigAccountKey` | INT (FK → DimAccount) | Khóa ngoại tài khoản nguồn |
| `DestAccountKey` | INT (FK → DimAccount) | Khóa ngoại tài khoản đích |
| `AmountBandKey` | INT (FK → DimAmountBand) | Khóa ngoại chiều Khoảng Tiền |
| `StepRaw` | INT | Giá trị step gốc từ PaySim (1–744) |
| `Amount` | DECIMAL(18,2) | Số tiền giao dịch |
| `OldBalanceOrig` | DECIMAL(18,2) | Số dư trước (tài khoản nguồn) |
| `NewBalanceOrig` | DECIMAL(18,2) | Số dư sau (tài khoản nguồn) |
| `OldBalanceDest` | DECIMAL(18,2) | Số dư trước (tài khoản đích) |
| `NewBalanceDest` | DECIMAL(18,2) | Số dư sau (tài khoản đích) |
| `IsFraud` | BIT | Nhãn Ground Truth (từ PaySim) |
| `IsFlaggedFraud` | BIT | Cờ gốc PaySim (tham khảo) |
| `BalanceDropOrig` | DECIMAL(18,2) | `OldBalanceOrig - NewBalanceOrig` (Derived measure) |
| `LoadedAt` | DATETIME | Timestamp khi record được load vào DW |

#### FactModelScore — Kết quả Chấm điểm ML

> **Grain:** 1 dòng = 1 kết quả scoring của 1 model cho 1 giao dịch

| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `ScoreKey` | BIGINT (PK) | Surrogate key tự tăng |
| `TransactionKey` | BIGINT (FK → FactTransaction) | Khóa liên kết với FactTransaction |
| `ModelVersionKey` | INT (FK → DimModelVersion) | Mô hình được dùng để score |
| `RiskPolicyKey` | INT (FK → DimRiskPolicy) | Policy áp dụng tại thời điểm score |
| `DateKey` | INT (FK → DimDate) | Ngày score được tính |
| `FraudScore` | DECIMAL(7,6) | Xác suất gian lận [0.000000, 1.000000] |
| `RiskLevel` | VARCHAR(10) | LOW, MEDIUM, HIGH, CRITICAL |
| `RecommendedAction` | VARCHAR(30) | ALLOW, STEP_UP_VERIFY, HOLD_AND_REVIEW, BLOCK_AND_ALERT |
| `IsPredictedFraud` | BIT | 1 nếu FraudScore ≥ Threshold |
| `ScoredAt` | DATETIME | Timestamp chấm điểm |

#### FactAlert — Cảnh báo Gian lận

> **Grain:** 1 dòng = 1 cảnh báo được phát ra (chỉ cho HIGH và CRITICAL)

| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `AlertKey` | BIGINT (PK) | Surrogate key tự tăng |
| `TransactionKey` | BIGINT (FK → FactTransaction) | Giao dịch kích hoạt cảnh báo |
| `ScoreKey` | BIGINT (FK → FactModelScore) | Kết quả scoring liên quan |
| `RiskPolicyKey` | INT (FK → DimRiskPolicy) | Policy áp dụng |
| `DateKey` | INT (FK → DimDate) | Ngày phát sinh cảnh báo |
| `AlertLevel` | VARCHAR(10) | HIGH hoặc CRITICAL |
| `AlertStatus` | VARCHAR(15) | OPEN, IN_REVIEW, RESOLVED, FALSE_POSITIVE |
| `FraudScore` | DECIMAL(7,6) | Điểm fraud tại thời điểm cảnh báo |
| `AlertAmount` | DECIMAL(18,2) | Số tiền của giao dịch bị cảnh báo |
| `CreatedAt` | DATETIME | Timestamp tạo cảnh báo |
| `ResolvedAt` | DATETIME | Timestamp xử lý xong (NULL nếu chưa xử lý) |

---

## 5. Sơ đồ Star Schema

```
                    ┌──────────────┐
                    │  DimDate     │
                    │  (DateKey)   │
                    └──────┬───────┘
                           │
         ┌──────────┐      │      ┌──────────────────┐
         │ DimTime  │      │      │DimTransactionType│
         │(TimeKey) │      │      │(TypeKey)         │
         └────┬─────┘      │      └────────┬─────────┘
              │            │               │
         ┌────▼─────────────▼───────────────▼────────┐
         │              FactTransaction               │
         │  TransactionKey (PK)                       │
         │  DateKey, TimeKey, TransactionTypeKey      │
         │  OrigAccountKey, DestAccountKey            │
         │  AmountBandKey                             │
         │  Amount, OldBalanceOrig, NewBalanceOrig    │
         │  IsFraud, IsFlaggedFraud                   │
         └──────────────┬────────────────────────────┘
                        │ 1:N
         ┌──────────────▼────────────────────────────┐
         │              FactModelScore                │
         │  ScoreKey (PK)                             │
         │  TransactionKey (FK), ModelVersionKey (FK) │
         │  RiskPolicyKey (FK), DateKey (FK)          │
         │  FraudScore, RiskLevel, RecommendedAction  │
         └──────────────┬────────────────────────────┘
                        │ 1:1 (chỉ HIGH/CRITICAL)
         ┌──────────────▼────────────────────────────┐
         │              FactAlert                     │
         │  AlertKey (PK)                             │
         │  TransactionKey (FK), ScoreKey (FK)        │
         │  RiskPolicyKey (FK), DateKey (FK)          │
         │  AlertLevel, AlertStatus, FraudScore       │
         └───────────────────────────────────────────┘

Dimensions chung:
  DimAccount (AccountKey) ← OrigAccountKey, DestAccountKey
  DimAmountBand (AmountBandKey) ← AmountBandKey
  DimRiskPolicy (RiskPolicyKey) ← FactModelScore, FactAlert
  DimModelVersion (ModelVersionKey) ← FactModelScore
```

---

## 6. Mapping Business Questions → Bảng/View SQL

> **Bộ Views chuẩn hóa (5 views):** Toàn bộ dự án chỉ dùng đúng 5 tên view này. TV2 tạo trong `06_create_bi_views.sql`, TV5 dùng trong Power BI và Streamlit.

| Business Question | Fact Table | Dimension Tables | BI View |
|---|---|---|---|
| KPI-T01/T02: Tổng quan giao dịch | FactTransaction | DimDate, DimTransactionType | `vw_TransactionSummary` |
| BQ-01: Fraud theo loại GD | FactTransaction | DimTransactionType | `vw_FraudAnalysis` |
| BQ-02: Fraud theo thời gian | FactTransaction | DimDate, DimTime | `vw_FraudAnalysis` |
| BQ-03: Fraud theo khoảng tiền | FactTransaction | DimAmountBand | `vw_FraudAnalysis` |
| BQ-04: Pattern số dư bất thường | FactTransaction | DimAccount | `vw_FraudAnalysis` |
| BQ-05: Model Performance | FactModelScore | DimModelVersion | `vw_ModelPerformance` |
| BQ-06: Captured Fraud Loss | FactModelScore + FactTransaction | DimModelVersion | `vw_ModelPerformance` |
| BQ-07: Alert by Risk Level (HIGH/CRITICAL) | FactAlert | DimRiskPolicy | `vw_AlertSummary` |
| BQ-08: ETL Reconciliation | stg.raw_paysim + FactTransaction | — | `vw_ETLQuality` |

---

## 7. Lịch sử Thay đổi

| Phiên bản | Ngày | Người cập nhật | Nội dung thay đổi |
|-----------|------|----------------|-------------------|
| v1.0 | 2026-08-09 | TV1 | Khởi tạo Bus Matrix và Star Schema Design |
| v1.1 | 2026-08-09 | TV1 | Fix §2 Bus Matrix: bỏ ✅ sai trên FactModelScore/FactAlert; xoá aggregate columns khỏi DimAccount; clarify TimeSlot boundary; thêm TODO cho RiskWeight; thêm disclaimer dữ liệu mô phỏng |
| v1.2 | 2026-08-10 | TV1 | Fix M1: xóa tham chiếu sai đến decision_policy.md trong §2; Fix M2: đổi tên TimeSlot NIGHT [22,24) → LATE_NIGHT để tránh trùng tên gây lỗi INSERT vào DimTime |
| v1.3 | 2026-08-10 | TV1 | Fix P1-1: chuẩn hóa bộ tên BI Views §6 về 5 views thống nhất (vw_TransactionSummary, vw_FraudAnalysis, vw_ModelPerformance, vw_AlertSummary, vw_ETLQuality) — xóa bỏ các tên phân mảnh vw_FraudByType/Time/Amount, vw_BalanceAnalysis; sửa BQ-06 vào vw_ModelPerformance |
| v1.4 | 2026-08-10 | TV1 | Cập nhật BQ-07 §6: khẳng định chỉ phân tích cảnh báo HIGH và CRITICAL |
