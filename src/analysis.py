from __future__ import annotations

import pandas as pd


def weekly_report(df: pd.DataFrame) -> pd.DataFrame:
    report = df.groupby(["week_start", "roster_site", "roster_shift", "roster_team", "agent_id", "agent_name"], dropna=False).agg(
        tickets=("ticket_id", "count"),
        breaches=("sla_breached", "sum"),
        median_response_minutes=("response_minutes", "median"),
        p90_response_minutes=("response_minutes", lambda s: s.quantile(0.90)),
        average_response_minutes=("response_minutes", "mean"),
    ).reset_index()
    report["breach_rate"] = report["breaches"] / report["tickets"]
    report["week_start"] = pd.to_datetime(report["week_start"]).dt.strftime("%Y-%m-%d")
    return report


def agent_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = df.groupby(["agent_id", "agent_name", "roster_site", "roster_shift", "roster_team"], dropna=False).agg(
        tickets=("ticket_id", "count"),
        breaches=("sla_breached", "sum"),
        median_response_minutes=("response_minutes", "median"),
        p90_response_minutes=("response_minutes", lambda s: s.quantile(0.90)),
        average_response_minutes=("response_minutes", "mean"),
    ).reset_index()
    out["breach_rate"] = out["breaches"] / out["tickets"]
    return out.sort_values(["tickets", "breaches"], ascending=[False, False])


def shift_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = df.groupby(["roster_shift"], dropna=False).agg(
        tickets=("ticket_id", "count"),
        breaches=("sla_breached", "sum"),
        median_response_minutes=("response_minutes", "median"),
        p90_response_minutes=("response_minutes", lambda s: s.quantile(0.90)),
        average_response_minutes=("response_minutes", "mean"),
    ).reset_index()
    out["breach_rate"] = out["breaches"] / out["tickets"]
    return out


def business_impact(df: pd.DataFrame) -> pd.DataFrame:
    total_breaches = int(df["sla_breached"].sum())
    total_credits = total_breaches * 350
    return pd.DataFrame([
        {
            "metric": "breaches",
            "value": total_breaches,
        },
        {
            "metric": "estimated_sla_credit_inr",
            "value": total_credits,
        },
        {
            "metric": "breach_rate",
            "value": float(df["sla_breached"].mean()),
        },
    ])
