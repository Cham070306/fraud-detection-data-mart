# KPI Dictionary
# PaySim Fraud Detection Data Mart

---

## Giới thiệu

Tài liệu này định nghĩa **từ điển các chỉ số KPI** (Key Performance Indicators) của hệ thống Fraud Detection Data Mart. Mỗi KPI được mô tả đầy đủ gồm: định nghĩa nghiệp vụ, công thức toán học, nguồn bảng/view, bộ lọc áp dụng và người kiểm chứng.

> **Quy tắc đặt tên KPI:** Mọi KPI phải có thể tính được từ SQL query trên Data Mart. Không được dùng dữ liệu ngoài Data Mart để tính KPI (phải đi qua BI Views).

---

## Nhóm 1: KPI Giao dịch (Transaction KPIs)

### KPI-T01 — Total Transaction Volume

| Mục | Chi tiết |
|-----|---------|
| **Tên đầy đủ** | Tổng số lượng giao dịch |
| **Mô tả** | Tổng số giao dịch được ghi nhận trong hệ thống trong khoảng thời gian xác định |
| **Công thức** | `COUNT(TransactionKey)` |
| **Đơn vị** | Số giao dịch |
| **Nguồn** | `fact.FactTransaction` |
| **Bộ lọc** | Có thể lọc theo `DimDate`, `DimTransactionType` |
| **View SQL** | `vw_TransactionSummary` |
| **Người kiểm chứng** | TV2 (Data Engineer), TV3 (Analyst) |

---

### KPI-T02 — Total Transaction Amount

| Mục | Chi tiết |
|-----|---------|
| **Tên đầy đủ** | Tổng giá trị giao dịch |
| **Mô tả** | Tổng số tiền của tất cả giao dịch trong khoảng thời gian xác định |
| **Công thức** | `SUM(amount)` |
| **Đơn vị** | Đơn vị tiền tệ (PaySim) |
| **Nguồn** | `fact.FactTransaction` |
| **Bộ lọc** | Lọc theo `DimDate`, `DimTransactionType`, `DimAmountBand` |
| **View SQL** | `vw_TransactionSummary` |
| **Người kiểm chứng** | TV2, TV3 |

---

### KPI-T03 — Fraud Transaction Volume

| Mục | Chi tiết |
|-----|---------|
| **Tên đầy đủ** | Số lượng giao dịch gian lận |
| **Mô tả** | Tổng số giao dịch được nhãn `isFraud = 1` trong dữ liệu gốc (Ground Truth) |
| **Công thức** | `COUNT(TransactionKey) WHERE is_fraud = 1` |
| **Đơn vị** | Số giao dịch |
| **Nguồn** | `fact.FactTransaction` |
| **Bộ lọc** | `is_fraud = 1` |
| **View SQL** | `vw_FraudAnalysis` |
| **Người kiểm chứng** | TV3, TV4 |
| **Giá trị kỳ vọng** | 8.213 giao dịch (toàn bộ dataset) |

---

### KPI-T04 — Fraud Amount

| Mục | Chi tiết |
|-----|---------|
| **Tên đầy đủ** | Tổng giá trị giao dịch gian lận |
| **Mô tả** | Tổng số tiền liên quan đến các giao dịch gian lận (Ground Truth) |
| **Công thức** | `SUM(amount) WHERE is_fraud = 1` |
| **Đơn vị** | Đơn vị tiền tệ (PaySim) |
| **Nguồn** | `fact.FactTransaction` |
| **Bộ lọc** | `is_fraud = 1` |
| **View SQL** | `vw_FraudAnalysis` |
| **Người kiểm chứng** | TV3, TV4 |

---

### KPI-T05 — Fraud Rate (by Volume)

| Mục | Chi tiết |
|-----|---------|
| **Tên đầy đủ** | Tỷ lệ gian lận theo số lượng giao dịch |
| **Mô tả** | Phần trăm giao dịch gian lận trên tổng số giao dịch |
| **Công thức** | `COUNT(is_fraud=1) / COUNT(*) × 100` |
| **Đơn vị** | % |
| **Nguồn** | `fact.FactTransaction` |
| **Bộ lọc** | Có thể nhóm theo `DimTransactionType`, `DimAmountBand`, `DimDate` |
| **View SQL** | `vw_FraudAnalysis` |
| **Người kiểm chứng** | TV3 |
| **Giá trị kỳ vọng** | ~0.13% (toàn bộ dataset) |

---

### KPI-T06 — Fraud Rate by Amount

| Mục | Chi tiết |
|-----|---------|
| **Tên đầy đủ** | Tỷ lệ gian lận theo giá trị tiền |
| **Mô tả** | Phần trăm tổng số tiền gian lận trên tổng số tiền giao dịch |
| **Công thức** | `SUM(amount WHERE is_fraud=1) / SUM(amount) × 100` |
| **Đơn vị** | % |
| **Nguồn** | `fact.FactTransaction` |
| **Bộ lọc** | Theo `DimTransactionType` |
| **View SQL** | `vw_FraudAnalysis` |
| **Người kiểm chứng** | TV3 |

---

## Nhóm 2: KPI Mô hình ML (Model Performance KPIs)

> **Ghi chú:** Các KPI này chỉ tính trên tập test (holdout set). Không tính trên toàn bộ dataset.

### KPI-M01 — Precision

| Mục | Chi tiết |
|-----|---------|
| **Tên đầy đủ** | Độ chính xác của mô hình |
| **Mô tả** | Trong số giao dịch mô hình dự đoán là Fraud, bao nhiêu phần trăm thực sự là Fraud |
| **Công thức** | `TP / (TP + FP)` |
| **Đơn vị** | Tỷ lệ [0, 1] hoặc % |
| **Nguồn** | `fact.FactModelScore` JOIN `fact.FactTransaction` |
| **View SQL** | `vw_ModelPerformance` |
| **Người kiểm chứng** | TV4 |
| **Mục tiêu** | Tham khảo; không phải chỉ số chính (ưu tiên Recall hơn) |

---

### KPI-M02 — Recall (Sensitivity)

| Mục | Chi tiết |
|-----|---------|
| **Tên đầy đủ** | Độ nhạy / Tỷ lệ phát hiện gian lận |
| **Mô tả** | Trong số giao dịch thực sự là Fraud, mô hình phát hiện được bao nhiêu phần trăm |
| **Công thức** | `TP / (TP + FN)` |
| **Đơn vị** | Tỷ lệ [0, 1] hoặc % |
| **Nguồn** | `fact.FactModelScore` JOIN `fact.FactTransaction` |
| **View SQL** | `vw_ModelPerformance` |
| **Người kiểm chứng** | TV4 |
| **Mục tiêu** | ≥ **0.80** (80%) — chỉ số quan trọng nhất |

---

### KPI-M03 — F2-Score

| Mục | Chi tiết |
|-----|---------|
| **Tên đầy đủ** | F2-Score (ưu tiên Recall gấp đôi Precision) |
| **Mô tả** | Trung bình điều hòa có trọng số của Precision và Recall, với Recall được ưu tiên gấp đôi (β=2) |
| **Công thức** | `(1 + 2²) × Precision × Recall / (2² × Precision + Recall)` = `5 × P × R / (4P + R)` |
| **Đơn vị** | Tỷ lệ [0, 1] |
| **Nguồn** | `fact.FactModelScore` JOIN `fact.FactTransaction` |
| **View SQL** | `vw_ModelPerformance` |
| **Người kiểm chứng** | TV4 |
| **Mục tiêu** | ≥ **0.70** |
| **Lý do dùng F2** | Trong fraud detection, bỏ sót gian lận (FN) nguy hiểm hơn nhiều so với cảnh báo nhầm (FP) |

---

### KPI-M04 — PR-AUC (Area Under Precision-Recall Curve)

| Mục | Chi tiết |
|-----|---------|
| **Tên đầy đủ** | Diện tích dưới đường cong Precision-Recall |
| **Mô tả** | Đo lường hiệu quả tổng thể của mô hình trên dataset mất cân bằng nhãn (tốt hơn ROC-AUC cho trường hợp này) |
| **Công thức** | `∫ Precision dRecall` (tích phân theo các ngưỡng threshold) |
| **Đơn vị** | [0, 1] |
| **Nguồn** | `fact.FactModelScore` JOIN `fact.FactTransaction` |
| **View SQL** | `vw_ModelPerformance` |
| **Người kiểm chứng** | TV4 |
| **Mục tiêu** | > 0.60 (dataset mất cân bằng; baseline ngẫu nhiên ≈ 0.0013) |
| **Lý do dùng PR-AUC** | ROC-AUC bị nhiễu bởi True Negative (99.87% dataset) — PR-AUC phản ánh thực chất hơn |

---

### KPI-M05 — Confusion Matrix Components

| Component | Định nghĩa | Ý nghĩa Nghiệp vụ |
|-----------|-----------|-------------------|
| **TP (True Positive)** | Fraud thực tế, mô hình dự đoán đúng là Fraud | Giao dịch gian lận bị chặn thành công |
| **FP (False Positive)** | Hợp lệ thực tế, mô hình dự đoán nhầm là Fraud | Giao dịch hợp lệ bị chặn oan — ảnh hưởng trải nghiệm khách hàng |
| **TN (True Negative)** | Hợp lệ thực tế, mô hình dự đoán đúng là hợp lệ | Giao dịch bình thường qua suôn sẻ |
| **FN (False Negative)** | Fraud thực tế, mô hình bỏ qua | Giao dịch gian lận lọt qua — **rủi ro cao nhất** |

---

## Nhóm 3: KPI Tài chính & Vận hành Alert (Alert & Financial KPIs)

### KPI-A01 — Captured Fraud Loss Rate

| Mục | Chi tiết |
|-----|---------|
| **Tên đầy đủ** | Tỷ lệ thiệt hại gian lận được phát hiện |
| **Mô tả** | Phần trăm tổng giá trị giao dịch gian lận mà mô hình đã phát hiện và cảnh báo (dựa trên TP) so với tổng thiệt hại thực tế |
| **Công thức** | `SUM(amount WHERE is_fraud=1 AND model_predicted=1) / SUM(amount WHERE is_fraud=1) × 100` |
| **Đơn vị** | % |
| **Nguồn** | `fact.FactModelScore` JOIN `fact.FactTransaction` |
| **View SQL** | `vw_ModelPerformance` |
| **Người kiểm chứng** | TV4, TV5 |
| **Mục tiêu** | Tối đa hóa (phụ thuộc vào Recall) |

---

### KPI-A02 — Alert Count by Risk Level

| Mục | Chi tiết |
|-----|---------|
| **Tên đầy đủ** | Số lượng cảnh báo theo mức độ rủi ro |
| **Mô tả** | Phân bố số lượng cảnh báo theo **2 mức được lưu trong `FactAlert`**: HIGH và CRITICAL. (LOW và MEDIUM không sinh cảnh báo — xem `FR-DSS-01` và `Decision Policy`) |
| **Công thức** | `COUNT(AlertKey) GROUP BY alert_level` — kết quả luôn có tối đa 2 nhóm: `HIGH` và `CRITICAL` |
| **Đơn vị** | Số cảnh báo |
| **Nguồn** | `fact.FactAlert` JOIN `dim.DimRiskPolicy` |
| **View SQL** | `vw_AlertSummary` |
| **Người kiểm chứng** | TV5 |

---

### KPI-A03 — False Positive Rate per Risk Level

| Mục | Chi tiết |
|-----|---------|
| **Tên đầy đủ** | Tỷ lệ cảnh báo nhầm theo mức rủi ro |
| **Mô tả** | Trong số giao dịch được cảnh báo ở từng mức rủi ro, bao nhiêu phần trăm thực tế là hợp lệ (không gian lận) |
| **Công thức** | `COUNT(AlertKey WHERE is_fraud=0) / COUNT(AlertKey) × 100` — nhóm theo `risk_level` |
| **Đơn vị** | % |
| **Nguồn** | `fact.FactAlert` JOIN `fact.FactTransaction` JOIN `dim.DimRiskPolicy` |
| **View SQL** | `vw_AlertSummary` |
| **Người kiểm chứng** | TV5 |

---

## Nhóm 4: KPI Chất lượng ETL (Data Quality KPIs)

### KPI-Q01 — ETL Reconciliation Rate

| Mục | Chi tiết |
|-----|---------|
| **Tên đầy đủ** | Tỷ lệ đối soát dữ liệu ETL |
| **Mô tả** | Phần trăm dòng dữ liệu từ Staging được load thành công vào Fact (không mất dòng) |
| **Công thức** | `(COUNT(FactTransaction) + COUNT(rejected_rows)) / COUNT(stg.raw_paysim) × 100` |
| **Đơn vị** | % |
| **Nguồn** | `stg.raw_paysim`, `fact.FactTransaction` |
| **View SQL** | `vw_ETLQuality` |
| **Mục tiêu** | = **100%** (không được mất dòng) |
| **Người kiểm chứng** | TV2 |

---

### KPI-Q02 — Data Validation Error Rate

| Mục | Chi tiết |
|-----|---------|
| **Tên đầy đủ** | Tỷ lệ lỗi validation dữ liệu |
| **Mô tả** | Phần trăm dòng dữ liệu bị từ chối trong bước Validate (amount < 0, kiểu dữ liệu sai...) |
| **Công thức** | `COUNT(rejected_rows) / COUNT(total_rows) × 100` |
| **Đơn vị** | % |
| **Nguồn** | ETL Log (`src/etl/validate.py`) |
| **View SQL** | `vw_ETLQuality` |
| **Mục tiêu** | < 0.1% |
| **Người kiểm chứng** | TV2 |

---

## Bảng Tổng hợp KPI

| ID | Tên KPI | Mục tiêu | Chủ sở hữu |
|----|---------|----------|------------|
| KPI-T01 | Total Transaction Volume | Phân tích | TV2, TV3 |
| KPI-T02 | Total Transaction Amount | Phân tích | TV2, TV3 |
| KPI-T03 | Fraud Transaction Volume | 8.213 giao dịch | TV3, TV4 |
| KPI-T04 | Fraud Amount | Phân tích | TV3, TV4 |
| KPI-T05 | Fraud Rate (Volume) | ~0.13% | TV3 |
| KPI-T06 | Fraud Rate (Amount) | Phân tích | TV3 |
| KPI-M01 | Precision | Tham khảo | TV4 |
| KPI-M02 | Recall | ≥ 80% | TV4 |
| KPI-M03 | F2-Score | ≥ 0.70 | TV4 |
| KPI-M04 | PR-AUC | > 0.60 | TV4 |
| KPI-A01 | Captured Fraud Loss Rate | Tối đa | TV4, TV5 |
| KPI-A02 | Alert Count by Risk Level | Phân tích | TV5 |
| KPI-A03 | False Positive Rate per Level | Tối thiểu | TV5 |
| KPI-Q01 | ETL Reconciliation Rate | = 100% | TV2 |
| KPI-Q02 | Data Validation Error Rate | < 0.1% | TV2 |

---

## Lịch sử Thay đổi

| Phiên bản | Ngày | Người cập nhật | Nội dung thay đổi |
|-----------|------|----------------|-------------------|
| v1.0 | 2026-08-09 | TV1 | Khởi tạo KPI Dictionary |
| v1.1 | 2026-08-10 | TV1 | Fix P1-1: chuẩn hóa View SQL — KPI-A01 đổi sang `vw_ModelPerformance`; thêm `View SQL: vw_ETLQuality` vào KPI-Q01/Q02; sửa công thức KPI-Q01 xử lý rejected rows |
| v1.2 | 2026-08-10 | TV1 | Fix P1-2: KPI-A02 sửa mô tả từ "4 mức" → "2 mức (HIGH, CRITICAL)"; sửa công thức GROUP BY alert_level thay vì risk_level |
