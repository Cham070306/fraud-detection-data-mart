"""Build the two reproducible PaySim EDA notebooks."""
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]

COMMON = '''from pathlib import Path
import hashlib, json, math, re
from collections import Counter
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display, Markdown

SEED = 42
CHUNK_SIZE = 200_000
ROOT = Path.cwd().resolve()
if ROOT.name == "notebooks": ROOT = ROOT.parent
RAW_DIR = ROOT / "data" / "raw"
CSV_PATH = next((RAW_DIR / n for n in ["PS_20174392719_1491204439457_log.csv", "PaySim.csv"] if (RAW_DIR / n).exists()), None)
if CSV_PATH is None:
    raise FileNotFoundError(f"Đặt PaySim tại {RAW_DIR} với một trong hai tên được hỗ trợ.")
OUT_DIR = ROOT / "docs" / "data"
FIG_DIR = OUT_DIR / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True); FIG_DIR.mkdir(parents=True, exist_ok=True)
EXPECTED_COLUMNS = ["step","type","amount","nameOrig","oldbalanceOrg","newbalanceOrig","nameDest","oldbalanceDest","newbalanceDest","isFraud","isFlaggedFraud"]
header = pd.read_csv(CSV_PATH, nrows=0).columns.tolist()
assert header == EXPECTED_COLUMNS, f"Schema không đúng: {header}"
sns.set_theme(style="whitegrid")
print(f"Nguồn: {CSV_PATH.name} | chunk={CHUNK_SIZE:,} | seed={SEED}")'''

# Profiling does not draw charts. Keeping its imports minimal also makes it
# robust when an IDE has cached a Python session without optional EDA packages.
PROFILING_COMMON = COMMON.replace("import matplotlib.pyplot as plt\n", "").replace(
    "import seaborn as sns\n", ""
).replace('sns.set_theme(style="whitegrid")\n', "")

def nb(title, intro, cells):
    book = nbf.v4.new_notebook()
    book["metadata"]["kernelspec"] = {
        "display_name":"Python (.venv) - Fraud Detection",
        "language":"python",
        "name":"fraud-detection-data-mart",
    }
    book["metadata"]["language_info"] = {"name":"python","version":"3.12"}
    book["cells"] = [nbf.v4.new_markdown_cell(f"# {title}\n\n{intro}")] + cells
    return book

prof_cells = [
 nbf.v4.new_code_cell(PROFILING_COMMON),
 nbf.v4.new_markdown_cell("## 1. Profiling toàn bộ dữ liệu\n\nĐọc tuần tự theo chunk; hash 64-bit ổn định được lưu cho toàn bộ 11 cột nên phát hiện được duplicate nằm ở các chunk khác nhau."),
 nbf.v4.new_code_cell('''numeric_cols = ["step","amount","oldbalanceOrg","newbalanceOrig","oldbalanceDest","newbalanceDest","isFraud","isFlaggedFraud"]
counts = Counter(); nulls = Counter(); domains = {c:set() for c in ["type","isFraud","isFlaggedFraud"]}
distinct_sets = {c:set() for c in ["type","nameOrig","nameDest","isFraud","isFlaggedFraud"]}
mins = {c:math.inf for c in numeric_cols}; maxs = {c:-math.inf for c in numeric_cols}; sums = Counter()
invalid = Counter(); hashes=[]; numeric_parts={c:[] for c in numeric_cols}
orig_prefix=Counter(); dest_prefix=Counter(); mismatch_orig=0; mismatch_dest=0; abnormal_balance=Counter()
for chunk in pd.read_csv(CSV_PATH, chunksize=CHUNK_SIZE):
    counts["rows"] += len(chunk)
    for c in EXPECTED_COLUMNS: nulls[c] += int(chunk[c].isna().sum())
    for c in numeric_cols:
        a=chunk[c].to_numpy(); numeric_parts[c].append(a.copy()); mins[c]=min(mins[c],float(np.nanmin(a))); maxs[c]=max(maxs[c],float(np.nanmax(a))); sums[c]+=float(np.nansum(a))
    for c in distinct_sets: distinct_sets[c].update(chunk[c].dropna().unique().tolist())
    for c in domains: domains[c].update(chunk[c].dropna().unique().tolist())
    invalid["amount"] += int((~np.isfinite(chunk.amount) | (chunk.amount < 0)).sum())
    invalid["nameOrig"] += int((~chunk.nameOrig.str.match(r"^[CM]\\d+$", na=False)).sum())
    invalid["nameDest"] += int((~chunk.nameDest.str.match(r"^[CM]\\d+$", na=False)).sum())
    invalid["type"] += int((~chunk.type.isin(["CASH_IN","CASH_OUT","DEBIT","PAYMENT","TRANSFER"])).sum())
    invalid["isFraud"] += int((~chunk.isFraud.isin([0,1])).sum()); invalid["isFlaggedFraud"] += int((~chunk.isFlaggedFraud.isin([0,1])).sum())
    for k,v in chunk.nameOrig.str[0].value_counts().items(): orig_prefix[k]+=int(v)
    for k,v in chunk.nameDest.str[0].value_counts().items(): dest_prefix[k]+=int(v)
    abnormal_balance["negative"] += int((chunk[["oldbalanceOrg","newbalanceOrig","oldbalanceDest","newbalanceDest"]] < 0).any(axis=1).sum())
    mismatch_orig += int((~np.isclose(chunk.oldbalanceOrg - chunk.amount, chunk.newbalanceOrig, atol=.01)).sum())
    mismatch_dest += int((~np.isclose(chunk.oldbalanceDest + chunk.amount, chunk.newbalanceDest, atol=.01)).sum())
    hashes.append(pd.util.hash_pandas_object(chunk[EXPECTED_COLUMNS], index=False).to_numpy(dtype="uint64"))
all_hashes=np.concatenate(hashes); _, hash_counts=np.unique(all_hashes, return_counts=True)
duplicate_rows=int((hash_counts-1).clip(min=0).sum()); duplicate_groups=int((hash_counts>1).sum())
arrays={c:np.concatenate(v) for c,v in numeric_parts.items()}
print(f"Dòng={counts['rows']:,}; cột={len(EXPECTED_COLUMNS)}; duplicate dư={duplicate_rows:,}; nhóm duplicate={duplicate_groups:,}")'''),
 nbf.v4.new_markdown_cell("## 2. Bảng profiling và kiểm tra chất lượng"),
 nbf.v4.new_code_cell('''rows=[]
for c in EXPECTED_COLUMNS:
    is_num=c in numeric_cols; a=arrays[c] if is_num else None
    distinct=len(np.unique(a)) if is_num else len(distinct_sets[c])
    rows.append({"column":c,"dtype":str(pd.read_csv(CSV_PATH,nrows=1)[c].dtype),"non_null":counts["rows"]-nulls[c],"null_count":nulls[c],"null_pct":nulls[c]/counts["rows"]*100,"distinct":distinct,
      "min":float(np.nanmin(a)) if is_num else min(distinct_sets[c]),"max":float(np.nanmax(a)) if is_num else max(distinct_sets[c]),
      "mean":float(np.nanmean(a)) if is_num else "","median":float(np.nanmedian(a)) if is_num else "","p25":float(np.nanpercentile(a,25)) if is_num else "","p75":float(np.nanpercentile(a,75)) if is_num else "","p95":float(np.nanpercentile(a,95)) if is_num else "","p99":float(np.nanpercentile(a,99)) if is_num else "",
      "invalid_count":invalid.get(c,0),"note": {"step":"1 step = 1 giờ mô phỏng","type":f"Domain: {sorted(domains['type'])}","amount":f"Tổng amount: {sums['amount']:.2f}","nameOrig":f"Prefix: {dict(orig_prefix)}","nameDest":f"Prefix: {dict(dest_prefix)}","isFraud":f"Domain: {sorted(domains['isFraud'])}","isFlaggedFraud":f"Domain: {sorted(domains['isFlaggedFraud'])}"}.get(c,"")})
profile=pd.DataFrame(rows); profile.to_csv(OUT_DIR/"profiling_summary.csv",index=False,encoding="utf-8-sig")
display(profile)
quality={"source":CSV_PATH.name,"run_date":pd.Timestamp.now().date().isoformat(),"rows":counts["rows"],"columns":len(EXPECTED_COLUMNS),"total_amount":sums["amount"],"fraud":int(sums["isFraud"]),"flagged":int(sums["isFlaggedFraud"]),"duplicate_rows":duplicate_rows,"duplicate_groups":duplicate_groups,"negative_balance_rows":abnormal_balance["negative"],"origin_balance_mismatch":mismatch_orig,"destination_balance_mismatch":mismatch_dest,"orig_prefix":dict(orig_prefix),"dest_prefix":dict(dest_prefix),"domains":{k:sorted(v) for k,v in domains.items()}}
(OUT_DIR/"profiling_metrics.json").write_text(json.dumps(quality,ensure_ascii=False,indent=2),encoding="utf-8")
display(Markdown(f"**Balance mismatch không bị loại bỏ:** nguồn {mismatch_orig:,} dòng; đích {mismatch_dest:,} dòng. Đây có thể là đặc tính mô phỏng/ghi nhận số dư của PaySim, không đủ căn cứ coi là dữ liệu lỗi."))'''),
 nbf.v4.new_code_cell('''assert counts["rows"] == 6_362_620 and int(sums["isFraud"]) == 8_213
assert profile.shape[0] == 11 and profile.null_count.sum() == 0
print("PASS: dataset PaySim chuẩn; CSV profiling đã ghi và kiểm tra.")''')]

eda_cells=[
 nbf.v4.new_code_cell(COMMON),
 nbf.v4.new_markdown_cell("## 1. Tổng hợp theo type, thời gian, amount, tài khoản và balance\n\n`isFraud` là ground truth; `isFlaggedFraud` chỉ được mô tả như cờ nguồn."),
 nbf.v4.new_code_cell('''type_parts=[]; hour_parts=[]; day_parts=[]; band_parts=[]; amount_label_parts=[]; balance_parts=[]
orig_counts=Counter(); dest_counts=Counter(); fraud_orig=Counter(); fraud_dest=Counter(); prefix_orig=Counter(); prefix_dest=Counter()
total_amount=fraud_amount=0.; old_dest_zero_fraud=full_drain_fraud=fraud_total=0
bins=[-np.inf,1000,10000,100000,1000000,10000000,np.inf]; labels=["XS","S","M","L","XL","XXL"]
for ch in pd.read_csv(CSV_PATH,chunksize=CHUNK_SIZE):
    ch["HourOfDay"]=(ch.step-1)%24; ch["StepDay"]=(ch.step-1)//24+1
    ch["AmountBand"]=pd.cut(ch.amount,bins=bins,labels=labels,right=False)
    for cols,target in [(["type"],type_parts),(["HourOfDay"],hour_parts),(["StepDay"],day_parts),(["AmountBand"],band_parts)]:
        target.append(ch.groupby(cols,observed=False).isFraud.agg(transaction_count="size",fraud_count="sum").reset_index())
    sample=pd.concat([g.sample(min(len(g),4000),random_state=SEED) for _,g in ch.groupby("isFraud")]); amount_label_parts.append(sample[["amount","isFraud"]])
    ch["BalanceDropOrig"]=ch.oldbalanceOrg-ch.newbalanceOrig; ch["BalanceChangeDest"]=ch.newbalanceDest-ch.oldbalanceDest
    balance_parts.append(ch.groupby("isFraud")[["BalanceDropOrig","BalanceChangeDest"]].agg(["mean","median"]))
    for k,v in ch.nameOrig.value_counts().items(): orig_counts[k]+=int(v)
    for k,v in ch.nameDest.value_counts().items(): dest_counts[k]+=int(v)
    fr=ch[ch.isFraud.eq(1)]; fraud_total+=len(fr)
    for k,v in fr.nameOrig.value_counts().items(): fraud_orig[k]+=int(v)
    for k,v in fr.nameDest.value_counts().items(): fraud_dest[k]+=int(v)
    for k,v in ch.nameOrig.str[0].value_counts().items(): prefix_orig[k]+=int(v)
    for k,v in ch.nameDest.str[0].value_counts().items(): prefix_dest[k]+=int(v)
    old_dest_zero_fraud+=int(fr.oldbalanceDest.eq(0).sum())
    full_drain_fraud+=int((np.isclose(fr.oldbalanceOrg-fr.amount,0,atol=.01)&fr.newbalanceOrig.eq(0)).sum())
    total_amount+=float(ch.amount.sum()); fraud_amount+=float(fr.amount.sum())
def combine(parts,key):
    x=pd.concat(parts); return x.groupby(key,observed=False)[["transaction_count","fraud_count"]].sum().reset_index().assign(fraud_rate=lambda d:d.fraud_count/d.transaction_count)
by_type=combine(type_parts,"type"); by_hour=combine(hour_parts,"HourOfDay"); by_day=combine(day_parts,"StepDay"); by_band=combine(band_parts,"AmountBand")
display(by_type); display(by_hour); display(by_day); display(by_band)'''),
 nbf.v4.new_markdown_cell("## 2. Biểu đồ và nhận xét"),
 nbf.v4.new_code_cell('''def save_show(name):
    plt.tight_layout(); plt.savefig(FIG_DIR/name,dpi=140,bbox_inches="tight"); plt.show()
fig,ax=plt.subplots(figsize=(10,5)); sns.barplot(data=by_type,x="type",y="transaction_count",ax=ax); ax.set(title="Phân phối giao dịch theo loại",xlabel="Loại giao dịch",ylabel="Số giao dịch"); save_show("01_transactions_by_type.png")
fig,axs=plt.subplots(1,2,figsize=(13,5)); sns.barplot(data=by_type,x="type",y="fraud_count",ax=axs[0]); sns.barplot(data=by_type,x="type",y="fraud_rate",ax=axs[1]); axs[0].set(title="Fraud count theo loại",xlabel="Loại",ylabel="Số fraud"); axs[1].set(title="Fraud rate theo loại",xlabel="Loại",ylabel="Tỷ lệ fraud"); axs[1].yaxis.set_major_formatter(lambda x,pos:f"{x:.2%}"); save_show("02_fraud_by_type.png")
fig,axs=plt.subplots(1,2,figsize=(13,5)); sns.lineplot(data=by_hour,x="HourOfDay",y="fraud_count",marker="o",ax=axs[0]); sns.lineplot(data=by_hour,x="HourOfDay",y="fraud_rate",marker="o",ax=axs[1]); axs[0].set(title="Fraud count theo giờ",xlabel="Giờ mô phỏng trong ngày",ylabel="Số fraud"); axs[1].set(title="Fraud rate theo giờ",xlabel="Giờ mô phỏng trong ngày",ylabel="Tỷ lệ fraud"); axs[1].yaxis.set_major_formatter(lambda x,pos:f"{x:.2%}"); save_show("03_fraud_by_hour.png")
sample=pd.concat(amount_label_parts,ignore_index=True); sample["label"]=sample.isFraud.map({0:"Non-fraud",1:"Fraud"}); fig,ax=plt.subplots(figsize=(10,5)); sns.histplot(data=sample,x="amount",hue="label",bins=60,log_scale=(True,False),element="step",stat="density",common_norm=False,ax=ax); ax.set(title="Phân phối amount: fraud và non-fraud (mẫu cố định)",xlabel="Amount (log scale)",ylabel="Mật độ"); save_show("04_amount_distribution.png")
fig,axs=plt.subplots(1,2,figsize=(13,5)); sns.barplot(data=by_band,x="AmountBand",y="fraud_count",ax=axs[0]); sns.barplot(data=by_band,x="AmountBand",y="fraud_rate",ax=axs[1]); axs[0].set(title="Fraud count theo amount band",xlabel="Amount band",ylabel="Số fraud"); axs[1].set(title="Fraud rate theo amount band",xlabel="Amount band",ylabel="Tỷ lệ fraud"); axs[1].yaxis.set_major_formatter(lambda x,pos:f"{x:.2%}"); save_show("05_fraud_by_amount_band.png")
balance=pd.concat(balance_parts).groupby(level=0).mean(); display(balance); balance.xs("mean",axis=1,level=1).plot(kind="bar",figsize=(10,5),title="Thay đổi số dư trung bình theo nhãn"); plt.xlabel("isFraud (ground truth)"); plt.ylabel("Đơn vị amount"); plt.legend(["Giảm số dư nguồn","Tăng số dư đích"]); save_show("06_balance_patterns.png")'''),
 nbf.v4.new_markdown_cell("## 3. Kết quả định lượng và kiểm chứng"),
 nbf.v4.new_code_cell('''metrics={"source":CSV_PATH.name,"run_date":pd.Timestamp.now().date().isoformat(),"rows":int(by_type.transaction_count.sum()),"fraud":fraud_total,"fraud_rate":fraud_total/int(by_type.transaction_count.sum()),"total_amount":total_amount,"fraud_amount":fraud_amount,"fraud_amount_share":fraud_amount/total_amount,
"unique_orig":len(orig_counts),"unique_dest":len(dest_counts),"orig_prefix":dict(prefix_orig),"dest_prefix":dict(prefix_dest),"top_orig":orig_counts.most_common(10),"top_dest":dest_counts.most_common(10),"top_fraud_orig":fraud_orig.most_common(10),"top_fraud_dest":fraud_dest.most_common(10),"old_dest_zero_fraud":old_dest_zero_fraud,"old_dest_zero_fraud_rate":old_dest_zero_fraud/fraud_total,"full_drain_fraud":full_drain_fraud,"full_drain_fraud_rate":full_drain_fraud/fraud_total,
"max_fraud_count_hour":int(by_hour.loc[by_hour.fraud_count.idxmax(),"HourOfDay"]),"max_fraud_rate_hour":int(by_hour.loc[by_hour.fraud_rate.idxmax(),"HourOfDay"]),"max_fraud_count_day":int(by_day.loc[by_day.fraud_count.idxmax(),"StepDay"]),"max_fraud_rate_day":int(by_day.loc[by_day.fraud_rate.idxmax(),"StepDay"]),
"by_type":by_type.to_dict("records"),"by_hour":by_hour.to_dict("records"),"by_day":by_day.to_dict("records"),"by_band":by_band.astype({"AmountBand":"str"}).to_dict("records")}
(OUT_DIR/"eda_metrics.json").write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({k:v for k,v in metrics.items() if not k.startswith("by_")},ensure_ascii=False,indent=2))
assert metrics["rows"]==6_362_620 and fraud_total==8_213 and set(by_type.loc[by_type.fraud_count.gt(0),"type"])=={"TRANSFER","CASH_OUT"}
print("PASS: tổng số, ground truth và domain fraud theo type đã được kiểm chứng.")''')]

nbf.write(nb("01 – Data Profiling PaySim","Thực hiện: Khải; kiểm chứng/phụ trách hạng mục: Châm. Toàn bộ số liệu được tính từ CSV thật; không loại dữ liệu vì balance mismatch.",prof_cells),ROOT/"notebooks"/"01_data_profiling.ipynb")
nbf.write(nb("02 – EDA Fraud PaySim","Thực hiện: Khải; kiểm chứng/phụ trách hạng mục: Châm. Phân tích type, thời gian, amount, tài khoản và balance; ground truth là `isFraud`.",eda_cells),ROOT/"notebooks"/"02_eda_fraud.ipynb")
print("Built notebooks")
