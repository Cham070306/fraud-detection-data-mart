# Bàn giao ML cho Power BI

## Trạng thái bàn giao

Model candidate `1.0.0` đã có feature pipeline, huấn luyện, đánh giá, threshold, scoring và risk mapping. Bộ CSV nhỏ trong `docs/integration/bi_model_handoff/` là dữ liệu tham chiếu đã version hóa để dựng trang **Model Performance** trước khi SQL Server sẵn sàng.

Không dùng các CSV tham chiếu này thay cho dữ liệu giao dịch. Dữ liệu vận hành của dashboard phải đọc từ các BI view hoặc bảng fact do Data Engineer cung cấp.

## File dành cho Hiệp

| File | Grain | Dùng cho visual |
|---|---|---|
| `model_performance.csv` | Một dòng cho mỗi ModelVersion và DatasetSplit | KPI cards PR-AUC, Precision, Recall, F2, threshold, alerts/1.000 và fraud amount captured |
| `confusion_matrix.csv` | Một ô confusion matrix cho mỗi dòng | Ma trận TN/FP/FN/TP trên test set |
| `risk_policy.csv` | Một RiskLevel cho mỗi dòng | Bảng chú giải LOW/MEDIUM/HIGH/CRITICAL, hành động và ưu tiên |

Nguồn tạo file:

```powershell
python scripts/build_bi_handoff.py
```

## Hợp đồng dữ liệu scoring

`scripts/score_transactions.py` tạo một dòng cho mỗi `(TransactionKey, ModelVersion)` với các cột:

- `TransactionKey`, `DateKey`, `TimeKey`, `TransactionType`, `Amount`
- `FraudScore`, `PredictedFraud`, `RiskLevel`, `CreateAlert`
- `AlertLevel`, `AlertStatus`, `RecommendedAction`
- `ModelVersion`, `PolicyVersion`, `ScoredAt`

Hiệp nên kết nối Power BI với các nguồn SQL sau khi Khải hoàn thành load:

- `bi.vw_ModelPerformance`: KPI model theo `ModelVersion`.
- `bi.vw_AlertQueue`: hàng đợi HIGH/CRITICAL, ưu tiên `CRITICAL` trước `HIGH`.
- `bi.vw_TransactionAnalysis`: chi tiết giao dịch và drill-through bằng `TransactionKey`.
- `bi.vw_ETLQuality`: chất lượng batch và reconciliation.

## Quy tắc dashboard

- Chỉ hiển thị KPI test khi `DatasetSplit = TEST`; validation dùng để giải thích việc chọn threshold.
- Hiển thị tỷ lệ dưới dạng phần trăm nhưng giữ giá trị nguồn trong khoảng 0–1.
- `step` là thời gian mô phỏng, không phải ngày lịch thực tế.
- Không diễn giải metric gần 100% như hiệu năng ngân hàng thực; PaySim là dữ liệu tổng hợp và có pattern số dư dễ phân tách.
- Alert Queue chỉ chứa `CreateAlert = true`, tương ứng HIGH hoặc CRITICAL theo policy `1.0.0`.

## Tiêu chí nghiệm thu với Hiệp

- Model Performance hiển thị đúng model `1.0.0`, threshold `0.32` và các metric test.
- Confusion matrix trả TN 88.213, FP 1, FN 1, TP 1.251.
- RiskLevel và RecommendedAction khớp `configs/risk_policy.yaml`.
- Khi nguồn SQL sẵn sàng, tổng score phải là 6.362.620 và HIGH + CRITICAL alert là 8.218.
- Drill-through giữ nguyên `TransactionKey`; không join bằng số thứ tự hiển thị.

## Phần phụ thuộc Data Engineer

Việc load `FactModelScore` và `FactAlert`, FK, idempotency, batch control và reconciliation trong SQL Server do Hoàng và Khải kiểm tra chung. Chi tiết nằm trong `docs/integration/sql-handoff.md`.
