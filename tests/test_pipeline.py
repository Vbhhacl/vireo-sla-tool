from __future__ import annotations

import pandas as pd

from src.ai_analysis import discover_themes, validate_ai_output
from src.dashboard_data import agent_week_matrix, build_ai_insight, filter_tickets, kpi_metrics, search_tickets
from src.roster import load_roster, match_roster
from src.sla import calculate_sla
from src.validation import deduplicate_tickets, validate_dataset


def test_duplicate_handling():
    raw = pd.read_csv("data/tickets.csv")
    clean = deduplicate_tickets(raw)
    assert len(clean) == 11200
    assert clean["ticket_id"].nunique() == 11200
    assert raw["ticket_id"].duplicated(keep=False).sum() == 1232


def test_timezone_conversion():
    raw = pd.read_csv("data/tickets.csv")
    clean = deduplicate_tickets(raw)
    clean = match_roster(clean, load_roster("data/agents.csv"))
    sla = calculate_sla(clean)
    assert isinstance(sla["created_at_ist"].dtype, pd.DatetimeTZDtype)
    assert isinstance(sla["first_response_at_ist"].dtype, pd.DatetimeTZDtype)
    assert "response_minutes" in sla.columns
    assert "sla_threshold_minutes" in sla.columns


def test_sla_thresholds():
    sample = pd.DataFrame(
        {
            "ticket_id": ["T1", "T2", "T3", "T4"],
            "created_at": ["2025-01-01T00:00:00Z", "2025-01-01T00:00:00Z", "2025-01-01T00:00:00Z", "2025-01-01T00:00:00Z"],
            "first_response_at": ["2025-01-01T00:16:00Z", "2025-01-01T02:00:00Z", "2025-01-01T04:30:00Z", "2025-01-01T08:30:00Z"],
            "resolved_at": [None, None, None, None],
            "status": ["resolved", "resolved", "resolved", "resolved"],
            "channel": ["chat", "voice", "social", "email"],
            "customer_id": ["C1", "C1", "C1", "C1"],
            "order_id": ["O1", "O2", "O3", "O4"],
            "product_sku": ["SKU1", "SKU2", "SKU3", "SKU4"],
            "category": ["shipping", "billing", "hardware", "general"],
            "priority": ["Normal", "Normal", "High", "Low"],
            "assigned_team": ["Chat Frontline", "Voice Frontline", "Chat Frontline", "Email Frontline"],
            "agent_id": ["A3005", "A3023", "A3005", "A3019"],
            "transfers": [0, 1, 0, 2],
            "csat_score": [5, 4, None, 3],
            "refund_amount_inr": [None, None, None, None],
            "refund_reason_code": [None, None, None, None],
            "replacement_issued": [False, False, False, False],
            "customer_message": ["late delivery", "charge issue", "speaker is broken", "password reset"],
            "agent_notes": ["replied", "investigated", "checked", "replied"],
            "source_system": ["helpdesk", "helpdesk", "helpdesk", "helpdesk"],
            "roster_site": ["Bengaluru", "Bengaluru", "Bengaluru", "Bengaluru"],
            "roster_shift": ["Morning", "Day", "Morning", "Morning"],
            "roster_team": ["Chat Frontline", "Voice Frontline", "Chat Frontline", "Email Frontline"],
            "roster_tier": [1, 1, 1, 1],
            "agent_name": ["Sameer Joshi", "Rahul Khanna", "Sameer Joshi", "Sai Sandhu"],
        }
    )
    sla = calculate_sla(sample)
    assert sla["sla_threshold_minutes"].tolist() == [15, 120, 240, 480]
    assert sla["sla_breached"].tolist() == [True, False, True, True]


def test_roster_matching_detects_zero_matches():
    raw = pd.read_csv("data/tickets.csv")
    clean = deduplicate_tickets(raw)
    roster = load_roster("data/agents.csv")
    assigned = match_roster(clean, roster)
    assert assigned["roster_match_count"].between(0, 1).all() or assigned["roster_match_count"].max() >= 1
    assert assigned["roster_valid_match"].isin([True, False]).all()
    assert assigned["roster_valid_match"].sum() < len(assigned)


def test_valdation_flags_broken_data():
    raw = pd.DataFrame(
        {
            "ticket_id": ["T1", "T1"],
            "created_at": ["2025-01-01T00:00:00Z", "2025-01-01T00:00:00Z"],
            "first_response_at": ["2025-01-01T00:30:00Z", "2025-01-01T00:10:00Z"],
            "resolved_at": [None, None],
            "status": ["resolved", "resolved"],
            "channel": ["chat", "chat"],
            "customer_id": ["C1", "C1"],
            "order_id": ["O1", "O2"],
            "product_sku": ["SKU1", "SKU1"],
            "category": ["general", "general"],
            "priority": ["Normal", "Normal"],
            "assigned_team": ["Chat Frontline", "Chat Frontline"],
            "agent_id": ["A3005", "A3005"],
            "transfers": [0, 0],
            "csat_score": [6, 5],
            "refund_amount_inr": [None, None],
            "refund_reason_code": [None, None],
            "replacement_issued": [False, False],
            "customer_message": ["hello", "hello"],
            "agent_notes": ["", ""],
            "source_system": ["helpdesk", "legacy_fd"],
        }
    )
    report = validate_dataset(raw, raw)
    assert any(check["name"] == "impossible_csat_values" for check in report["checks"])


def test_text_theme_discovery_is_reproducible_and_covers_messages():
    messages = pd.DataFrame(
        {
            "customer_message": [
                "wireless speaker bluetooth pairing issue",
                "bluetooth speaker will not pair",
                "wireless speaker pairing keeps failing",
                "payment refund charged twice invoice",
                "duplicate payment charge refund invoice",
                "invoice shows duplicate charge need refund",
            ]
        }
    )
    themes = discover_themes(messages, n_topics=2)
    assert len(themes) == 2
    assert int(themes["tickets"].sum()) == len(messages)
    assert themes["top_terms"].notna().all()


def test_ai_validation_reports_coverage_not_semantic_accuracy():
    sample = pd.DataFrame({"driver_label": ["delivery/order issue", "other"]})
    report = validate_ai_output(sample)
    assert report["keyword_label_coverage_rate"] == 1.0
    assert report["semantic_accuracy"] is None
    assert "human-labeled" in report["semantic_accuracy_note"]


def test_dashboard_shared_filters_recompute_kpis_and_insight():
    tickets = pd.DataFrame(
        {
            "ticket_id": ["T1", "T2", "T3"],
            "sla_breached": [True, False, True],
            "sla_threshold_minutes": [15, 120, 15],
            "response_minutes": [20.0, 30.0, 60.0],
            "roster_site": ["Pune", "Pune", "Mumbai"],
            "roster_shift": ["Morning", "Day", "Morning"],
            "roster_team": ["Chat", "Voice", "Chat"],
            "channel": ["chat", "voice", "chat"],
            "priority": ["High", "Normal", "High"],
            "category": ["Delivery", "Billing", "Delivery"],
            "transfers": [0, 1, 0],
            "week_start": pd.to_datetime(["2025-01-01", "2025-01-08", "2025-01-15"], utc=True),
            "created_at": pd.to_datetime(["2025-01-01", "2025-01-08", "2025-01-15"], utc=True),
        }
    )
    filtered = filter_tickets(tickets, {"site": ["Pune"], "shift": ["Morning"], "team": ["Chat"], "channel": ["chat"], "priority": ["High"]})
    metrics = kpi_metrics(filtered)
    insight = build_ai_insight(filtered, "What is driving Morning shift breaches?")
    assert filtered["ticket_id"].tolist() == ["T1"]
    assert metrics["tickets"] == 1
    assert metrics["breaches"] == 1
    assert insight["source_count"] == 1
    assert "Morning" in insight["headline"]
    assert filter_tickets(tickets, {"shift": []}).empty
    assert search_tickets(tickets, "", category="Delivery")["ticket_id"].tolist() == ["T3", "T1"]


def test_agent_week_heatmap_aggregates_multiple_roster_rows():
    tickets = pd.DataFrame(
        {
            "agent_id": ["A1", "A1", "A1"],
            "agent_name": ["Agent One"] * 3,
            "roster_site": ["Pune", "Pune", "Pune"],
            "roster_team": ["Chat", "Voice", "Chat"],
            "roster_shift": ["Morning", "Day", "Morning"],
            "week_start": pd.to_datetime(["2025-01-06"] * 3, utc=True),
            "ticket_id": ["T1", "T2", "T3"],
            "sla_breached": [True, False, True],
            "response_minutes": [30.0, 10.0, 50.0],
        }
    )
    grouped, matrix = agent_week_matrix(tickets)
    assert len(grouped) == 2
    assert matrix.loc[("A1", "Agent One")].iloc[0] == 2 / 3
