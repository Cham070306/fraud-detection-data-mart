# Data Insights - PaySim Fraud Detection
# Tac gia: Khai (TV2)
# Ngay: 2026-08-10

## 1. Tong quan tap du lieu

| Thong tin | Gia tri |
|-----------|---------|
| Tong so dong | 6.362.620 |
| Tong so cot | 11 |
| Null values | 0 (khong co) |
| Khoang thoi gian | Step 1 - 743 (~ 31 ngay mo phong) |
| Tong amount | 1.144.392.944.759.77 don vi |

## 2. Phan phoi theo loai giao dich (type)

| Type | So dong | Ty le |
|------|---------|-------|
| CASH_IN | 1.399.284 | 22.0% |
| CASH_OUT | 2.237.500 | 35.2% |
| DEBIT | 41.432 | 0.7% |
| PAYMENT | 2.151.495 | 33.8% |
| TRANSFER | 532.909 | 8.4% |

**Insight DW:** TypeCode la business key cua DimTransactionType. IsHighRiskType = 1 cho TRANSFER va CASH_OUT.

## 3. Phan tich gian lan (isFraud)

| Loai | So dong | Ty le |
|------|---------|-------|
| Non-fraud (0) | 6.354.407 | 99.871% |
| Fraud (1) | 8.213 | 0.129% |

**Mat can bang nhan nghiem trong.** Ti le fraud chi 0.129%.

### 3.1. Fraud chi xuat hien o 2 loai giao dich

| Type | Fraud count | Ty le fraud trong type |
|------|-------------|------------------------|
| TRANSFER | 4.097 | 0.769% |
| CASH_OUT | 4.116 | 0.184% |
| PAYMENT | 0 | 0% |
| DEBIT | 0 | 0% |
| CASH_IN | 0 | 0% |

**Insight DW:** IsHighRiskType trong DimTransactionType = 1 cho TRANSFER va CASH_OUT.
**Insight ETL:** Chi can flag high-risk khi type = TRANSFER hoac CASH_OUT.
**Insight ML:** Feature engineering nen tap trung vao 2 loai nay.

### 3.2. Pattern Full-Drain (so du bi vet sach)

- 8.024 / 8.213 giao dich fraud (97.7%) co pattern: oldbalanceOrg == amount AND newbalanceOrig == 0
- Nguoi gian lan rut het toan bo so du tai khoan nguon
- Day la feature manh nhat de phat hien fraud

**Insight DW:** Them cot BalanceDropOrig = OldBalanceOrig - NewBalanceOrig vao FactTransaction.

### 3.3. isFlaggedFraud khong dang tin cay

- Chi co 16 dong duoc danh dau isFlaggedFraud = 1
- Trong khi thuc te co 8.213 fraud
- isFlaggedFraud la co bao dong nguon, KHONG dung lam ground truth

**Insight ETL:** Luu isFlaggedFraud vao staging va fact de tham khao, nhung khong dung lam nhan ML.

## 4. Phan tich tai khoan (Account)

| Thong tin | Gia tri |
|-----------|---------|
| Unique nameOrig | 6.353.307 |
| Unique nameDest | 2.722.362 |
| nameOrig bat dau bang C | 100% (tat ca Customer) |
| nameDest bat dau bang C | 4.211.125 (Customer) |
| nameDest bat dau bang M | 2.151.495 (Merchant) |
| nameOrig bat dau bang M | 0 (khong co Merchant o phia nguon) |

**Insight DW:** AccountType = C hoac M lay tu ky tu dau cua nameOrig/nameDest.
**Insight ETL:** Validate account ID bat buoc bat dau bang C hoac M.
**Insight DW:** Merchant chi xuat hien o phia dich (nameDest), khong bao gio la nguon.

### 4.1. Fraud voi so du tai khoan dich = 0

- 5.351 / 8.213 giao dich fraud (65.2%) co oldbalanceDest = 0 truoc khi nhan tien
- Dau hieu tai khoan dich la tai khoan gia/mule account

**Insight ML:** oldbalanceDest = 0 khi nhan transfer la feature manh.

## 5. Phan tich khoang tien (Amount Band)

| Band | Nhan | Khoang | So dong | Ty le |
|------|------|--------|---------|-------|
| XS | Rat nho | < 1.000 | 142.642 | 2.2% |
| S | Nho | 1.000 - 9.999 | 1.143.361 | 18.0% |
| M | Trung binh | 10.000 - 99.999 | 2.239.253 | 35.2% |
| L | Lon | 100.000 - 999.999 | 2.706.738 | 42.5% |
| XL | Rat lon | 1.000.000 - 9.999.999 | 124.976 | 2.0% |
| XXL | Cuc lon | >= 10.000.000 | 5.650 | 0.1% |

**Fraud amount max = 10.000.000** (gioi han cua PaySim).
**Fraud amount tong = 12.056.415.427.84** don vi (1.05% tong amount).
**Insight DW:** 6 bang amount band nay chinh xac cho DimAmountBand.

## 6. Phan tich thoi gian (step)

- step = 1 den 743 (thieu step 744 so voi mo phong 744 gio)
- HourOfDay = (step - 1) % 24 : gio trong ngay (0-23)
- StepDay = (step - 1) / 24 + 1 : ngay thu may (1-31)
- Map sang ngay thuc tu 2023-01-01 theo cau hinh

**Insight DW:** DimDate.DateKey = 20230101 + (StepDay - 1) ngay, DimTime.TimeKey = HourOfDay.

## 7. Van de chat luong du lieu

| Van de | Ket qua kiem tra | Danh gia |
|--------|------------------|----------|
| Null values | 0 | Tot |
| Negative amount | 0 | Tot |
| Invalid type domain | 0 | Tot |
| Invalid isFraud values | 0 | Tot |
| Balance mismatch (PAYMENT/TRANSFER) | 1.674.676 | Can luu y (*) |
| Duplicate rows | Chua kiem tra day du | Can xac nhan |

(*) Balance mismatch PAYMENT/TRANSFER: oldbalanceOrg - amount != newbalanceOrig cho 1.674.676 dong.
Day la dac tinh cua du lieu mo phong PaySim, khong phai loi du lieu thuc.
ETL van nap tat ca dong, luu BalanceDropOrig = OldBalanceOrig - NewBalanceOrig de tinh chinh xac.

## 8. Ket luan va cac quyet dinh thiet ke

| Quyet dinh | Ly do |
|-----------|-------|
| IsHighRiskType = 1 cho TRANSFER va CASH_OUT | Chi 2 type nay co fraud |
| BalanceDropOrig la derived measure trong FactTransaction | Pattern full-drain la feature manh |
| isFlaggedFraud luu vao staging/fact nhung KHONG dung lam nhan | Chi co 16, khong tin cay |
| AccountType lay tu ky tu dau cua account ID | Nhat quan 100% trong du lieu |
| Merchant chi la tai khoan dich, khong la nguon | 100% nameOrig bat dau bang C |
| 6 amount bands: XS/S/M/L/XL/XXL | Phu hop phan phoi du lieu thuc |
| ETL can validate: amount>=0, type in domain, isFraud in {0,1} | Dat chuan chat luong |
| Balance mismatch KHONG loai don vi khi nap | La dac tinh du lieu mo phong |
