# Báo cáo Tổng hợp Dự án
# PaySim Fraud Detection Data Mart

---

> ⚠️ **Tài liệu này sẽ được hoàn thiện khi toàn bộ dự án hoàn thành.**
> Cấu trúc đã sẵn sàng — các phần có nhãn *[TODO]* sẽ được TV1 điền sau khi tổng hợp kết quả từ tất cả thành viên.

---

## 1. Thông tin Dự án

| Mục | Nội dung |
|-----|---------|
| **Tên dự án** | PaySim Fraud Detection Data Mart |
| **Môn học** | Data Warehouse |
| **Tên nhóm** | *(Cập nhật sau)* |
| **Giảng viên hướng dẫn** | *(Cập nhật sau)* |
| **Ngày hoàn thành** | *(Cập nhật sau)* |

---

## 2. Tóm tắt Kết quả Thực hiện

### 2.1 Data Mart (TV2 — Data Engineer)

| Hạng mục | Kết quả |
|----------|---------|
| Số bảng Dimension | 7/7 ✅ |
| Số bảng Fact | 3/3 ✅ |
| Số BI Views | 5/5 ✅ |
| Tổng dòng Staging load | 6.362.620 ✅ |
| Tổng dòng FactTransaction | 6.362.620 ✅ |
| Reconciliation | PASS ✅ |
| Thời gian ETL | 1h48m (lần 1) / 1h46m (lần 2) |
| ETL re-run (không duplicate) | PASS ✅ |
| Orphan FK | 0/5 ✅ |
| EDA comparison | 140/141 PASS ✅ |

### 2.2 Phân tích Dữ liệu (TV3 — Data Analyst)

| Câu hỏi Nghiệp vụ | Kết quả Phát hiện |
|---|---|
| BQ-01: Fraud theo loại GD | TRANSFER có fraud rate cao nhất (0,769%); CASH_OUT có fraud count cao nhất (4.116). |
| BQ-02: Fraud theo thời gian | Fraud count cao nhất lúc 9h; fraud rate cao nhất lúc 4h (cần đọc cùng transaction count). |
| BQ-03: Fraud theo khoảng tiền | L có fraud count cao nhất; XXL có fraud rate cao nhất (5,080%). |
| BQ-04: Pattern số dư | Full-drain xuất hiện ở 8.024/8.213 fraud (97,699%); không loại balance mismatch. |

### 2.3 Mô hình Machine Learning (TV4 — ML Engineer)

| Chỉ số | Giá trị Mục tiêu | Kết quả Thực tế |
|--------|-----------------|-----------------|
| Model sử dụng | — | **Random Forest v1.0.0** |
| Precision | Tham khảo | **0,999201** |
| **Recall** | **≥ 0.80** | **0,999201** ✅ |
| **F2-Score** | **≥ 0.70** | **0,999201** ✅ |
| PR-AUC | > 0.60 | **0,999999** ✅ |
| Threshold được chọn | 0.50 (baseline) | **0,32** |
| Confusion Matrix (test) | — | TN 88.213 / FP 1 / FN 1 / TP 1.251 |
| Fraud Amount Capture Rate | Tối đa | **99,98%** ✅ |

### 2.4 Dashboard & App (TV5 — BI/App Dev)

| Hạng mục | Trạng thái |
|----------|-----------|
| Power BI: Executive Overview | ✅ Spec + Streamlit page |
| Power BI: Transaction Analysis | ✅ Spec + Streamlit page |
| Power BI: Model Performance | ✅ Spec + Streamlit page |
| Power BI: Alert Queue | ✅ Spec + Streamlit page + Feedback Loop |
| Power BI: ETL Quality | ✅ Spec + Streamlit page |
| Streamlit Dashboard (5 pages) | ✅ Hoàn thành |
| FastAPI Data Service | ✅ Hoàn thành |
| Demo Runbook | ✅ Hoàn thành |
| Power BI `.pbix` | 🟡 Chờ build thủ công trong Power BI Desktop |

---

## 3. KPI Tổng hợp

| KPI | Mục tiêu | Kết quả |
|-----|---------|---------|
| ETL Reconciliation Rate | = 100% | **100%** ✅ (2 lần chạy PASS) |
| Fraud Rate (Volume) | ~0.13% | **0,129%** (8.213/6.362.620) ✅ |
| Recall | ≥ 80% | **99,92%** ✅ |
| F2-Score | ≥ 0.70 | **99,92%** ✅ |
| Captured Fraud Loss Rate | Tối đa | **99,98%** ✅ |

---

## 4. Cấu trúc Files Bàn giao (TV1 Checklist)

| File | Đường dẫn | Trạng thái |
|------|-----------|-----------|
| Project Charter | `docs/requirements/project_charter.md` | ✅ Hoàn thành |
| Business Requirements | `docs/requirements/business_requirements.md` | ✅ Hoàn thành |
| KPI Dictionary | `docs/requirements/kpi_dictionary.md` | ✅ Hoàn thành |
| Bus Matrix & Star Schema | `docs/design/bus_matrix.md` | ✅ Hoàn thành |
| Decision Policy | `docs/design/decision_policy.md` | ✅ Hoàn thành |
| README.md | `README.md` | ✅ Hoàn thành |
| Báo cáo Tổng hợp | `docs/reports/bao_cao_tong_hop.md` | 🔄 Chờ điền kết quả |

---

## 5. Bài học Kinh nghiệm (Lessons Learned)

*[TODO: Điền sau khi dự án hoàn thành — những khó khăn gặp phải, cách giải quyết, điều sẽ làm khác nếu làm lại]*

---

## 6. Tài liệu Đính kèm

- *[TODO: Link file Power BI .pbix]*
- *[TODO: Link video demo]*
- *[TODO: Link slide thuyết trình]*
