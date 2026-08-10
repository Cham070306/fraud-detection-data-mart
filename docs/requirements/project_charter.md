# Project Charter
# PaySim Fraud Detection Data Mart (Đồ án môn Data Warehouse)

---

## 1. Thông tin Dự án

| Mục                    | Nội dung                                                                 |
|------------------------|--------------------------------------------------------------------------|
| **Tên dự án**          | PaySim Fraud Detection Data Mart                                         |
| **Môn học**            | Data Warehouse                                                           |
| **Dataset**            | PaySim Synthetic Financial Dataset (Kaggle)                              |
| **Phương pháp thiết kế** | Kimball Bottom-Up Data Mart (Star Schema)                              |
| **Ngôn ngữ / Công nghệ** | Python 3.11+, SQL Server 2019+, Power BI, Streamlit, scikit-learn / LightGBM |
| **Ngày khởi động**     | 2026-08                                                                  |
| **Trạng thái**         | Đang triển khai                                                          |

---

## 2. Thành viên Nhóm & Phân công

| Vai trò | Họ tên | Nhiệm vụ chính |
|---------|--------|----------------|
| **TV1 – BA / Trưởng nhóm** | *(Cập nhật sau)* | Tài liệu yêu cầu, Bus Matrix, KPI Dict, Decision Policy, README, Báo cáo tổng hợp |
| **TV2 – Data Engineer** | *(Cập nhật sau)* | Thiết kế Star Schema SQL Server, pipeline ETL (Staging → Data Mart), Reconciliation |
| **TV3 – Data Analyst** | *(Cập nhật sau)* | Data Profiling, EDA phân tích gian lận, Data Dictionary |
| **TV4 – ML Engineer** | *(Cập nhật sau)* | Feature Engineering, huấn luyện mô hình, tối ưu ngưỡng (Threshold Tuning), Scoring |
| **TV5 – BI / App Dev** | *(Cập nhật sau)* | Power BI (5 trang báo cáo), Streamlit Alert Queue App |

> **Ghi chú:** Tên thật các thành viên sẽ được cập nhật khi nhóm cung cấp.

---

## 3. Bối cảnh & Vấn đề Kinh doanh

### 3.1 Bối cảnh
Gian lận giao dịch tài chính (Financial Transaction Fraud) là vấn đề nghiêm trọng trong lĩnh vực ngân hàng và ví điện tử. Tổ chức thiếu hệ thống giám sát tập trung dễ dẫn đến:
- Không phát hiện kịp thời các giao dịch bất thường.
- Thiếu dữ liệu lịch sử để phân tích pattern gian lận.
- Không có cơ chế cảnh báo tự động cho đội ngũ rủi ro.

### 3.2 Vấn đề cụ thể
Dataset PaySim mô phỏng **6.362.620 giao dịch** trong 30 ngày với **8.213 giao dịch gian lận** (tỷ lệ gian lận ~0.13% — mất cân bằng nhãn nghiêm trọng). Hệ thống cần:
1. Lưu trữ và tổ chức dữ liệu theo mô hình Data Mart chuẩn Kimball.
2. Xây dựng chỉ số KPI đo lường hiệu quả phòng chống gian lận.
3. Tích hợp mô hình ML để tự động chấm điểm rủi ro từng giao dịch.
4. Sinh cảnh báo tự động và hỗ trợ ra quyết định (DSS).

---

## 4. Mục tiêu Dự án (Objectives)

| Mục tiêu | Tiêu chí đo lường |
|----------|-------------------|
| Xây dựng Data Mart Star Schema trên SQL Server | 3 bảng Fact + 7 bảng Dimension đầy đủ constraints & indexes |
| Pipeline ETL ổn định, không mất dữ liệu | Reconciliation: Row count Staging = Row count Fact ± 0 |
| Mô hình ML phát hiện gian lận | F2-Score ≥ 0.70, Recall ≥ 0.80 trên tập test |
| Dashboard trực quan hóa KPI | Power BI: 5 trang báo cáo được tích hợp dữ liệu thực |
| Hệ thống cảnh báo tự động | Streamlit Alert Queue: hiển thị giao dịch HIGH/CRITICAL trong < 5 giây |

---

## 5. Phạm vi Dự án (Scope)

### 5.1 Trong phạm vi (In Scope)
- [x] Data Mart Star Schema (SQL Server): Staging, Dimensions, Facts, BI Views.
- [x] ETL Pipeline: Extract từ CSV, Transform/Validate, Load theo chunk.
- [x] Data Quality & Reconciliation.
- [x] Feature Engineering từ dữ liệu giao dịch PaySim.
- [x] Huấn luyện & tối ưu ngưỡng mô hình ML (LightGBM/Random Forest).
- [x] Scoring giao dịch và phân loại rủi ro theo policy.
- [x] Power BI Dashboard (5 trang: Overview, Transaction Analysis, Model Performance, Alert Queue, ETL Quality).
- [x] Streamlit Alert Queue Application.
- [x] Tài liệu đầy đủ (7 file bàn giao của TV1).

### 5.2 Ngoài phạm vi (Out of Scope)
- [ ] Kết nối hệ thống ngân hàng thực tế (Production integration).
- [ ] Real-time streaming (Kafka, Flink); dự án xử lý batch.
- [ ] Mobile application.
- [ ] Triển khai cloud (AWS/Azure/GCP).

---

## 6. Phân tích Stakeholders

| Stakeholder | Vai trò trong dự án | Quan tâm chính |
|-------------|---------------------|----------------|
| **Giảng viên hướng dẫn** | Người đánh giá & phản hồi | Đúng phương pháp Kimball, tài liệu đầy đủ, code hoạt động |
| **Risk Analyst** (mô phỏng) | Người dùng cuối Dashboard & Alert | Fraud Rate, Alert Queue, Recommended Action |
| **Data Engineer** (TV2) | Xây dựng & vận hành ETL | Schema design, Data quality, Reconciliation |
| **ML Engineer** (TV4) | Xây dựng mô hình & Scoring | Feature Store, Model Metrics, Threshold Policy |
| **BI Developer** (TV5) | Xây dựng Dashboard | KPI definitions, View names, Data freshness |
| **Nhóm sinh viên** | Chủ dự án | Hoàn thành đồ án đúng hạn, đạt điểm cao |

---

## 7. Kiến trúc Tổng thể (High-Level Architecture)

```
CSV (PaySim.csv)
      │
      ▼
[STAGING Layer]         ← SQL Server: stg.raw_paysim
      │ ETL Transform + Validate
      ▼
[DIMENSION Tables]      ← dim.DimDate, DimTime, DimTransactionType,
      │                    DimAccount, DimAmountBand, DimRiskPolicy, DimModelVersion
      ▼
[FACT Tables]           ← fact.FactTransaction, FactModelScore, FactAlert
      │
      ├──► [BI VIEWS]          ← vw.TransactionSummary, FraudAnalysis, ModelPerf...
      │         │
      │         ├──► Power BI Dashboard (5 pages)
      │         └──► Streamlit Alert Queue App
      │
      └──► [ML PIPELINE]
                │  Feature Engineering → Train → Evaluate → Score
                └──► Fact_ModelScore (fraud_score, risk_level, recommended_action)
```

---

## 8. Rủi ro & Kế hoạch Giảm thiểu

| Rủi ro | Xác suất | Tác động | Kế hoạch giảm thiểu |
|--------|----------|----------|---------------------|
| Dataset mất cân bằng nhãn (99.87% / 0.13%) | Cao | Cao | Dùng SMOTE hoặc class_weight; tối ưu Recall thay vì Accuracy |
| SQL Server không cài đặt được | Thấp | Cao | Fallback sang SQLite cho môi trường dev |
| Thành viên chưa quen Kimball | Trung bình | Trung bình | Tài liệu hóa chi tiết Bus Matrix; weekly sync |
| File PaySim.csv (~493MB) quá lớn | Thấp | Trung bình | Đọc theo chunk (chunksize=50000); không push lên Git |

---

## 9. Tiêu chí Hoàn thành (Definition of Done)

### Toàn dự án hoàn thành khi:
- [ ] Tất cả 7 file tài liệu TV1 được commit lên nhánh `main`.
- [ ] SQL DDL chạy thành công từ `00_create_database.sql` đến `08_validation_queries.sql`.
- [ ] ETL pipeline xử lý toàn bộ 6.362.620 dòng, Reconciliation pass.
- [ ] Mô hình ML đạt F2 ≥ 0.70, Recall ≥ 0.80.
- [ ] Power BI Dashboard 5 trang kết nối SQL Server thành công.
- [ ] Streamlit Alert Queue App khởi động và hiển thị dữ liệu thực.
- [ ] README.md hướng dẫn đủ để người mới chạy được toàn bộ pipeline từ đầu.

---

## 10. Lịch sử Thay đổi

| Phiên bản | Ngày | Người cập nhật | Nội dung thay đổi |
|-----------|------|----------------|-------------------|
| v1.0 | 2026-08-09 | TV1 | Khởi tạo Project Charter |
