from __future__ import annotations

import numpy as np
import pandas as pd

SLA_RULES = {
    "chat": 15,
    "voice": 120,
    "social": 240,
    "email": 480,
}


def calculate_sla(tickets_df: pd.DataFrame) -> pd.DataFrame:
    df = tickets_df.copy()
    if "created_at" not in df.columns:
        raise ValueError("Expected created_at column in ticket data.")
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
    df["first_response_at"] = pd.to_datetime(df["first_response_at"], utc=True, errors="coerce")
    df["resolved_at"] = pd.to_datetime(df["resolved_at"], utc=True, errors="coerce")
    df["created_at_ist"] = df["created_at"].dt.tz_convert("Asia/Kolkata")
    df["first_response_at_ist"] = df["first_response_at"].dt.tz_convert("Asia/Kolkata")
    df["response_minutes"] = (df["first_response_at"] - df["created_at"]).dt.total_seconds() / 60
    df["sla_threshold_minutes"] = df["channel"].map(SLA_RULES)
    df["sla_breached"] = df["first_response_at"].notna() & (df["response_minutes"] > df["sla_threshold_minutes"])
    df["breach_minutes"] = np.where(df["sla_breached"], df["response_minutes"] - df["sla_threshold_minutes"], 0.0)
    naive_ist = df["created_at_ist"].dt.tz_localize(None)
    df["week_start"] = naive_ist.dt.to_period("W-MON").apply(lambda p: p.start_time).dt.tz_localize("Asia/Kolkata")
    df["roster_shift"] = df["roster_shift"].fillna("unknown")
    df["roster_site"] = df["roster_site"].fillna("unknown")
    df["roster_team"] = df["roster_team"].fillna("unknown")
    df["roster_tier"] = df["roster_tier"].fillna("unknown")
    return df
