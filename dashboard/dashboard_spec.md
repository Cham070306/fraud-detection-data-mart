# Power BI Dashboard Specification — PaySim Fraud Detection Data Mart

**Version:** 1.0.0
**Owner:** TV5 (BI / App Dev)
**Status:** Ready for build in Power BI Desktop
**Deliverable:** `dashboard/FraudDetection.pbix` (built manually from this spec)

---

## 1. Purpose

Spec for the Power BI dashboard for the PaySim Fraud Detection Data Mart. It has **5 pages**:

1. **Overview** — Executive transaction & fraud KPIs
2. **Transaction Analysis** — Drill-through to individual transactions
3. **Model Performance** — ML evaluation metrics
4. **Alert Queue** — HIGH/CRITICAL alerts + analyst feedback workflow
5. **ETL & DQ** — Pipeline reconciliation & validation quality

All numbers must reconcile with the SQL BI views so that Power BI, the Streamlit
dashboard, and the FastAPI service report identical values.

---

## 2. Source Data

- **Database:** `FraudDW` (SQL Server 2019+)
- **Mode:** Import (default), refresh manually or scheduled
- **Connection:** SQL Server + ODBC Driver 17
- **Source views** (each Power BI table maps to one view):

| Power BI table | Source view | Grain |
|---|---|---|
| `TransactionSummary` | `bi.vw_TransactionSummary` | per day × type |
| `TransactionAnalysis` | `bi.vw_TransactionAnalysis` | 1 row per transaction |
| `AlertQueue` | `bi.vw_AlertQueue` | 1 row per HIGH/CRITICAL alert |
| `AlertFeedback` | `bi.vw_AlertFeedback` | 1 row per alert (with decision) |
| `ETLQuality` | `bi.vw_ETLQualitySummary` | 1 row per ETL batch |

> **Refresh note:** PaySim `step` is *simulated time*, not a real calendar. Do not
> interpret dates as actual banking activity. `DimDate.DateKey` is derived from
> `2023-01-01 + (step-1) days`.

---

## 3. Data Model (Relationships)

Configure these relationships (hide join columns where not needed for filters):

| From | To | Cardinality | Filter |
|---|---|---|---|
| `TransactionAnalysis[TransactionKey]` | `AlertQueue[TransactionKey]` | 1:Many | Both |
| `TransactionAnalysis[TransactionKey]` | `AlertFeedback[TransactionKey]` | 1:Many | Both |
| `AlertQueue[AlertKey]` | `AlertFeedback[AlertKey]` | 1:1 | Both |
| `TransactionSummary[StepDay]` | `TransactionAnalysis[StepDay]` | Many:Many | Single |
| `AlertQueue[DateKey]` | `TransactionAnalysis[DateKey]` | Many:Many | Single |
| `ETLQuality` | (none — standalone) | — | — |

If many-to-many causes ambiguity, keep `TransactionSummary` standalone and filter
pages with explicit slicers on `StepDay` / `TypeCode` / `RiskLevel`.

---

## 4. DAX Measures

Store numeric values as decimals; format percent measures with `%` (multiply by 100
in format string, keep underlying value 0–1).

### Group 1 — Transaction KPIs
```dax
Total Volume = SUM(TransactionSummary[TransactionCount])
Total Amount = SUM(TransactionSummary[TotalAmount])
Fraud Count = SUM(TransactionSummary[FraudCount])
Fraud Amount = SUMX(TransactionSummary,
    TransactionSummary[FraudCount] * TransactionSummary[TotalAmount]
        / DIVIDE(TransactionSummary[TransactionCount], 1))
Fraud Rate (Volume) = DIVIDE([Fraud Count], [Total Volume])
Fraud Rate (Amount) = DIVIDE([Fraud Amount], [Total Amount])
```

### Group 2 — Model Performance KPIs
```dax
Model Precision = MAX(DimModelVersion[Precision])   -- from metadata or view
Model Recall = MAX(DimModelVersion[Recall])
Model F2 = MAX(DimModelVersion[F2Score])
Model PR-AUC = MAX(DimModelVersion[PrAUC])
Model Threshold = MAX(DimModelVersion[Threshold])
```
> For a static, authoritative test-set card, import `docs/integration/bi_model_handoff/model_performance.csv`
> and `confusion_matrix.csv` instead of computing from the sparse `FactModelScore`
> table (which is empty until TV2 loads scores). Label clearly as **TEST split**.

### Group 3 — Alert & Financial KPIs
```dax
Captured Fraud Loss Rate = DIVIDE(
    CALCULATE(SUM(TransactionAnalysis[Amount]), TransactionAnalysis[IsFraud] = 1),
    SUM(TransactionAnalysis[Amount]))
Alert Count = COUNT(AlertQueue[AlertKey])
Alert Amount = SUM(AlertQueue[Amount])
% Confirmed Fraud = DIVIDE(
    CALCULATE(COUNT(AlertFeedback[AlertKey]), AlertFeedback[AnalystDecision] = "CONFIRMED_FRAUD"),
    COUNT(AlertFeedback[AlertKey]))
% False Positive = DIVIDE(
    CALCULATE(COUNT(AlertFeedback[AlertKey]), AlertFeedback[AnalystDecision] = "FALSE_POSITIVE"),
    COUNT(AlertFeedback[AlertKey]))
```

### Group 4 — Data Quality KPIs
```dax
Reconciliation Rate = MAX(ETLQuality[ReconciliationRate])   -- target 100%
Validation Error Rate = MAX(ETLQuality[ValidationErrorRate]) -- target < 0.1%
```

---

## 5. Pages (visual-by-visual)

### Page 1 — Overview
- **KPI cards:** Total Volume, Total Amount, Fraud Count, Fraud Amount, Fraud Rate (Vol), Fraud Rate (Amt)
- **Line chart:** Fraud Count by StepDay
- **Bar chart:** Fraud Count by TypeCode
- **Bar chart:** Fraud Count by BandLabel (amount band)
- **Column chart:** Transaction Volume by TimeSlot
- **Slicers:** StepDay range, TypeCode multi-select

### Page 2 — Transaction Analysis
- **Filters:** StepDay, TypeCode, RiskLevel, IsFraud
- **Table:** TransactionKey, StepDay, HourOfDay, TypeCode, BandLabel, Amount, OrigAccountID, DestAccountID, IsFraud, FraudScore, RiskLevel
- **Matrix:** Fraud Count by TypeCode × Amount Band
- **Scatter/bubble:** FraudScore vs Amount (colored by RiskLevel)
- **Drill-through target:** configure `TransactionKey` as drill-through field → Transaction Detail page

### Page 3 — Model Performance
- **KPI cards:** Precision, Recall, F2, PR-AUC, Threshold, Capture Rate (**TEST split only**)
- **Matrix / table:** Confusion matrix (TN/FP/FN/TP) from `confusion_matrix.csv`
- **Table:** Risk policy legend (RiskLevel, Score Range, Alert?, Action)
- **Note text:** "Synthetic PaySim data — near-perfect metrics are not real banking performance"

### Page 4 — Alert Queue
- **Slicers:** RiskLevel, AlertStatus, AnalystDecision
- **Table:** AlertKey, TransactionKey, TypeCode, Amount, FraudScore, RiskLevel, AlertLevel, AlertStatus, RecommendedAction, AnalystDecision, ReviewedBy, ReviewedAt
- **Donut:** Alerts by RiskLevel
- **Stacked bar:** AlertStatus breakdown (Open / Confirmed / False Positive / Under Investigation)
- **Drill-through target:** AlertKey → Transaction Detail page
- **Feedback integration:** add a page-level note that feedback is captured in the Streamlit app and reflected here via `AlertFeedback`

### Page 5 — ETL & DQ
- **KPI cards:** Reconciliation Rate (target 100%), Validation Error Rate (target < 0.1%), Latest Batch ID, Batch Status
- **Table:** BatchID, SourceFileName, SourceRows, FactRows, ReconStatus, RejectCount, StartedAt, FinishedAt, DurationMinutes
- **Column chart:** RejectCount by BatchID

### Drill-through — Transaction Detail (shared)
- **Fields:** all columns of `TransactionAnalysis`
- **Entry points:** Transaction Analysis page (by TransactionKey), Alert Queue (by AlertKey → TransactionKey)
- **Visuals:** single-transaction card layout: amount, type, risk level, fraud score, account IDs, balances, balance drop

---

## 6. Feedback Integration

Analyst decisions are written by the Streamlit Alert Queue (or FastAPI
`POST /api/alerts/{key}/feedback`) into `fact.FactAlert`:
`AnalystDecision` + `AlertStatus` + `ReviewedBy` + `ReviewedAt`.

| Decision | AlertStatus | Dashboard effect |
|---|---|---|
| `CONFIRMED_FRAUD` | `RESOLVED` | Counts as confirmed in feedback visuals |
| `FALSE_POSITIVE` | `FALSE_POSITIVE` | Counts as false positive |
| `UNDER_INVESTIGATION` | `IN_REVIEW` | Counts as under investigation |
| (none) | `NEW` / `OPEN` | Counts as open |

The `AlertFeedback` view drives the feedback funnel and % measures above.

---

## 7. Acceptance Checks

Before publishing, verify:

- [ ] Total scores = **6,362,620** (`TransactionAnalysis` count)
- [ ] Total fraud = **8,213**
- [ ] HIGH+CRITICAL alerts = **8,218**
- [ ] Model v1.0.0 threshold = **0.32**
- [ ] Test confusion matrix: **TN 88,213 / FP 1 / FN 1 / TP 1,251**
- [ ] Reconciliation rate = **100%** (single ETL batch, 0 rejects)
- [ ] All 5 pages connect and refresh without error
- [ ] Drill-through from Alert Queue → Transaction Detail works via TransactionKey

---

## 8. Deployment

1. Open Power BI Desktop.
2. Get Data → SQL Server → `FraudDW` → select the 5 `bi.vw_*` views.
3. Build model relationships (Section 3), add measures (Section 4), layout pages (Section 5).
4. Save as `dashboard/FraudDetection.pbix`.
5. Optional: Publish to Power BI Service; schedule refresh.

> The `.pbix` is a binary produced in Power BI Desktop. This document is the
> engineering source-of-truth for its content; commit the spec, publish the binary.
