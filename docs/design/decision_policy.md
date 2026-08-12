# Decision Policy — Chính sách Phân loại Rủi ro & Ra quyết định
# PaySim Fraud Detection Data Mart

---

## 1. Tổng quan

Tài liệu này định nghĩa **chính sách phân loại rủi ro** (Risk Decision Policy) cho Hệ thống Hỗ trợ Ra quyết định (DSS). Mỗi giao dịch sau khi được mô hình ML chấm điểm (`fraud_score`) sẽ được phân loại vào một mức rủi ro và nhận hành động khuyến nghị tương ứng.

> **Nguyên tắc thiết kế:**
> - Policy được đọc từ `configs/risk_policy.yaml` — **không hardcode** vào code Python hoặc SQL.
> - Thay đổi ngưỡng chỉ cần sửa YAML và reload; không cần deploy lại mô hình.
> - Policy version được lưu vào `DimRiskPolicy` để đảm bảo tính lần vết (auditability).

---

## 2. Ma trận Quyết định Rủi ro (Risk Decision Matrix)

| Risk Level | Fraud Score Range | Hành động Khuyến nghị | Ưu tiên Xử lý | Ý nghĩa Nghiệp vụ |
|---|---|---|---|---|
| 🟢 **LOW** | 0.00 – 0.30 | `ALLOW` | 4 (Thấp nhất) | Giao dịch có xác suất gian lận thấp — cho phép qua tự động |
| 🟡 **MEDIUM** | 0.30 – 0.60 | `STEP_UP_VERIFY` | 3 | Nghi ngờ vừa — yêu cầu xác thực thêm (OTP, xác nhận) |
| 🟠 **HIGH** | 0.60 – 0.85 | `HOLD_AND_REVIEW` | 2 | Nguy cơ cao — tạm giữ giao dịch, đội rủi ro xem xét thủ công |
| 🔴 **CRITICAL** | 0.85 – 1.00 | `BLOCK_AND_ALERT` | 1 (Cao nhất) | Nguy cơ cực cao — chặn giao dịch ngay & sinh cảnh báo khẩn |

---

## 3. Định nghĩa Chi tiết Từng Mức Rủi ro

### 🟢 LOW — Rủi ro Thấp
```
Fraud Score: [0.00, 0.30)
Action: ALLOW
Alert Generated: KHÔNG
Priority: 4
```
**Mô tả:** Mô hình đánh giá giao dịch này có xác suất gian lận dưới 30%. Giao dịch được phép tiến hành tự động mà không cần can thiệp thủ công. Không sinh cảnh báo trong `FactAlert`.

**Khi nào xảy ra:**
- Giao dịch PAYMENT nhỏ từ tài khoản hoạt động bình thường.
- Giao dịch CASH_IN (nạp tiền) — PaySim chưa ghi nhận loại này có gian lận.
- Giao dịch có pattern số dư nhất quán (oldbalance - amount ≈ newbalance).

---

### 🟡 MEDIUM — Rủi ro Trung bình
```
Fraud Score: [0.30, 0.60)
Action: STEP_UP_VERIFY
Alert Generated: TÙY CẤU HÌNH (mặc định: KHÔNG sinh FactAlert)
Priority: 3
```
**Mô tả:** Giao dịch có một số dấu hiệu đáng ngờ nhưng chưa đủ để chặn. Hệ thống yêu cầu xác thực bổ sung từ người dùng (ví dụ: xác nhận OTP, câu hỏi bảo mật) trước khi hoàn tất giao dịch.

**Khi nào xảy ra:**
- Giao dịch TRANSFER lớn bất thường so với lịch sử.
- Giao dịch đến tài khoản mới chưa từng giao dịch.
- Số dư sau giao dịch tiến gần về 0.

---

### 🟠 HIGH — Rủi ro Cao
```
Fraud Score: [0.60, 0.85)
Action: HOLD_AND_REVIEW
Alert Generated: CÓ (sinh record vào FactAlert với AlertLevel = 'HIGH')
Priority: 2
```
**Mô tả:** Giao dịch bị tạm giữ (HOLD) và chờ đội ngũ rủi ro xem xét thủ công. Một cảnh báo được sinh ra trong `FactAlert` với trạng thái `OPEN`. Sau khi xem xét, đội rủi ro cập nhật `AlertStatus` thành:
- `RESOLVED` — xác nhận là gian lận thực, đã xử lý xong.
- `FALSE_POSITIVE` — xác nhận giao dịch hợp lệ, cảnh báo nhầm.
- `IN_REVIEW` — đang được xem xét, chưa có kết luận.

**Khi nào xảy ra:**
- Giao dịch TRANSFER lớn với `newbalanceOrig = 0` (tài khoản bị rút sạch).
- Giao dịch từ tài khoản đã có lịch sử bị flag.
- Pattern số dư nguồn và đích bất nhất (balance discrepancy).

---

### 🔴 CRITICAL — Rủi ro Cực cao
```
Fraud Score: [0.85, 1.00]
Action: BLOCK_AND_ALERT
Alert Generated: CÓ (sinh record vào FactAlert với AlertLevel = 'CRITICAL')
Priority: 1
```
**Mô tả:** Giao dịch bị chặn ngay lập tức. Cảnh báo khẩn được sinh ra với mức ưu tiên cao nhất và hiển thị nổi bật trên Streamlit Alert Queue. Đội rủi ro được thông báo để xử lý ưu tiên.

**Khi nào xảy ra:**
- Giao dịch có fraud_score ≥ 0.85 — mô hình tin tưởng rất cao đây là gian lận.
- Thường là TRANSFER hoặc CASH_OUT số tiền lớn với `newbalanceOrig ≈ 0`.
- Tài khoản đích là merchant (M...) nhưng nhận TRANSFER (bất thường).

---

## 4. Cấu trúc File YAML (configs/risk_policy.yaml)

File cấu hình ánh xạ 1:1 với tài liệu này. Thay đổi ngưỡng chỉ cần sửa file YAML:

```yaml
# configs/risk_policy.yaml
# PaySim Fraud Detection Data Mart — Risk Decision Policy
# Version: v1.0
# Last Updated: 2026-08-09
# Owner: TV1 (BA/Lead) + TV4 (ML Engineer)

policy_version: "v1.0"
effective_date: "2026-08-09"

# QUY ƯỚC RANH GIỚI (Boundary Rule):
#   score_min ≤ fraud_score < score_max  → áp dụng cho LOW, MEDIUM, HIGH
#   Riêng CRITICAL: score_min ≤ fraud_score ≤ 1.00  → inclusive cả 2 đầu
#   Ví dụ: score = 0.30 → thuộc MEDIUM (không phải LOW)
#          score = 0.60 → thuộc HIGH (không phải MEDIUM)
#          score = 0.85 → thuộc CRITICAL (không phải HIGH)
risk_levels:
  - level: "LOW"
    score_min: 0.00        # ≥ 0.00 (inclusive)
    score_max: 0.30        # < 0.30 (exclusive)
    action: "ALLOW"
    generate_alert: false
    priority: 4
    description: "Giao dịch có rủi ro thấp, cho phép tự động"

  - level: "MEDIUM"
    score_min: 0.30        # ≥ 0.30 (inclusive)
    score_max: 0.60        # < 0.60 (exclusive)
    action: "STEP_UP_VERIFY"
    generate_alert: false
    priority: 3
    description: "Nghi ngờ vừa, yêu cầu xác thực thêm"

  - level: "HIGH"
    score_min: 0.60        # ≥ 0.60 (inclusive)
    score_max: 0.85        # < 0.85 (exclusive)
    action: "HOLD_AND_REVIEW"
    generate_alert: true
    alert_level: "HIGH"
    priority: 2
    description: "Rủi ro cao, tạm giữ và xem xét thủ công"

  - level: "CRITICAL"
    score_min: 0.85        # ≥ 0.85 (inclusive)
    score_max: 1.00        # ≤ 1.00 (inclusive — bao gồm cả điểm 1.00)
    action: "BLOCK_AND_ALERT"
    generate_alert: true
    alert_level: "CRITICAL"
    priority: 1
    description: "Rủi ro cực cao, chặn ngay và cảnh báo khẩn"

# Ngưỡng mặc định cho binary classification (IsPredictedFraud = 1 nếu score ≥ threshold)
# Được tối ưu bởi TV4 (ML Engineer) dựa trên Precision-Recall Curve
# TODO: TV4 cập nhật giá trị sau khi chạy select_threshold.py
default_classification_threshold: 0.50
```

> **Lưu ý quan trọng:** Ngưỡng `default_classification_threshold` (0.50) là giá trị tạm thời.
> TV4 (ML Engineer) sẽ cập nhật giá trị chính xác sau khi thực hiện **Threshold Tuning** dựa trên Precision-Recall Curve của mô hình thực tế.

---

## 5. Luồng Xử lý Quyết định (Decision Flow)

```
Giao dịch mới
      │
      ▼
[Feature Engineering]
  (build_features.py)
      │
      ▼
[ML Model Scoring]
  fraud_score ∈ [0.0, 1.0]
      │
      ▼
[Risk Policy Engine]
  Đọc configs/risk_policy.yaml
      │
      ├─► fraud_score < 0.30   → risk_level = LOW      → action = ALLOW
      │                                                  → KHÔNG sinh Alert
      │
      ├─► 0.30 ≤ score < 0.60  → risk_level = MEDIUM   → action = STEP_UP_VERIFY
      │                                                  → KHÔNG sinh Alert
      │
      ├─► 0.60 ≤ score < 0.85  → risk_level = HIGH     → action = HOLD_AND_REVIEW
      │                                                  → Sinh FactAlert (HIGH)
      │
      └─► score ≥ 0.85         → risk_level = CRITICAL  → action = BLOCK_AND_ALERT
                                                         → Sinh FactAlert (CRITICAL)
                                                         → Hiển thị trên Alert Queue
      │
      ▼
[Lưu vào FactModelScore]
  fraud_score, risk_level, recommended_action, scored_at
      │
      ▼ (nếu generate_alert = true)
[Lưu vào FactAlert]
  alert_level, alert_status = 'OPEN', created_at
```

---

## 6. Giải thích Căn cứ Chọn Ngưỡng

| Quyết định | Căn cứ |
|-----------|--------|
| **LOW < 0.30** | Ngưỡng loại bỏ noise — dưới 30% mô hình gần như chắc chắn đây không phải fraud |
| **MEDIUM 0.30–0.60** | Vùng không chắc chắn — xác minh thêm giảm rủi ro mà không ảnh hưởng nhiều trải nghiệm |
| **HIGH 0.60–0.85** | Rủi ro đáng kể — cần review thủ công nhưng chưa đủ cơ sở để chặn hoàn toàn |
| **CRITICAL ≥ 0.85** | Mô hình rất tự tin đây là fraud — chặn ngay để bảo vệ tài sản |
| **Ngưỡng ưu tiên Recall** | Trong fraud detection, bỏ sót (FN) nguy hiểm hơn cảnh báo nhầm (FP) → ngưỡng CRITICAL đặt ở 0.85 (không quá cao) để không bỏ lọt |

> **Sau threshold tuning:** TV4 có thể đề xuất điều chỉnh các ngưỡng trên dựa trên kết quả Precision-Recall Curve thực tế của mô hình. TV1 sẽ cập nhật tài liệu và YAML tương ứng.

---

## 7. Phiên bản & Kiểm soát Thay đổi Policy

| PolicyVersion | Ngày Hiệu lực | Người cập nhật | Thay đổi chính |
|---|---|---|---|
| v1.0 | 2026-08-09 | TV1 | Phiên bản khởi tạo dựa trên best practices ngành |

> Mỗi khi thay đổi ngưỡng, phải:
> 1. Cập nhật `policy_version` trong `configs/risk_policy.yaml`.
> 2. Chạy lại `07_seed_dimensions.sql` để thêm record mới vào `DimRiskPolicy`.
> 3. Cập nhật tài liệu này.
> 4. Commit với message: `docs: update risk policy to vX.Y`.

---

## 8. Lịch sử Thay đổi Tài liệu

| Phiên bản | Ngày | Người cập nhật | Nội dung thay đổi |
|-----------|------|----------------|-------------------|
| v1.0 | 2026-08-09 | TV1 | Khởi tạo Decision Policy |
| v1.1 | 2026-08-10 | TV1 | Fix P1-5a: thay thế "APPROVE/REJECT" bằng các giá trị `AlertStatus` đúng (RESOLVED, FALSE_POSITIVE, IN_REVIEW); Fix P1-5b: thêm Boundary Rule rõ ràng vào YAML snippet §4 ([inclusive min, exclusive max]) |
| v1.2 | 2026-08-10 | TV1 | Fix P1-6: đồng bộ snippet YAML §4 với `configs/risk_policy.yaml` thực tế (thêm `alert_level` cho HIGH/CRITICAL, bổ sung ví dụ boundary) |
