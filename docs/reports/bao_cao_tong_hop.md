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
| **Nhóm** | *[TODO: Tên nhóm/MSSV]* |
| **Giảng viên hướng dẫn** | *[TODO]* |
| **Ngày hoàn thành** | *[TODO]* |

---

## 2. Tóm tắt Kết quả Thực hiện

### 2.1 Data Mart (TV2 — Data Engineer)

| Hạng mục | Kết quả |
|----------|---------|
| Số bảng Dimension | 7/7 ✅ |
| Số bảng Fact | 3/3 ✅ |
| Số BI Views | *[TODO]* |
| Tổng dòng Staging load | *[TODO: 6.362.620 rows expected]* |
| Tổng dòng FactTransaction | *[TODO]* |
| Reconciliation | *[TODO: PASS/FAIL]* |
| Thời gian ETL | *[TODO: X phút]* |

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
| Model sử dụng | LightGBM / XGBoost | *[TODO]* |
| Precision | Tham khảo | *[TODO]* |
| **Recall** | **≥ 0.80** | *[TODO]* |
| **F2-Score** | **≥ 0.70** | *[TODO: PASS/FAIL]* |
| PR-AUC | > 0.60 | *[TODO]* |
| Threshold được chọn | 0.50 (baseline) | *[TODO: giá trị thực]* |

### 2.4 Dashboard & App (TV5 — BI/App Dev)

| Hạng mục | Trạng thái |
|----------|-----------|
| Power BI: Executive Overview | *[TODO: ✅/❌]* |
| Power BI: Transaction Analysis | *[TODO]* |
| Power BI: Model Performance | *[TODO]* |
| Power BI: Alert Queue | *[TODO]* |
| Power BI: ETL Quality | *[TODO]* |
| Streamlit Alert Queue App | *[TODO]* |

---

## 3. KPI Tổng hợp

| KPI | Mục tiêu | Kết quả |
|-----|---------|---------|
| ETL Reconciliation Rate | = 100% | *[TODO]* |
| Fraud Rate (Volume) | ~0.13% (verify) | 0,129% (8.213/6.362.620) |
| Recall | ≥ 80% | *[TODO]* |
| F2-Score | ≥ 0.70 | *[TODO]* |
| Captured Fraud Loss Rate | Tối đa | *[TODO]* |

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
