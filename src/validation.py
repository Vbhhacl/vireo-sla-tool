from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


EXPECTED_STATUS = {"open", "pending", "resolved", "closed"}
EXPECTED_CHANNELS = {"chat", "email", "voice", "social"}
EXPECTED_PRIORITIES = {"Low", "Normal", "High"}


def deduplicate_tickets(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    df["source_priority"] = df["source_system"].map({"helpdesk": 0, "legacy_fd": 1})
    df = df.sort_values(["ticket_id", "source_priority"], na_position="last")
    clean = df.drop_duplicates(subset="ticket_id", keep="first").drop(columns=["source_priority"])
    return clean.reset_index(drop=True)


def validate_dataset(raw_df: pd.DataFrame, clean_df: pd.DataFrame | None = None) -> dict[str, Any]:
    raw = raw_df.copy()
    clean = deduplicate_tickets(raw) if clean_df is None else clean_df.copy()

    report: dict[str, Any] = {
        "summary": {},
        "checks": [],
    }

    raw_duplicate_ids = raw[raw["ticket_id"].duplicated(keep=False)]["ticket_id"].nunique()
    report["checks"].append(
        {
            "name": "duplicate_ticket_ids",
            "passed": raw_duplicate_ids == 616,
            "details": {
                "duplicate_ticket_ids": int(raw_duplicate_ids),
                "duplicated_rows": int(raw[raw["ticket_id"].duplicated(keep=False)].shape[0]),
            },
        }
    )

    invalid_created = raw["created_at"].isna().sum()
    invalid_first_response = raw["first_response_at"].isna().sum()
    report["checks"].append(
        {
            "name": "invalid_timestamps",
            "passed": int(invalid_created) == 0 and int(invalid_first_response) == 0,
            "details": {"invalid_created_at": int(invalid_created), "invalid_first_response_at": int(invalid_first_response)},
        }
    )

    impossible_order = clean[clean["first_response_at"].notna() & clean["created_at"].notna()]
    impossible = ((pd.to_datetime(impossible_order["first_response_at"], utc=True) < pd.to_datetime(impossible_order["created_at"], utc=True)).sum())
    report["checks"].append(
        {
            "name": "first_response_before_created",
            "passed": int(impossible) == 0,
            "details": {"count": int(impossible)},
        }
    )

    invalid_resolution = clean["resolved_at"].isna().sum()
    report["checks"].append(
        {
            "name": "resolution_timestamp_validation",
            "passed": int(invalid_resolution) == 0,
            "details": {"missing_resolved_at": int(invalid_resolution)},
        }
    )

    missing_critical = [
        col for col in ["ticket_id", "created_at", "first_response_at", "status", "channel", "customer_id", "order_id", "product_sku", "category", "priority", "assigned_team", "agent_id"]
        if clean[col].isna().any()
    ]
    report["checks"].append(
        {
            "name": "missing_critical_fields",
            "passed": len(missing_critical) == 0,
            "details": {"columns_with_missing_values": missing_critical},
        }
    )

    status_invalid = set(clean[~clean["status"].isin(EXPECTED_STATUS)]["status"].dropna().unique())
    report["checks"].append({"name": "unexpected_status_values", "passed": len(status_invalid) == 0, "details": sorted(status_invalid)})

    channel_invalid = set(clean[~clean["channel"].isin(EXPECTED_CHANNELS)]["channel"].dropna().unique())
    report["checks"].append({"name": "unexpected_channel_values", "passed": len(channel_invalid) == 0, "details": sorted(channel_invalid)})

    priority_invalid = set(clean[~clean["priority"].isin(EXPECTED_PRIORITIES)]["priority"].dropna().unique())
    report["checks"].append({"name": "invalid_priority_values", "passed": len(priority_invalid) == 0, "details": sorted(priority_invalid)})

    csat_invalid = clean[clean["csat_score"].notna() & (~clean["csat_score"].between(1, 5, inclusive="both"))]
    report["checks"].append(
        {
            "name": "impossible_csat_values",
            "passed": csat_invalid.empty,
            "details": {"count": int(len(csat_invalid))},
        }
    )

    negative_refund = clean[clean["refund_amount_inr"].notna() & (clean["refund_amount_inr"] < 0)]
    report["checks"].append(
        {
            "name": "suspicious_negative_refund_values",
            "passed": negative_refund.empty,
            "details": {"count": int(len(negative_refund))},
        }
    )

    report["summary"] = {
        "raw_rows": int(len(raw)),
        "clean_rows": int(len(clean)),
        "duplicate_ticket_ids": int(raw_duplicate_ids),
        "unique_ticket_ids_clean": int(clean["ticket_id"].nunique()),
        "status": "pass" if all(check["passed"] for check in report["checks"]) else "warning",
    }
    return report


def write_validation_report(report: dict[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path
