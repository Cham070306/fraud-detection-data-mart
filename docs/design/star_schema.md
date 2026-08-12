# Star Schema Technical Design
# PaySim Fraud Detection Data Mart

## 1. Muc tieu
Tai lieu nay chuyen hoa thiet ke nghiep vu trong docs/design/bus_matrix.md thanh thiet ke ky thuat de TV2 trien khai SQL va ETL.

## 2. Grain
- act.FactTransaction: 1 dong CSV = 1 giao dich PaySim
- act.FactModelScore: 1 ket qua score cho 1 giao dich, 1 model
- act.FactAlert: 1 canh bao cho 1 giao dich duoc xep HIGH/CRITICAL

## 3. Source-to-Target Mapping

| CSV Column | Target | Logic |
|------------|--------|-------|
| step | stg.StepRaw -> FactTransaction.StepRaw | gia tri goc |
| step | FactTransaction.DateKey | DateKey = 2023-01-01 + floor((step-1)/24) |
| step | FactTransaction.TimeKey | TimeKey = (step-1) % 24 |
| type | DimTransactionType.TypeCode | lookup by type |
| amount | FactTransaction.Amount | copy |
| amount | DimAmountBand | XS/S/M/L/XL/XXL |
| nameOrig | DimAccount.AccountID | OrigAccountKey |
| nameDest | DimAccount.AccountID | DestAccountKey |
| oldbalanceOrg | FactTransaction.OldBalanceOrig | copy |
| newbalanceOrig | FactTransaction.NewBalanceOrig | copy |
| oldbalanceDest | FactTransaction.OldBalanceDest | copy |
| newbalanceDest | FactTransaction.NewBalanceDest | copy |
| isFraud | FactTransaction.IsFraud | ground truth |
| isFlaggedFraud | FactTransaction.IsFlaggedFraud | source flag only |

## 4. Business Rules
- AccountType = ky tu dau cua AccountID (C/M)
- IsHighRiskType = 1 cho TRANSFER, CASH_OUT
- BalanceDropOrig = OldBalanceOrig - NewBalanceOrig
- RiskLevel map theo configs/risk_policy.yaml
- Chi tao alert cho HIGH, CRITICAL

## 5. Audit Strategy
- Staging luu BatchID + SourceFileName + RowNumberInChunk
- ETL log ghi source rows, valid rows, reject rows, load status
- Reconciliation doi soat row count va amount sum
