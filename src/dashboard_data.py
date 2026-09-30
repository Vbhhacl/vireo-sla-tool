from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
OUTPUTS = ROOT / "outputs"


def load_dashboard_data() -> dict[str, Any]:
    """Load compact reports and local detail data for server-side filtering."""
    tickets_path = DATA / "clean_tickets_with_roster.csv"
    if not tickets_path.exists():
        raise FileNotFoundError("Run `python -m src.pipeline` before launching Vireo Pulse.")
    tickets = pd.read_csv(tickets_path, parse_dates=["created_at", "first_response_at", "resolved_at", "created_at_ist", "first_response_at_ist", "week_start"])
    weekly = pd.read_csv(REPORTS / "weekly_report.csv", parse_dates=["week_start"])
    validation_path = DATA / "validation_report.json"
    roster_path = OUTPUTS / "roster_validation.json"
    ai_validation_path = OUTPUTS / "ai_validation.json"
    return {
        "tickets": tickets,
        "weekly": weekly,
        "validation": json.loads(validation_path.read_text(encoding="utf-8")) if validation_path.exists() else {},
        "roster": json.loads(roster_path.read_text(encoding="utf-8")) if roster_path.exists() else {},
        "ai_validation": json.loads(ai_validation_path.read_text(encoding="utf-8")) if ai_validation_path.exists() else {},
        "themes": pd.read_csv(OUTPUTS / "ai_theme_summary.csv") if (OUTPUTS / "ai_theme_summary.csv").exists() else pd.DataFrame(),
        "pipeline_mtime": max(path.stat().st_mtime for path in [tickets_path, REPORTS / "weekly_report.csv"]),
    }


def filter_tickets(tickets: pd.DataFrame, filters: dict[str, list[str]]) -> pd.DataFrame:
    """Apply one shared filter state to ticket-level data."""
    column_map = {
        "site": "roster_site",
        "shift": "roster_shift",
        "team": "roster_team",
        "channel": "channel",
        "priority": "priority",
    }
    mask = pd.Series(True, index=tickets.index)
    for filter_name, column in column_map.items():
        if filter_name in filters:
            selected = filters[filter_name]
            mask &= tickets[column].astype(str).isin(selected)
    return tickets.loc[mask].copy()


def kpi_metrics(tickets: pd.DataFrame) -> dict[str, float | int]:
    total = int(len(tickets))
    breaches = int(tickets["sla_breached"].fillna(False).astype(bool).sum())
    threshold = pd.to_numeric(tickets["sla_threshold_minutes"], errors="coerce")
    return {
        "tickets": total,
        "breaches": breaches,
        "breach_rate": breaches / total if total else 0.0,
        "credit_exposure_inr": breaches * 350,
        "median_response": float(tickets["response_minutes"].median()) if total else 0.0,
        "p90_response": float(tickets["response_minutes"].quantile(0.90)) if total else 0.0,
        "median_channel_threshold": float(threshold.median()) if total else 0.0,
    }


def weekly_analysis(tickets: pd.DataFrame) -> pd.DataFrame:
    if tickets.empty:
        return pd.DataFrame(columns=["week_start", "tickets", "breaches", "breach_rate", "median_response_minutes", "p90_response_minutes"])
    out = tickets.groupby("week_start", dropna=False).agg(
        tickets=("ticket_id", "count"),
        breaches=("sla_breached", "sum"),
        median_response_minutes=("response_minutes", "median"),
        p90_response_minutes=("response_minutes", lambda values: values.quantile(0.90)),
    ).reset_index()
    out["breach_rate"] = out["breaches"] / out["tickets"]
    return out.sort_values("week_start")


def shift_analysis(tickets: pd.DataFrame) -> pd.DataFrame:
    if tickets.empty:
        return pd.DataFrame(columns=["roster_shift", "tickets", "breaches", "breach_rate", "median_response_minutes", "p90_response_minutes"])
    out = tickets.groupby("roster_shift", dropna=False).agg(
        tickets=("ticket_id", "count"),
        breaches=("sla_breached", "sum"),
        median_response_minutes=("response_minutes", "median"),
        p90_response_minutes=("response_minutes", lambda values: values.quantile(0.90)),
    ).reset_index()
    out["breach_rate"] = out["breaches"] / out["tickets"]
    return out.sort_values("breaches", ascending=False)


def category_analysis(tickets: pd.DataFrame) -> pd.DataFrame:
    if tickets.empty:
        return pd.DataFrame(columns=["category", "tickets", "breaches", "breach_rate"])
    out = tickets.groupby("category", dropna=False).agg(tickets=("ticket_id", "count"), breaches=("sla_breached", "sum")).reset_index()
    out["breach_rate"] = out["breaches"] / out["tickets"]
    return out.sort_values("breaches", ascending=False)


def agent_week_matrix(tickets: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    columns = ["agent_id", "agent_name", "roster_site", "roster_team", "roster_shift", "week_start", "tickets", "breaches", "breach_rate", "median_response_minutes", "p90_response_minutes"]
    if tickets.empty:
        return pd.DataFrame(columns=columns), pd.DataFrame()
    grouped = tickets.groupby(["agent_id", "agent_name", "roster_site", "roster_team", "roster_shift", "week_start"], dropna=False).agg(
        tickets=("ticket_id", "count"),
        breaches=("sla_breached", "sum"),
        median_response_minutes=("response_minutes", "median"),
        p90_response_minutes=("response_minutes", lambda values: values.quantile(0.90)),
    ).reset_index()
    grouped["breach_rate"] = grouped["breaches"] / grouped["tickets"]
    matrix_rows = tickets.groupby(["agent_id", "agent_name", "week_start"], dropna=False).agg(
        tickets=("ticket_id", "count"), breaches=("sla_breached", "sum")
    ).reset_index()
    matrix_rows["breach_rate"] = matrix_rows["breaches"] / matrix_rows["tickets"]
    matrix = matrix_rows.pivot_table(index=["agent_id", "agent_name"], columns="week_start", values="breach_rate", aggfunc="first")
    return grouped[columns], matrix


def search_tickets(tickets: pd.DataFrame, query: str, breached_only: bool = False, category: str | None = None, limit: int = 200) -> pd.DataFrame:
    result = tickets
    if breached_only:
        result = result[result["sla_breached"].fillna(False).astype(bool)]
    if category and category != "All categories":
        result = result[result["category"].astype(str).eq(category)]
    term = query.strip().lower()
    if term:
        search_columns = ["ticket_id", "agent_id", "agent_name", "category", "customer_message", "agent_notes", "channel"]
        mask = pd.Series(False, index=result.index)
        for column in search_columns:
            mask |= result[column].fillna("").astype(str).str.lower().str.contains(term, regex=False)
        result = result[mask]
    return result.sort_values("created_at", ascending=False).head(limit).copy()


def build_ai_insight(tickets: pd.DataFrame, question: str) -> dict[str, Any]:
    """Build a deterministic evidence bundle; no generative model can invent metrics."""
    total = kpi_metrics(tickets)
    if tickets.empty:
        return {"headline": "No tickets match the active filters.", "evidence": [], "source_count": 0, "confidence": "No evidence"}
    shifts = shift_analysis(tickets)
    categories = category_analysis(tickets)
    channels = tickets.groupby("channel").agg(tickets=("ticket_id", "count"), breaches=("sla_breached", "sum")).reset_index()
    channels["breach_rate"] = channels["breaches"] / channels["tickets"]
    priorities = tickets.groupby("priority").agg(tickets=("ticket_id", "count"), breaches=("sla_breached", "sum")).reset_index()
    focus_shift = shifts.iloc[0]
    shift_share_breaches = float(focus_shift["breaches"] / total["breaches"]) if total["breaches"] else 0.0
    shift_share_volume = float(focus_shift["tickets"] / total["tickets"]) if total["tickets"] else 0.0
    focus_category = categories.iloc[0] if not categories.empty else None
    focus_channel = channels.sort_values("breaches", ascending=False).iloc[0] if not channels.empty else None
    question_lower = question.lower()
    if "transfer" in question_lower:
        transfer = tickets.assign(transfer_group=tickets["transfers"].fillna(0).gt(0).map({True: "Transferred", False: "Not transferred"})).groupby("transfer_group").agg(
            tickets=("ticket_id", "count"), breach_rate=("sla_breached", "mean"), median_response=("response_minutes", "median")
        ).reset_index()
        headline = "Transferred tickets can be compared with non-transferred tickets; this association does not establish causation."
        evidence = transfer.to_dict(orient="records")
    elif "increasing" in question_lower:
        trend = weekly_analysis(tickets)
        if len(trend) >= 8:
            baseline_rate = float(trend.head(4)["breach_rate"].mean())
            recent_rate = float(trend.tail(4)["breach_rate"].mean())
            change_pp = (recent_rate - baseline_rate) * 100
            direction = "increased" if change_pp > 0 else "decreased" if change_pp < 0 else "was unchanged"
            headline = f"The average weekly breach rate {direction} by {abs(change_pp):.1f} percentage points between the first and latest four observed weeks in this filtered view. This is descriptive, not causal."
            evidence = [{"period": "first four observed weeks", "breach_rate": baseline_rate}, {"period": "latest four observed weeks", "breach_rate": recent_rate}]
        else:
            headline = "Too few weekly observations in the current filtered view to assess a period trend."
            evidence = [{"observed_weeks": int(len(trend))}]
    elif "after june" in question_lower:
        maximum = pd.to_datetime(tickets["created_at"], utc=True).max()
        headline = f"The supplied dataset ends on {maximum:%d %b %Y}; there is no post-June period in these data to compare."
        evidence = [{"dataset_end": maximum.isoformat()}]
    else:
        headline = (
            f"{focus_shift['roster_shift']} accounts for {shift_share_breaches:.1%} of breaches "
            f"while handling {shift_share_volume:.1%} of tickets in the current view. "
            f"{focus_channel['channel'] if focus_channel is not None else 'No channel'} has the largest breach count."
        )
        evidence = [
            {"type": "shift", "name": str(focus_shift["roster_shift"]), "tickets": int(focus_shift["tickets"]), "breaches": int(focus_shift["breaches"]), "breach_rate": float(focus_shift["breach_rate"]), "share_of_breaches": shift_share_breaches, "share_of_tickets": shift_share_volume},
            {"type": "category", "name": str(focus_category["category"]), "tickets": int(focus_category["tickets"]), "breaches": int(focus_category["breaches"]), "breach_rate": float(focus_category["breach_rate"])} if focus_category is not None else {},
            {"type": "channel", "name": str(focus_channel["channel"]), "tickets": int(focus_channel["tickets"]), "breaches": int(focus_channel["breaches"]), "breach_rate": float(focus_channel["breach_rate"])} if focus_channel is not None else {},
            {"type": "priority", "distribution": priorities.to_dict(orient="records")},
        ]
    return {
        "headline": headline,
        "evidence": evidence,
        "source_count": int(total["tickets"]),
        "breach_count": int(total["breaches"]),
        "confidence": "Descriptive association; not causal",
    }