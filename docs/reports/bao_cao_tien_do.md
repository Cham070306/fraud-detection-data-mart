# Báo cáo Tiến độ Dự án
# PaySim Fraud Detection Data Mart

| Mục | Nội dung |
|-----|---------|
| **Tên dự án** | PaySim Fraud Detection Data Mart (Đồ án môn Data Warehouse) |
| **Dataset** | PaySim Synthetic Financial Dataset (Kaggle) |
| **Ngày lập báo cáo** | 2026-09-04 |
| **Trạng thái tổng thể** | 🟢 **~90% hoàn thành** — pipeline chính hoàn tất, còn phần bàn giao .pbix |

---

## 1. Tổng quan tiến độ theo nhánh công việc

| Nhánh công việc | TV | Tiến độ | Ghi chú |
|---|---|---|---|
| Thiết kế DW / ERD / Star Schema | TV2 | ✅ 100% | 7 dims, 3 facts, 5 BI views |
| SQL DDL (00–09) | TV2 | ✅ 100% | Toàn bộ schema + constraints + indexes |
| ETL Pipeline | TV2 | ✅ 100% | 6.36M dòng, 0 reject, reconciliation PASS |
| Phân tích dữ liệu / EDA | TV3 | ✅ 100% | Profiling + 8 câu hỏi nghiệp vụ |
| ML Training / Scoring | TV4 | ✅ 100% | Random Forest v1.0.0 |
| **Dashboard & API** | **TV5** | 🟡 **~90%** | Streamlit + API + spec Power BI xong; còn build `.pbix` |
| Tài liệu & Bàn giao | TV1 | 🟡 ~85% | Cập nhật báo cáo tổng hợp |

---

## 2. Kết quả thực hiện theo thành viên

### 2.1 Data Mart & ETL (TV2 — Data Engineer)

| Hạng mục | Kết quả |
|----------|---------|
| Bảng Dimension | 7/7 ✅ |
| Bảng Fact | 3/3 ✅ |
| BI Views | 5/5 ✅ |
| Staging rows | 6.362.620 ✅ |
| FactTransaction rows | 6.362.620 ✅ |
| Rejected rows | 0 ✅ |
| Reconciliation | PASS ✅ |
| ETL re-run (idempotency) | PASS ✅ (không duplicate) |
| Orphan FK | 0 ✅ |
| EDA comparison | 140/141 PASS ✅ |

### 2.2 Phân tích dữ liệu (TV3 — Data Analyst)

| Câu hỏi nghiệp vụ | Kết quả |
|---|---|
| BQ-01: Fraud theo loại GD | TRANSFER: fraud rate cao nhất 0,769%; CASH_OUT: fraud count cao nhất 4.116 |
| BQ-02: Fraud theo thời gian | Fraud count cao nhất lúc 9h; fraud rate cao nhất lúc 4h |
| BQ-03: Fraud theo khoảng tiền | Band L: count cao nhất; Band XXL: rate cao nhất 5,080% |
| BQ-04: Pattern số dư | Full-drain: 8.024/8.213 fraud (97,699%) |

### 2.3 Mô hình Machine Learning (TV4 — ML Engineer)

| Chỉ số | Mục tiêu | Kết quả thực tế |
|--------|---------|-----------------|
| Model | — | **Random Forest** (so sánh: Baseline Rule, Logistic Regression) |
| Version | — | **v1.0.0** |
| Threshold | tối ưu | **0.32** |
| Precision | Tham khảo | **0.999201** |
| **Recall** | **≥ 0.80** | **0.999201** ✅ |
| **F2-Score** | **≥ 0.70** | **0.999201** ✅ |
| PR-AUC | > 0.60 | **0.999999** ✅ |
| Confusion Matrix (test) | — | TN 88.213 / FP 1 / FN 1 / TP 1.251 |
| Fraud Amount Capture Rate | Tối đa | **99,98%** ✅ |

> ⚠️ **Lưu ý:** Số liệu gần hoàn hảo do dữ liệu PaySim là tổng hợp (synthetic) — biến số dư khiến fraud dễ tách biệt. Không diễn giải như hiệu năng ngân hàng thực.

### 2.4 Dashboard & App (TV5 — BI / App Dev)

| Hạng mục | Trạng thái |
|----------|-----------|
| Streamlit Dashboard (5 pages) | ✅ Hoàn thành |
| Alert Queue + Feedback Loop | ✅ Hoàn thành |
| FastAPI Data Service | ✅ Hoàn thành (8 endpoints) |
| Power BI Spec (`dashboard_spec.md`) | ✅ Hoàn thành |
| Power BI `.pbix` | 🟡 **Chờ build** trong Power BI Desktop |
| Demo Runbook | ✅ Hoàn thành |

---

## 3. KPI Tổng hợp

| KPI | Mục tiêu | Kết quả |
|-----|---------|---------|
| ETL Reconciliation Rate | = 100% | **100%** ✅ |
| Fraud Rate (Volume) | ~0.13% | **0,129%** (8.213/6.362.620) ✅ |
| Recall | ≥ 80% | **99,92%** ✅ |
| F2-Score | ≥ 0.70 | **99,92%** ✅ |
| Captured Fraud Loss Rate | Tối đa | **99,98%** ✅ |
| HIGH+CRITICAL Alerts | — | **8.218** |
| Fraud Amount | — | 12.056.415.427,84 (1,054% tổng) |

---

## 4. Bàn giao theo `yeucau..txt`

| # | Yêu cầu | Trạng thái | Ghi chú |
|---|---------|-----------|---------|
| 1 | Power BI: 5 pages + drill-through | 🟡 90% | Spec xong; `.pbix` chờ build thủ công |
| 2 | Drill-through đến giao dịch | ✅ | Spec + API `GET /api/transactions/{key}` |
| 3 | Tích hợp phản hồi xử lý | ✅ | Feedback loop Alert Queue |
| 4 | Ứng dụng + kịch bản demo | ✅ | Streamlit + `demo_runbook.md` |

### Files bàn giao

| File | Đường dẫn | Trạng thái |
|------|-----------|-----------|
| Power BI file | `dashboard/FraudDetection.pbix` | 🟡 Chờ build |
| Power BI spec | `dashboard/dashboard_spec.md` | ✅ |
| App | `dashboard/app/app.py` | ✅ |
| Alert Queue | `dashboard/app/pages/alert_queue.py` | ✅ |
| Demo runbook | `docs/demo/demo_runbook.md` | ✅ |
| Streamlit (full) | `dashboard/streamlit/*` | ✅ |
| API | `src/api/main.py`, `src/api/schemas.py` | ✅ |
| SQL dashboard objects | `sql/10_create_dashboard_objects.sql` | ✅ |

---

## 5. Tồn đọng & Việc cần làm tiếp theo

1. **[TV5] Build `dashboard/FraudDetection.pbix`** trong Power BI Desktop theo `dashboard_spec.md`.
2. **[TV1] Cập nhật `bao_cao_tong_hop.md`** — điền kết quả ML & Dashboard (đã có trong báo cáo này).
3. **[Cả nhóm] Chốt quản lý nhánh** — hiện có 2 phiên bản dashboard trên nhánh `Hiep` và `Hiep2`; cần thống nhất merge.
4. **Kiểm thử end-to-end** — cài dependencies (`requirements.txt`), kết nối SQL Server, chạy `run_dashboard.ps1`.

---

## 6. Rủi ro & Giảm thiểu

| Rủi ro | Mức độ | Giảm thiểu |
|--------|--------|-----------|
| Số liệu ML quá cao dễ hiểu nhầm | Trung bình | Ghi rõ nguồn synthetic trong mọi báo cáo |
| SQL Server chưa load FactModelScore/FactAlert | Cao | Cần TV2 load theo `docs/integration/sql-handoff.md` |
| Branch phân mảnh (Hiep vs Hiep2) | Trung bình | Chốt merge sớm, giữ `develop` làm nguồn chuẩn |

---

## 7. Tài liệu Đính kèm

- `docs/design/bus_matrix.md`, `docs/design/star_schema.md`, `docs/design/fraud-detection-erd.md`
- `docs/reports/model-report.md`, `docs/reports/bao_cao_etl_chi_tiet.md`
- `dashboard/dashboard_spec.md`, `docs/demo/demo_runbook.md`
