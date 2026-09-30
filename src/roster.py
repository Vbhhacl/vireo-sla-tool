from __future__ import annotations

from typing import Any

import pandas as pd


def load_roster(path: str) -> pd.DataFrame:
    roster = pd.read_csv(path)
    roster["from_date"] = pd.to_datetime(roster["from_date"], errors="coerce")
    roster["to_date"] = pd.to_datetime(roster["to_date"], errors="coerce")
    return roster


def match_roster(tickets_df: pd.DataFrame, roster_df: pd.DataFrame) -> pd.DataFrame:
    df = tickets_df.copy()
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
    df["created_at_ist"] = df["created_at"].dt.tz_convert("Asia/Kolkata")
    roster = roster_df.copy()
    roster["from_dt"] = pd.to_datetime(roster["from_date"], utc=False).dt.tz_localize("Asia/Kolkata")
    roster["to_dt"] = pd.to_datetime(roster["to_date"], utc=False).dt.tz_localize("Asia/Kolkata")

    match_counts = []
    roster_site = []
    roster_shift = []
    roster_team = []
    roster_tier = []
    roster_agent_name = []
    roster_assignment_id = []
    roster_match_valid = []

    for row in df.itertuples():
        ticket_ts = row.created_at_ist
        matches = roster[
            (roster["agent_id"] == row.agent_id)
            & (ticket_ts >= roster["from_dt"])
            & ((roster["to_dt"].isna()) | (ticket_ts <= roster["to_dt"]))
        ]
        match_counts.append(len(matches))
        if len(matches) == 1:
            m = matches.iloc[0]
            roster_site.append(m["site"])
            roster_shift.append(m["shift"])
            roster_team.append(m["team"])
            roster_tier.append(m["tier"])
            roster_agent_name.append(m["name"])
            roster_assignment_id.append(f"{m['agent_id']}-{m['from_date'].date()}-{m['to_date'].date() if pd.notna(m['to_date']) else 'open'}")
            roster_match_valid.append(True)
        else:
            roster_site.append(None)
            roster_shift.append(None)
            roster_team.append(None)
            roster_tier.append(None)
            roster_agent_name.append(None)
            roster_assignment_id.append(None)
            roster_match_valid.append(False)

    df["roster_match_count"] = match_counts
    df["roster_valid_match"] = roster_match_valid
    df["roster_site"] = roster_site
    df["roster_shift"] = roster_shift
    df["roster_team"] = roster_team
    df["roster_tier"] = roster_tier
    df["roster_agent_name"] = roster_agent_name
    df["roster_assignment_id"] = roster_assignment_id
    return df


def roster_validation_report(df: pd.DataFrame) -> dict[str, Any]:
    zero_match = df[df["roster_valid_match"] == False]
    report = {
        "zero_match_cases": int(len(zero_match)),
        "multiple_match_cases": int((df["roster_match_count"] > 1).sum()),
        "unique_match_count_distribution": df["roster_match_count"].value_counts().sort_index().to_dict(),
        "zero_match_ticket_ids": zero_match["ticket_id"].tolist()[:20],
    }
    return report
