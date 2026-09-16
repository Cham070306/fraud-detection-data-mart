# Dữ liệu PaySim

Đặt dữ liệu nguồn tại:

```text
data/raw/PS_20174392719_1491204439457_log.csv
```

Tệp dữ liệu thô không được commit vào Git. Có thể tải bộ PaySim từ Kaggle hoặc
copy tệp đã giải nén vào thư mục `data/raw`.

Schema bắt buộc gồm 11 cột:

```text
step,type,amount,nameOrig,oldbalanceOrg,newbalanceOrig,nameDest,
oldbalanceDest,newbalanceDest,isFraud,isFlaggedFraud
```

ETL đọc đường dẫn, chunk size, ngày mô phỏng bắt đầu và giới hạn step từ
`configs/app.yaml`. Chạy `python scripts/preflight.py` trước ETL để kiểm tra tệp.

`data/interim` và `data/processed` cũng không được commit vì có thể chứa dữ liệu
trung gian lớn hoặc dữ liệu dẫn xuất từ nguồn.
