from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from src.common.database import get_connection


REQUIRED_COLUMNS = {
    "TransactionKey", "DateKey", "Amount", "FraudScore", "PredictedFraud",
    "RiskLevel", "CreateAlert", "RecommendedAction", "ModelVersion",
    "PolicyVersion", "ScoredAt",
}

CREATE_TEMP_SQL = """
DROP TABLE IF EXISTS #ScoreInput;
CREATE TABLE #ScoreInput (
    TransactionKey BIGINT NOT NULL,
    DateKey INT NOT NULL,
    Amount DECIMAL(18,2) NOT NULL,
    FraudScore DECIMAL(7,6) NOT NULL,
    IsPredictedFraud BIT NOT NULL,
    RiskLevel VARCHAR(10) NOT NULL,
    CreateAlert BIT NOT NULL,
    RecommendedAction VARCHAR(30) NOT NULL,
    ModelVersion VARCHAR(10) NOT NULL,
    PolicyVersion VARCHAR(10) NOT NULL,
    ScoredAt DATETIME2 NOT NULL
);
"""

UPSERT_SCORES_SQL = """
IF EXISTS (
    SELECT 1 FROM #ScoreInput i
    LEFT JOIN fact.FactTransaction ft ON ft.TransactionKey = i.TransactionKey
    WHERE ft.TransactionKey IS NULL
)
    THROW 51020, 'Scoring input contains unknown TransactionKey values.', 1;

MERGE fact.FactModelScore WITH (HOLDLOCK) AS target
USING (
    SELECT i.*, mv.ModelVersionKey, rp.RiskPolicyKey
    FROM #ScoreInput i
    JOIN dim.DimModelVersion mv ON mv.Version = i.ModelVersion
    JOIN dim.DimRiskPolicy rp
      ON rp.PolicyVersion = i.PolicyVersion AND rp.RiskLevel = i.RiskLevel
) AS source
ON target.TransactionKey = source.TransactionKey
AND target.ModelVersionKey = source.ModelVersionKey
WHEN MATCHED THEN UPDATE SET
    RiskPolicyKey = source.RiskPolicyKey,
    DateKey = source.DateKey,
    FraudScore = source.FraudScore,
    RiskLevel = source.RiskLevel,
    RecommendedAction = source.RecommendedAction,
    IsPredictedFraud = source.IsPredictedFraud,
    ScoredAt = source.ScoredAt
WHEN NOT MATCHED THEN INSERT (
    TransactionKey, ModelVersionKey, RiskPolicyKey, DateKey, FraudScore,
    RiskLevel, RecommendedAction, IsPredictedFraud, ScoredAt
) VALUES (
    source.TransactionKey, source.ModelVersionKey, source.RiskPolicyKey,
    source.DateKey, source.FraudScore, source.RiskLevel,
    source.RecommendedAction, source.IsPredictedFraud, source.ScoredAt
);

MERGE fact.FactAlert WITH (HOLDLOCK) AS target
USING (
    SELECT ms.ScoreKey, i.TransactionKey, rp.RiskPolicyKey, i.DateKey,
           i.RiskLevel, i.FraudScore, i.Amount
    FROM #ScoreInput i
    JOIN dim.DimModelVersion mv ON mv.Version = i.ModelVersion
    JOIN dim.DimRiskPolicy rp
      ON rp.PolicyVersion = i.PolicyVersion AND rp.RiskLevel = i.RiskLevel
    JOIN fact.FactModelScore ms
      ON ms.TransactionKey = i.TransactionKey
     AND ms.ModelVersionKey = mv.ModelVersionKey
    WHERE i.CreateAlert = 1
) AS source
ON target.ScoreKey = source.ScoreKey
WHEN MATCHED THEN UPDATE SET
    TransactionKey = source.TransactionKey,
    RiskPolicyKey = source.RiskPolicyKey,
    DateKey = source.DateKey,
    AlertLevel = source.RiskLevel,
    FraudScore = source.FraudScore,
    AlertAmount = source.Amount
WHEN NOT MATCHED THEN INSERT (
    TransactionKey, ScoreKey, RiskPolicyKey, DateKey, AlertLevel,
    AlertStatus, FraudScore, AlertAmount
) VALUES (
    source.TransactionKey, source.ScoreKey, source.RiskPolicyKey,
    source.DateKey, source.RiskLevel, 'NEW', source.FraudScore, source.Amount
);
"""


def ensure_model_version(conn, metadata: dict) -> int:
    version = str(metadata["version"])
    model_name = str(metadata.get("model_name", "model"))
    metrics = metadata.get("test_metrics") or {}
    cur = conn.cursor()
    try:
        cur.execute("SELECT ModelVersionKey FROM dim.DimModelVersion WHERE Version = ?", version)
        row = cur.fetchone()
        if row:
            key = int(row[0])
            cur.execute(
                """
                UPDATE dim.DimModelVersion
                SET ModelName=?, Precision=?, Recall=?, F2Score=?, PrAUC=?, Threshold=?,
                    IsProduction=1, ModelFilePath=?
                WHERE ModelVersionKey=?
                """,
                model_name, metrics.get("precision"), metrics.get("recall"),
                metrics.get("f2"), metrics.get("pr_auc"), metadata.get("threshold"),
                f"models/fraud_model_v{version}.joblib", key,
            )
        else:
            cur.execute("SELECT ISNULL(MAX(ModelVersionKey), 0) + 1 FROM dim.DimModelVersion")
            key = int(cur.fetchone()[0])
            cur.execute(
                """
                INSERT INTO dim.DimModelVersion (
                    ModelVersionKey, ModelName, Version, Precision, Recall, F2Score,
                    PrAUC, Threshold, IsProduction, ModelFilePath
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                key, model_name, version, metrics.get("precision"), metrics.get("recall"),
                metrics.get("f2"), metrics.get("pr_auc"), metadata.get("threshold"),
                f"models/fraud_model_v{version}.joblib",
            )
        conn.commit()
        return key
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def ensure_risk_policy(conn, policy: dict) -> None:
    version = str(policy["policy_version"])
    cur = conn.cursor()
    try:
        for rule in policy["risk_levels"]:
            level = rule["level"].upper()
            cur.execute(
                """
                SELECT RiskPolicyKey FROM dim.DimRiskPolicy
                WHERE PolicyVersion=? AND RiskLevel=?
                """,
                version, level,
            )
            row = cur.fetchone()
            if row:
                cur.execute(
                    """
                    UPDATE dim.DimRiskPolicy
                    SET ScoreThresholdMin=?, ScoreThresholdMax=?, RecommendedAction=?,
                        EffectiveDate=?, IsActive=1
                    WHERE RiskPolicyKey=?
                    """,
                    rule["score_min"], rule["score_max"], rule["action"],
                    policy["effective_date"], int(row[0]),
                )
            else:
                cur.execute("SELECT ISNULL(MAX(RiskPolicyKey), 0) + 1 FROM dim.DimRiskPolicy")
                key = int(cur.fetchone()[0])
                cur.execute(
                    """
                    INSERT INTO dim.DimRiskPolicy (
                        RiskPolicyKey, PolicyVersion, RiskLevel, ScoreThresholdMin,
                        ScoreThresholdMax, RecommendedAction, EffectiveDate, IsActive
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    key, version, level, rule["score_min"], rule["score_max"],
                    rule["action"], policy["effective_date"],
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def normalize_chunk(frame: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(f"Scoring CSV is missing columns: {missing}")
    out = frame[list(REQUIRED_COLUMNS)].copy()
    out["TransactionKey"] = pd.to_numeric(out["TransactionKey"], errors="raise").astype("int64")
    out["DateKey"] = pd.to_numeric(out["DateKey"], errors="raise").astype(int)
    out["Amount"] = pd.to_numeric(out["Amount"], errors="raise").round(2)
    out["FraudScore"] = pd.to_numeric(out["FraudScore"], errors="raise")
    if not out["FraudScore"].between(0, 1).all():
        raise ValueError("FraudScore must be in [0, 1]")
    def to_bool(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)) and value in (0, 1):
            return bool(value)
        normalized = str(value).strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
        raise ValueError(f"Invalid boolean value: {value}")

    out["PredictedFraud"] = out["PredictedFraud"].map(to_bool)
    out["CreateAlert"] = out["CreateAlert"].map(to_bool)
    out["RiskLevel"] = out["RiskLevel"].astype(str).str.upper()
    out["ScoredAt"] = pd.to_datetime(out["ScoredAt"], utc=True).dt.tz_localize(None)
    return out.drop_duplicates(["TransactionKey", "ModelVersion"], keep="last")


def load_scoring_results(
    scores_path: str | Path,
    metadata_path: str | Path,
    policy_path: str | Path,
    chunk_size: int = 50_000,
) -> dict:
    metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
    policy = yaml.safe_load(Path(policy_path).read_text(encoding="utf-8"))
    conn = get_connection()
    total_input = 0
    expected_alerts = 0
    try:
        model_key = ensure_model_version(conn, metadata)
        ensure_risk_policy(conn, policy)
        for raw in pd.read_csv(scores_path, chunksize=chunk_size):
            frame = normalize_chunk(raw)
            if set(frame["ModelVersion"].astype(str)) != {str(metadata["version"])}:
                raise ValueError("Scoring CSV ModelVersion does not match metadata")
            if set(frame["PolicyVersion"].astype(str)) != {str(policy["policy_version"])}:
                raise ValueError("Scoring CSV PolicyVersion does not match risk policy")
            total_input += len(frame)
            expected_alerts += int(frame["CreateAlert"].sum())
            rows = [
                (
                    int(r.TransactionKey), int(r.DateKey), float(r.Amount),
                    float(r.FraudScore), int(r.PredictedFraud), str(r.RiskLevel),
                    int(r.CreateAlert), str(r.RecommendedAction), str(r.ModelVersion),
                    str(r.PolicyVersion), r.ScoredAt.to_pydatetime(),
                )
                for r in frame.itertuples(index=False)
            ]
            cur = conn.cursor()
            try:
                cur.execute(CREATE_TEMP_SQL)
                if hasattr(cur, "fast_executemany"):
                    cur.fast_executemany = True
                cur.executemany(
                    "INSERT INTO #ScoreInput VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    rows,
                )
                cur.execute(UPSERT_SCORES_SQL)
                while cur.nextset():
                    pass
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cur.close()

        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT_BIG(*) FROM fact.FactModelScore WHERE ModelVersionKey=?",
            model_key,
        )
        score_count = int(cur.fetchone()[0])
        cur.execute(
            """
            SELECT COUNT_BIG(*)
            FROM fact.FactAlert a
            JOIN fact.FactModelScore s ON s.ScoreKey=a.ScoreKey
            WHERE s.ModelVersionKey=?
            """,
            model_key,
        )
        alert_count = int(cur.fetchone()[0])
        cur.close()
        if score_count != total_input:
            raise RuntimeError(
                f"ML reconciliation failed: input={total_input}, scores={score_count}"
            )
        if alert_count != expected_alerts:
            raise RuntimeError(
                f"Alert reconciliation failed: input={expected_alerts}, alerts={alert_count}"
            )
        return {
            "model_version": metadata["version"],
            "input_rows": total_input,
            "score_rows": score_count,
            "alert_rows": alert_count,
            "status": "PASS",
        }
    finally:
        conn.close()
