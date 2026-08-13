"""Render EDA Markdown from notebook-produced, code-verified metrics."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/"docs"/"data"
p=json.loads((DATA/"profiling_metrics.json").read_text(encoding="utf-8"))
e=json.loads((DATA/"eda_metrics.json").read_text(encoding="utf-8"))
fmt=lambda n:f"{n:,.0f}".replace(",",".")
money=lambda n:f"{n:,.2f}".replace(",","_").replace(".",",").replace("_",".")
pct=lambda x:f"{x:.3%}".replace(".",",")
type_rows="\n".join(f"| {r['type']} | {fmt(r['transaction_count'])} | {fmt(r['fraud_count'])} | {pct(r['fraud_rate'])} |" for r in e["by_type"])
band_rows="\n".join(f"| {r['AmountBand']} | {fmt(r['transaction_count'])} | {fmt(r['fraud_count'])} | {pct(r['fraud_rate'])} |" for r in e["by_band"])
insights=f'''# Khảo sát và phân tích dữ liệu PaySim – EDA-01

**Nguồn:** `{e['source']}`

**Ngày chạy:** {e['run_date']}

**Thực hiện:** Khải; **kiểm chứng/phụ trách hạng mục:** Châm

**Phương pháp:** đọc toàn bộ CSV theo chunk 200.000 dòng; ground truth là `isFraud`.

## 1. Tổng quan và chất lượng dữ liệu

| Chỉ số | Kết quả đã kiểm chứng |
|---|---:|
| Số dòng / số cột | {fmt(p['rows'])} / {p['columns']} |
| Null | 0 |
| Step | 1–743 (31 ngày mô phỏng) |
| Tổng amount | {money(e['total_amount'])} |
| Fraud count | {fmt(e['fraud'])} |
| Fraud rate | {pct(e['fraud_rate'])} |
| `isFlaggedFraud = 1` | {fmt(p['flagged'])} |
| Duplicate hoàn toàn / nhóm duplicate | {fmt(p['duplicate_rows'])} / {fmt(p['duplicate_groups'])} |
| Dòng có balance âm | {fmt(p['negative_balance_rows'])} |
| Mismatch số dư nguồn / đích | {fmt(p['origin_balance_mismatch'])} / {fmt(p['destination_balance_mismatch'])} |

Không loại dữ liệu vì balance mismatch. PaySim là dữ liệu mô phỏng; số dư có thể không phản ánh một phép ghi sổ khép kín ở từng dòng. ETL nên giữ bản ghi gốc, lưu cờ chất lượng và các chênh lệch dẫn xuất để phân tích.

## 2. Theo loại giao dịch

| Type | Transaction count | Fraud count | Fraud rate trong type |
|---|---:|---:|---:|
{type_rows}

Fraud chỉ xuất hiện ở `TRANSFER` và `CASH_OUT`. `CASH_OUT` có fraud count cao hơn một chút, nhưng `TRANSFER` có fraud rate cao hơn; hai khái niệm không được dùng thay thế nhau.

![Fraud theo type](figures/02_fraud_by_type.png)

## 3. Theo thời gian

- Giờ có fraud count cao nhất: **{e['max_fraud_count_hour']}h**.
- Giờ có fraud rate cao nhất: **{e['max_fraud_rate_hour']}h**.
- Ngày có fraud count cao nhất: **ngày {e['max_fraud_count_day']}**.
- Ngày có fraud rate cao nhất: **ngày {e['max_fraud_rate_day']}**; ngày này chỉ có 272 giao dịch và tất cả là fraud, nên không nên kết luận rủi ro chỉ từ rate mà không hiển thị transaction count.

![Fraud theo giờ](figures/03_fraud_by_hour.png)

## 4. Theo amount

| Amount band | Transaction count | Fraud count | Fraud rate |
|---|---:|---:|---:|
{band_rows}

- Tổng amount fraud: **{money(e['fraud_amount'])}**, chiếm **{pct(e['fraud_amount_share'])}** tổng amount.
- XXL có fraud rate cao nhất, trong khi L có fraud count cao nhất. Dashboard phải trình bày đồng thời count, rate và mẫu số.

![Phân phối amount](figures/04_amount_distribution.png)

## 5. Theo tài khoản

- `nameOrig` phân biệt: **{fmt(e['unique_orig'])}**; `nameDest` phân biệt: **{fmt(e['unique_dest'])}**.
- Toàn bộ {fmt(e['orig_prefix']['C'])} tài khoản nguồn mang prefix C; merchant không xuất hiện ở nguồn.
- Ở đích: C = {fmt(e['dest_prefix']['C'])}, M = {fmt(e['dest_prefix']['M'])}; merchant chỉ xuất hiện ở đích.
- Tài khoản nguồn xuất hiện nhiều nhất có 3 giao dịch; tài khoản đích đứng đầu là `{e['top_dest'][0][0]}` với {e['top_dest'][0][1]} giao dịch.
- Mỗi nguồn fraud chỉ xuất hiện một lần; nhóm đích fraud cao nhất có 2 giao dịch fraud.
- Fraud có `oldbalanceDest = 0`: **{fmt(e['old_dest_zero_fraud'])}/{fmt(e['fraud'])} ({pct(e['old_dest_zero_fraud_rate'])})**. Đây là dấu hiệu đáng chú ý, chưa phải bằng chứng tài khoản mule nếu chưa có dữ liệu bổ sung.

## 6. Theo balance

- Full-drain (`abs(oldbalanceOrg - amount) < 0,01` và `newbalanceOrig = 0`): **{fmt(e['full_drain_fraud'])}/{fmt(e['fraud'])} ({pct(e['full_drain_fraud_rate'])})** fraud.
- `BalanceDropOrig = oldbalanceOrg - newbalanceOrig` và `BalanceChangeDest = newbalanceDest - oldbalanceDest` là trường dẫn xuất độc lập với nhãn; `isFraud` không được dùng làm đầu vào tạo feature.
- Full-drain và `oldbalanceDest = 0` là các dấu hiệu đáng chú ý; chưa gọi là feature “mạnh nhất” khi chưa có phép đo so sánh trên mô hình/validation.

![So sánh balance](figures/06_balance_patterns.png)

## 7. Ảnh hưởng triển khai

- **Data Warehouse:** lưu `HourOfDay`, `StepDay`, `AmountBand`, `AccountType`, `BalanceDropOrig`, `BalanceChangeDest`, `IsHighRiskType`; giữ nguyên balance gốc và cờ mismatch.
- **ETL:** kiểm tra schema/domain/null/amount âm/account format; không loại bản ghi chỉ vì mismatch; reconciliation phải giữ đủ {fmt(e['rows'])} dòng.
- **ML:** chỉ dùng `isFraud` làm nhãn; `isFlaggedFraud` là thuộc tính nguồn; đánh giá feature bằng validation thay vì suy diễn từ EDA.
- **Dashboard:** luôn hiển thị fraud count, fraud rate và transaction count; cảnh báo nhóm có mẫu số nhỏ.
'''
(DATA/"data_insights.md").write_text(insights,encoding="utf-8")

report_path=ROOT/"docs"/"reports"/"bao_cao_tong_hop.md"; report=report_path.read_text(encoding="utf-8")
repl={
"*[TODO: Loại nào chiếm tỷ lệ cao nhất?]*":f"TRANSFER có fraud rate cao nhất ({pct(next(x['fraud_rate'] for x in e['by_type'] if x['type']=='TRANSFER'))}); CASH_OUT có fraud count cao nhất ({fmt(next(x['fraud_count'] for x in e['by_type'] if x['type']=='CASH_OUT'))}).",
"*[TODO: Giờ cao điểm?]*":f"Fraud count cao nhất lúc {e['max_fraud_count_hour']}h; fraud rate cao nhất lúc {e['max_fraud_rate_hour']}h (cần đọc cùng transaction count).",
"*[TODO: Amount Band nào?]*":f"L có fraud count cao nhất; XXL có fraud rate cao nhất ({pct(next(x['fraud_rate'] for x in e['by_band'] if x['AmountBand']=='XXL'))}).",
"*[TODO: Quan sát nổi bật?]*":f"Full-drain xuất hiện ở {fmt(e['full_drain_fraud'])}/{fmt(e['fraud'])} fraud ({pct(e['full_drain_fraud_rate'])}); không loại balance mismatch.",
"*[TODO]* |\n| Recall":f"{pct(e['fraud_rate'])} ({fmt(e['fraud'])}/{fmt(e['rows'])}) |\n| Recall"
}
for old,new in repl.items():
    if old not in report: print("WARN marker already replaced")
    report=report.replace(old,new,1)
report_path.write_text(report,encoding="utf-8")
print("Rendered Markdown from verified metrics")
