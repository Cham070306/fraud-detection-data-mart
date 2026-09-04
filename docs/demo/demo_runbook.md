# Demo Runbook — PaySim Fraud Detection Data Mart

**Purpose:** End-to-end demonstration for instructor/evaluator.
**Duration:** ~20 minutes (adjust per audience)

---

## Prerequisites

| Item | Requirement |
|---|---|
| Python | 3.11+ |
| SQL Server | 2019+ with ODBC Driver 17 |
| Dataset | `data/raw/PS_20174392719_1491204439457_log.csv` (493 MB) |
| DB | `FraudDW` already created (`sql/00` – `sql/08` run once) |
| `.env` | `FRAUD_DB_SERVER`, `FRAUD_DB_NAME`, `FRAUD_DB_USER`, `FRAUD_DB_PASSWORD` set |
| Virtual env | `pip install -r requirements.txt` |

---

## Demo Flow

### Step 0 — Show Project Overview (2 min)

Open `README.md` in browser/VS Code. Briefly explain:
- **Goal:** fraud detection data mart using PaySim synthetic transactions
- **Architecture:** CSV → SQL Server (Star Schema, 7 Dims + 3 Facts) → ML pipeline → BI dashboard
- **5 team roles** and what each contributed

---

### Step 1 — ETL Pipeline (3 min)

```bash
# Run ETL
python -m src.etl.run_etl
```

**Expected output:**
```
Pipeline hoan thanh: SUCCESS
{'batch_id': 7, 'status': 'SUCCESS', 'source_rows': 6362620,
 'valid_rows': 6362620, 'rejected_rows': 0, ...}
```

**Validation queries** (run in SQL Server Management Studio):
```sql
-- Row counts
SELECT 'stg', COUNT(*) FROM stg.TransactionRaw
UNION ALL
SELECT 'fact', COUNT(*) FROM fact.FactTransaction;
-- Both should show 6,362,620

-- Fraud count
SELECT COUNT(*) FROM fact.FactTransaction WHERE IsFraud = 1;
-- Expected: 8,213

-- Reconciliation
SELECT * FROM audit.ReconciliationLog ORDER BY ReconID DESC;
-- Status should be PASS
```

**Talking points:**
- 6.36M rows, 32 chunks, 0 rejected
- All 6 orphan FK checks = 0
- EDA comparison: 140/141 PASS (single float-precision delta)

---

### Step 2 — ML Training & Scoring (3 min)

```bash
# Train models
python scripts/train_model.py
# Score all transactions
python scripts/score_transactions.py
```

**Expected values (from saved metadata):**
- Model: Random Forest v1.0.0
- Threshold: 0.32
- Test confusion: TN 88,213 / FP 1 / FN 1 / TP 1,251
- Fraud amount capture rate: 99.98%
- Total alerts: 8,218 (HIGH + CRITICAL)

**Show model card:**
```
models/model_card.md
models/registry.json
```

**Talking points:**
- 3 models compared: Business Rule Baseline, Logistic Regression, Random Forest
- Temporal split avoids future leakage
- Threshold chosen at max F2 subject to Recall >= 0.80

---

### Step 3 — Streamlit Dashboard (7 min)

```bash
streamlit run dashboard/streamlit/app.py
```

Open browser to `http://localhost:8501`.

#### 3a. Overview (2 min)
- Show KPI cards: Volume, Amount, Fraud Count, Fraud Amount, Fraud Rate
- Point to fraud-by-type chart (CASH_OUT and TRANSFER are fraud types)
- Point to fraud-by-hour chart
- Demonstrate sidebar filters (adjust StepDay range → numbers update)

#### 3b. Alert Queue (3 min)
- Show summary strip: total alerts, confirmed, false positive, under investigation, open
- Show alert table (CRITICAL alerts first, sorted by score)
- **Demo the feedback loop:**
  1. Select an alert from the dropdown
  2. Choose "Confirmed Fraud", enter your name, submit
  3. Table refreshes — alert now shows `AnalystDecision = CONFIRMED_FRAUD`
  4. Summary strip updates: confirmed count increases
- This demonstrates the analyst feedback workflow

#### 3c. Model Performance (1 min)
- KPI cards: Precision, Recall, F2, PR-AUC
- Confusion matrix
- Risk policy legend
- Model registry table

#### 3d. Operations (1 min)
- ETL reconciliation rate (100%)
- Validation error rate (0.00%)
- Batch history
- Reject log (empty = clean ETL)

---

### Step 4 — FastAPI (2 min)

```bash
# In a separate terminal:
python -m uvicorn src.api.main:app --reload --port 8000
```

**Demo endpoints** (use browser or curl):
```
GET  http://localhost:8000/api/health
GET  http://localhost:8000/api/overview/kpis
GET  http://localhost:8000/api/alerts?risk_level=CRITICAL&limit=5
POST http://localhost:8000/api/alerts/{key}/feedback
```

Example POST:
```bash
curl -X POST http://localhost:8000/api/alerts/123/feedback \
  -H "Content-Type: application/json" \
  -d '{"decision":"CONFIRMED_FRAUD","comment":"demo","reviewed_by":"demo_user"}'
```

**Talking points:**
- API exposes same data as Streamlit — numbers reconcile
- RESTful contract for Power BI / external consumers

---

### Step 5 — Power BI (2 min)

Open `dashboard/FraudDetection.pbix` in Power BI Desktop (if available).
Otherwise show `dashboard/dashboard_spec.md` and describe the 5-page layout.

**Talking points:**
- 5 pages: Overview, Transaction Analysis, Model Performance, Alert Queue, ETL & DQ
- Drill-through configured on TransactionKey
- Data source: same SQL BI views as Streamlit
- `.pbix` built from `dashboard_spec.md`

---

### Step 6 — Recap & Q&A (3 min)

Key numbers to reinforce:
| Metric | Value |
|---|---|
| Total transactions | 6,362,620 |
| Fraud count | 8,213 (0.129%) |
| ML model | Random Forest v1.0.0 |
| Threshold | 0.32 |
| Test recall | 99.92% |
| Test capture rate | 99.98% |
| HIGH+CRITICAL alerts | 8,218 |
| ETL reconciliation | 100% |

Mention project structure: 122 files, full documentation, automated tests.

---

## Troubleshooting

| Issue | Solution |
|---|---|
| pyodbc not found | `pip install pyodbc`; install ODBC Driver 17 |
| CSV not found | Download from Kaggle, place in `data/raw/` |
| Streamlit won't start | `pip install streamlit plotly`; check `requirements.txt` |
| API won't start | `pip install fastapi uvicorn` |
| DB connection refused | Check `.env` values and SQL Server service is running |

---

## File Checklist (for instructor submission)

- [ ] `dashboard/FraudDetection.pbix` (built in Power BI Desktop)
- [ ] `dashboard/dashboard_spec.md` (this doc)
- [ ] `dashboard/streamlit/app.py` + `pages/*` + `components/filters.py`
- [ ] `docs/demo/demo_runbook.md` (this doc)
