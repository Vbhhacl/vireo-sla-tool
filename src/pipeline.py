from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .ai_analysis import classify_sample, discover_themes, save_ai_report, validate_ai_output
from .analysis import agent_summary, business_impact, shift_summary, weekly_report
from .roster import load_roster, match_roster, roster_validation_report
from .sla import calculate_sla
from .validation import deduplicate_tickets, validate_dataset, write_validation_report

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
OUTPUTS_DIR = ROOT / "outputs"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def write_report_markdown(report: dict, path: Path) -> None:
    lines = [
        "# Validation Report",
        "",
        f"- Raw rows: {report['summary']['raw_rows']}",
        f"- Clean rows: {report['summary']['clean_rows']}",
        f"- Duplicate ticket IDs: {report['summary']['duplicate_ticket_ids']}",
        f"- Status: {report['summary']['status']}",
        "",
        "## Checks",
    ]
    for check in report["checks"]:
        lines.append(f"- {check['name']}: {'pass' if check['passed'] else 'warning'}")
        if check.get("details"):
            details = json.dumps(check["details"], sort_keys=True)
            lines.append(f"  - {details}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_memo(summary_df: pd.DataFrame, business_df: pd.DataFrame, validation_report: dict, roster_report: dict, ticket_df: pd.DataFrame) -> None:
    total_tickets = int(ticket_df["ticket_id"].nunique())
    total_breaches = int(business_df.loc[business_df["metric"] == "breaches", "value"].iloc[0])
    breach_rate = total_breaches / total_tickets if total_tickets else 0.0
    credit_total = int(business_df.loc[business_df["metric"] == "estimated_sla_credit_inr", "value"].iloc[0])
    shift_totals = ticket_df[ticket_df["roster_shift"].ne("unknown")].groupby("roster_shift").agg(
        tickets=("ticket_id", "count"), breaches=("sla_breached", "sum")
    )
    focus_shift = shift_totals["breaches"].idxmax() if not shift_totals.empty else "unavailable"
    focus = shift_totals.loc[focus_shift] if focus_shift != "unavailable" else None
    focus_rate = float(focus["breaches"] / focus["tickets"]) if focus is not None and focus["tickets"] else 0.0
    focus_share = float(focus["breaches"] / total_breaches) if focus is not None and total_breaches else 0.0
    focus_channel = "not available"
    if focus is not None:
        channel_totals = ticket_df.loc[ticket_df["roster_shift"].eq(focus_shift)].groupby("channel")["sla_breached"].sum()
        if not channel_totals.empty:
            focus_channel = str(channel_totals.idxmax())

    target_rate = 0.15
    weekly_volume = 650
    quarter_weeks = 13
    quarterly_tickets = weekly_volume * quarter_weeks
    quarterly_exposure_reduction = max(0.0, (breach_rate - target_rate) * quarterly_tickets * 350)
    summary = validation_report.get("summary", {})
    zero_matches = int(roster_report.get("zero_match_cases", 0))
    multiple_matches = int(roster_report.get("multiple_match_cases", 0))
    warning_names = [check["name"] for check in validation_report.get("checks", []) if not check.get("passed", True)]
    warning_text = ", ".join(warning_names) if warning_names else "no failed data-quality checks"
    memo_path = REPORTS_DIR / "memo.md"
    memo_text = f"""# First-Response SLA: Operations Decision Memo

**To:** Neha Kulkarni

**Subject:** Pilot Morning-shift queue balancing before adding headcount

## Decision in brief
The cleaned dataset contains **{total_tickets:,} tickets** and **{total_breaches:,} first-response breaches ({breach_rate:.1%})**. The {focus_shift} shift carries the largest recorded burden: **{int(focus['breaches']):,} breaches among {int(focus['tickets']):,} tickets ({focus_rate:.1%} rate; {focus_share:.1%} of all breaches)**. Within that shift, **{focus_channel}** has the largest breach count. This shows concentration, not proof that shift or channel caused each breach.

## Business goal and value scenario
Proposed pilot goal: lower the overall breach rate from **{breach_rate:.1%} to 15%** by rebalancing queue intake and shift handoff, then compare the same measure after four weeks. The 15% is a management test target—not a threshold inferred by the dataset. At about **650 tickets/week**, a quarter is **650 x 13 = {quarterly_tickets:,} tickets**. If the target were sustained, the policy-based exposure reduction would be approximately **({breach_rate:.1%} - 15%) x {quarterly_tickets:,} x Rs 350 = Rs {quarterly_exposure_reduction:,.0f} per quarter**. This is potential credit exposure, not verified cash savings.

## Recommended action
Run a four-week queue-balancing pilot focused on {focus_shift} {focus_channel} work: review arrival/backlog timing, agree an overflow trigger with the adjacent shift, and monitor weekly breach rate and volume. Keep current staffing during the test; review staffing only after measuring demand and handoff effects. Do not use the agent table as a punitive ranking.

## Confidence and caveats
SLA thresholds and the Rs 350 credit rule come from the supplied support policy. The pipeline deduplicates {int(summary.get('duplicate_ticket_ids', 0)):,} repeated ticket IDs and reports roster mismatches ({zero_matches} zero-match; {multiple_matches} multiple-match). Data-quality checks requiring review: {warning_text}. The theme model is exploratory and has no human-labeled accuracy score; read examples before acting. Credit exposure assumes the policy applies to every breach and is not an audited payout total. Re-run the pipeline when the source data changes.
"""
    memo_path.write_text(memo_text, encoding="utf-8")


def run_pipeline() -> dict:
    ensure_dirs()
    raw = pd.read_csv(DATA_DIR / "tickets.csv")
    clean = deduplicate_tickets(raw)
    validation = validate_dataset(raw, clean)
    write_validation_report(validation, DATA_DIR / "validation_report.json")
    write_report_markdown(validation, REPORTS_DIR / "validation_report.md")

    roster = load_roster(str(DATA_DIR / "agents.csv"))
    assigned = match_roster(clean, roster)
    roster_report = roster_validation_report(assigned)
    (OUTPUTS_DIR / "roster_validation.json").write_text(json.dumps(roster_report, indent=2), encoding="utf-8")
    assigned["agent_name"] = assigned["agent_id"].map(
        roster[["agent_id", "name"]].drop_duplicates().set_index("agent_id")["name"]
    )

    sla_df = calculate_sla(assigned)
    clean.to_csv(DATA_DIR / "clean_tickets.csv", index=False)
    sla_df.to_csv(DATA_DIR / "clean_tickets_with_roster.csv", index=False)

    weekly = weekly_report(sla_df)
    weekly.to_csv(REPORTS_DIR / "weekly_report.csv", index=False)

    agent = agent_summary(sla_df)
    agent.to_csv(REPORTS_DIR / "agent_summary.csv", index=False)

    shift = shift_summary(sla_df)
    shift.to_csv(REPORTS_DIR / "shift_summary.csv", index=False)

    business = business_impact(sla_df)
    business.to_csv(REPORTS_DIR / "business_metrics.csv", index=False)

    ai_sample = classify_sample(sla_df, sample_size=80)
    ai_sample.to_csv(OUTPUTS_DIR / "ai_sample.csv", index=False)
    ai_themes = discover_themes(sla_df)
    ai_themes.to_csv(OUTPUTS_DIR / "ai_theme_summary.csv", index=False)
    ai_report = validate_ai_output(ai_sample)
    ai_report["text_rows_analyzed_for_themes"] = int(ai_themes["tickets"].sum()) if not ai_themes.empty else 0
    ai_report["text_rows_excluded_from_themes"] = int(sla_df["customer_message"].notna().sum() - ai_report["text_rows_analyzed_for_themes"])
    ai_report["theme_count"] = int(len(ai_themes))
    save_ai_report(ai_report, OUTPUTS_DIR / "ai_validation.json")

    write_memo(weekly, business, validation, roster_report, sla_df)

    return {
        "clean_rows": len(clean),
        "validation": validation,
        "roster": roster_report,
        "weekly_report": weekly,
        "agent_summary": agent,
        "shift_summary": shift,
        "business_impact": business,
        "ai_report": ai_report,
        "ai_themes": ai_themes,
    }


if __name__ == "__main__":
    run_pipeline()
    print("Pipeline complete")
