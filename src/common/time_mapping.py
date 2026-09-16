from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd


def derive_simulation_time(step: pd.Series, start_date: str) -> pd.DataFrame:
    """Map PaySim's one-based hourly step to consistent DW date/time keys."""
    numeric_step = pd.to_numeric(step, errors="raise").astype(int)
    hour_of_day = (numeric_step - 1) % 24
    step_day = ((numeric_step - 1) // 24) + 1
    base = datetime.strptime(start_date, "%Y-%m-%d")
    date_key = step_day.map(
        lambda day: int((base + timedelta(days=int(day) - 1)).strftime("%Y%m%d"))
    )
    return pd.DataFrame(
        {
            "StepRaw": numeric_step,
            "StepDay": step_day,
            "HourOfDay": hour_of_day,
            "DateKey": date_key,
            "TimeKey": hour_of_day,
        },
        index=step.index,
    )
