from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from .dashboard_data import (
    agent_week_matrix,
    build_ai_insight,
    category_analysis,
    filter_tickets,
    kpi_metrics,
    load_dashboard_data,
    search_tickets,
    shift_analysis,
    weekly_analysis,
)

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
PAGES = ["Command Center", "SLA Timeline", "Shift Intelligence", "Agent Lens", "Ticket Explorer", "AI Insights", "Data Quality"]
FILTER_KEYS = {"Site": "selected_site", "Shift": "selected_shift", "Team": "selected_team", "Channel": "selected_channel", "Priority": "selected_priority"}


@st.cache_data(show_spinner=False)
def cached_dashboard_data(pipeline_mtime: float) -> dict[str, Any]:
    """Cache loaded source data until the pipeline regenerates its reports."""
    del pipeline_mtime
    return load_dashboard_data()


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        :root { color-scheme: dark; }
        .stApp { background: radial-gradient(ellipse at 78% -18%, rgba(40,91,111,.19), transparent 38%), #0b0f13; color: #e7edf1; }
        [data-testid="stHeader"] { background: rgba(11,15,19,.88); border-bottom: 1px solid #202a31; }
        [data-testid="stSidebar"] { background: #0d1217; border-right: 1px solid #1e2a31; width:260px !important; min-width:260px !important; max-width:260px !important; }
        [data-testid="stSidebar"] > div:first-child { padding-top: 1.2rem; }
        h1,h2,h3 { letter-spacing: -.035em; }
        h1 { font-size: 2rem !important; }
        h2 { font-size: 1.38rem !important; }
        h3 { font-size: 1rem !important; color: #c7d3d9; }
        p, label, [data-testid="stCaptionContainer"] { color: #9aaab3; }
        [data-testid="stMetric"] { background: linear-gradient(145deg, rgba(24,34,41,.92), rgba(17,24,29,.82)); border: 1px solid #26333a; padding: .8rem 1rem; border-radius: 10px; }
        [data-testid="stMetricLabel"] { color: #96a7b0; font-size: .78rem; }
        [data-testid="stMetricValue"] { color: #f2f6f7; font-variant-numeric: tabular-nums; }
        [data-testid="stVerticalBlockBorderWrapper"] { border-color: #253138 !important; background: rgba(19,27,32,.72); }
        div[data-testid="stPlotlyChart"] { border: 1px solid #222f36; border-radius: 10px; background: #10171b; overflow: hidden; }
        [data-baseweb="select"] > div, [data-baseweb="input"] > div { background: #11191e; border-color: #2b3941; }
        button[kind="secondary"] { border: 1px solid #2b3b43; color: #dce5e9; background: #121a1f; }
        button[kind="secondary"]:hover { border-color: #60c5bd; color: #9be5dd; }
        [data-testid="stDataFrame"] { border: 1px solid #26343b; border-radius: 8px; }
        .brand { font-size: 1rem; line-height: 1.12; font-weight: 800; letter-spacing: .16em; color: #e6f0f1; }
        .brand span { color: #65d4c8; }
        .brand-sub { margin-top: .42rem; color: #81939c; font-size: .68rem; line-height: 1.45; letter-spacing: .04em; }
        .eyebrow { color: #75d6cb; font-size: .68rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; }
        .topline { display:flex; justify-content:space-between; align-items:center; gap:1rem; padding:.2rem 0 1rem; border-bottom:1px solid #202a31; margin-bottom:1.25rem; }
        .live { color:#8fe2d4; font-size:.72rem; letter-spacing:.1em; font-weight:700; }
        .live i { display:inline-block; width:7px; height:7px; margin-right:7px; border-radius:50%; background:#61d7a8; box-shadow:0 0 12px rgba(97,215,168,.55); }
        .hero { display:grid; grid-template-columns:1fr 180px; gap:1rem; align-items:center; padding:1.5rem 1.7rem; border-radius:12px; border:1px solid #2b4048; background:linear-gradient(112deg,rgba(21,39,45,.98),rgba(16,25,30,.96) 62%,rgba(23,43,45,.92)); box-shadow:inset 0 1px rgba(255,255,255,.025); }
        .hero-value { color:#effafa; font-size:clamp(3rem,7vw,5rem); line-height:1; font-weight:750; letter-spacing:-.07em; font-variant-numeric:tabular-nums; animation:rise .65s ease-out; }
        .hero-label { color:#c0d0d4; font-size:.92rem; margin:.35rem 0 .7rem; }
        .hero-meta { color:#8fa3aa; font-size:.76rem; }
        .pulse-ring { width:132px; height:132px; margin:auto; border-radius:50%; display:grid; place-items:center; background:conic-gradient(#63d5c8 var(--progress),#2b3d42 0); box-shadow:0 0 26px rgba(69,205,194,.11); }
        .pulse-inner { width:110px; height:110px; border-radius:50%; display:grid; place-items:center; align-content:center; background:#122027; color:#89dfd5; font-size:.66rem; font-weight:700; letter-spacing:.08em; text-align:center; }
        .pulse-inner strong { font-size:1.22rem; letter-spacing:0; color:#f0f7f7; margin-bottom:3px; }
        .status-line { margin-top:1.1rem; display:flex; justify-content:space-between; gap:1rem; color:#cfdbdf; font-size:.75rem; }
        .status-attention { color:#eac27a; }
        .panel { border:1px solid #25343b; border-radius:10px; padding:1rem 1.05rem; background:linear-gradient(145deg,rgba(19,28,33,.9),rgba(14,20,24,.87)); }
        .lane { min-height:250px; padding:1rem; border:1px solid #29363c; border-radius:10px; background:linear-gradient(160deg,rgba(25,40,44,var(--intensity)),rgba(16,23,27,.97) 70%); }
        .lane-name { letter-spacing:.14em; color:#cfdbde; font-size:.72rem; font-weight:800; }
        .lane-rate { font-size:2.2rem; line-height:1.1; font-weight:740; color:#f3f7f6; margin:.9rem 0 .25rem; }
        .lane-meta { color:#91a1a7; font-size:.74rem; line-height:1.9; }
        .lane-track { height:3px; border-radius:5px; background:#243238; margin:.8rem 0; }
        .lane-fill { height:3px; border-radius:5px; background:linear-gradient(90deg,#43bcb2,#e5aa60); }
        .health-stage { border:1px solid #26343a; border-radius:8px; padding:.8rem .9rem; min-height:110px; background:#11191d; }
        .health-stage b { display:block; color:#d8e2e5; font-size:.72rem; letter-spacing:.08em; }
        .health-stage strong { display:block; margin:.45rem 0 .2rem; color:#f1f5f5; font-size:1.2rem; }
        .health-stage small { color:#899ca4; }
        .health-good { color:#69d5a9 !important; }
        .health-warn { color:#e5b861 !important; }
        .filter-chip { display:inline-block; margin:.1rem .35rem .4rem 0; padding:.22rem .52rem; border:1px solid #34464e; border-radius:20px; color:#a9c0c3; font-size:.66rem; letter-spacing:.04em; }
        .quiet { color:#81939a; font-size:.75rem; }
        @keyframes rise { from { opacity:.25; transform:translateY(7px); } to { opacity:1; transform:translateY(0); } }
        @media(max-width:760px) { .hero { grid-template-columns:1fr; } .pulse-ring { display:none; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def configure_plot(fig: go.Figure, height: int = 330) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#9fb0b6", "family": "Inter, sans-serif", "size": 11},
        margin={"l": 20, "r": 22, "t": 25, "b": 25},
        hoverlabel={"bgcolor": "#172329", "bordercolor": "#40565d", "font": {"color": "#eef5f4"}},
        legend={"orientation": "h", "y": 1.12, "x": 0, "font": {"size": 10}},
    )
    fig.update_xaxes(gridcolor="#202d33", zerolinecolor="#28373d", linecolor="#28373d")
    fig.update_yaxes(gridcolor="#202d33", zerolinecolor="#28373d", linecolor="#28373d")
    return fig


def timeline_figure(tickets: pd.DataFrame, title: str = "Weekly SLA timeline") -> go.Figure:
    weekly = weekly_analysis(tickets)
    fig = go.Figure()
    if not weekly.empty:
        fig.add_trace(go.Scatter(
            x=weekly["week_start"], y=weekly["breach_rate"] * 100,
            customdata=weekly[["tickets", "breaches", "median_response_minutes", "p90_response_minutes"]],
            mode="lines+markers", name="Breach rate", line={"color": "#64d5ca", "width": 2.5, "shape": "spline"},
            marker={"size": 5, "color": "#8be2d9"},
            hovertemplate="%{x|%d %b %Y}<br>Rate %{y:.1f}%<br>Tickets %{customdata[0]}<br>Breaches %{customdata[1]}<br>Median %{customdata[2]:.0f} min<br>P90 %{customdata[3]:.0f} min<extra></extra>",
        ))
        spike_cutoff = float(weekly["breach_rate"].quantile(.95))
        spikes = weekly[weekly["breach_rate"].ge(spike_cutoff)]
        fig.add_trace(go.Scatter(
            x=spikes["week_start"], y=spikes["breach_rate"] * 100, mode="markers", name="High-rate week",
            marker={"color": "#e4a55c", "size": 9, "line": {"color": "#211b13", "width": 1}},
            hovertemplate="High-rate week · %{x|%d %b %Y}<br>Breach rate %{y:.1f}%<extra></extra>",
        ))
        fig.add_hline(y=15, line_dash="dot", line_color="#d0a75f", opacity=.8, annotation_text="Proposed pilot goal · 15%", annotation_position="top left", annotation_font_color="#d6b46f")
    fig.update_layout(title={"text": title, "font": {"size": 13, "color": "#d9e3e5"}}, xaxis_title=None, yaxis_title="Breach rate (%)", clickmode="event+select")
    return configure_plot(fig, 350)


def set_pending_shift(shift: str) -> None:
    st.session_state["pending_shift"] = shift


def handle_command() -> None:
    query = st.session_state.get("command_search", "").strip()
    if not query:
        return
    lowered = query.lower()
    for page in PAGES:
        if lowered in page.lower():
            st.session_state["active_page"] = page
            return
    if "morning" in lowered or "day" in lowered or "night" in lowered:
        shift = next(name for name in ["Morning", "Day", "Night"] if name.lower() in lowered)
        st.session_state["selected_shift"] = shift
        st.session_state["active_page"] = "Command Center"
        return
    if lowered.startswith("tk-"):
        st.session_state["ticket_query"] = query
        st.session_state["active_page"] = "Ticket Explorer"


def advance_demo_tour(page: str) -> None:
    current = PAGES.index(page) if page in PAGES else 0
    st.session_state["pending_demo_page"] = PAGES[(current + 1) % len(PAGES)]


def reset_global_filters() -> None:
    for key in FILTER_KEYS.values():
        st.session_state[key] = "All"


def render_sidebar(data: dict[str, Any], tickets: pd.DataFrame) -> str:
    with st.sidebar:
        if "pending_demo_page" in st.session_state:
            st.session_state["active_page"] = st.session_state.pop("pending_demo_page")
        st.markdown('<div class="brand">VIREO<br><span>PULSE</span></div><div class="brand-sub">SUPPORT OPERATIONS<br>INTELLIGENCE</div>', unsafe_allow_html=True)
        st.text_input("Command search", key="command_search", placeholder="Show Morning shift…", on_change=handle_command, label_visibility="collapsed")
        st.caption("Command search · pages, shifts, tickets")
        st.radio("Workspace", PAGES, key="active_page", label_visibility="collapsed")
        st.divider()
        st.toggle("Demo mode · guided tour", key="demo_mode", value=False)
        roster = data.get("roster", {})
        total = int(len(tickets))
        matched = total - int(roster.get("zero_match_cases", 0))
        run_time = datetime.fromtimestamp(float(data["pipeline_mtime"]))
        st.markdown("<div class='eyebrow'>Data health</div>", unsafe_allow_html=True)
        roster_issues = int(roster.get("zero_match_cases", 0)) + int(roster.get("multiple_match_cases", 0))
        st.markdown(f"**{total:,} tickets**<br><span class='quiet'>Roster matched {matched:,} / {total:,}</span><br><span class='quiet'>Pipeline · {run_time:%d %b %Y %H:%M}</span><br><span class='live'><i></i>{'REVIEW' if roster_issues else 'HEALTHY'}</span>", unsafe_allow_html=True)
    return st.session_state.get("active_page", "Command Center")


def render_topbar(tickets: pd.DataFrame) -> dict[str, list[str]]:
    if "pending_shift" in st.session_state:
        st.session_state["selected_shift"] = st.session_state.pop("pending_shift")
    dimensions = {"Site": "roster_site", "Shift": "roster_shift", "Team": "roster_team", "Channel": "channel", "Priority": "priority"}
    first = pd.to_datetime(tickets["created_at"], utc=True).min()
    last = pd.to_datetime(tickets["created_at"], utc=True).max()
    st.markdown(
        f"<div class='topline'><div><strong>Vireo Audio</strong><br><span class='quiet'>Support Operations Intelligence · {first:%b %Y} → {last:%b %Y}</span></div><div class='live'><i></i>ANALYSIS READY</div></div>",
        unsafe_allow_html=True,
    )
    current: dict[str, list[str]] = {}
    with st.expander("FILTERS · Site / Shift / Team / Channel / Priority", expanded=False):
        first_row = st.columns(3)
        second_row = st.columns(3)
        columns = [*first_row, *second_row[:2]]
        for column, (label, field) in zip(columns, dimensions.items()):
            values = sorted(tickets[field].dropna().astype(str).unique().tolist())
            options = ["All", *values]
            key = FILTER_KEYS[label]
            if key not in st.session_state or st.session_state[key] not in options:
                st.session_state[key] = "All"
            with column:
                selected = st.selectbox(label, options, key=key, label_visibility="visible")
                current[label.lower()] = values if selected == "All" else [selected]
        with second_row[2]:
            st.button("Reset filters", key="reset_filters", on_click=reset_global_filters, use_container_width=True)
    return current


@st.dialog("Ticket incident", width="large")
def show_ticket_dialog(ticket: dict[str, Any]) -> None:
    st.markdown(f"<div class='eyebrow'>Incident · {ticket.get('ticket_id')}</div>", unsafe_allow_html=True)
    breached = bool(ticket.get("sla_breached"))
    st.error("BREACHED" if breached else "WITHIN SLA")
    cols = st.columns(3)
    cols[0].metric("Response", f"{float(ticket.get('response_minutes') or 0):.0f} min")
    cols[1].metric("Policy target", f"{float(ticket.get('sla_threshold_minutes') or 0):.0f} min")
    cols[2].metric("Delay beyond target", f"{max(float(ticket.get('breach_minutes') or 0), 0):.0f} min")
    st.write({key: ticket.get(key) for key in ["ticket_id", "channel", "priority", "category", "status", "agent_id", "agent_name", "roster_site", "roster_shift", "roster_team", "roster_assignment_id", "transfers"]})
    st.markdown("**Customer message**")
    st.write(ticket.get("customer_message") or "No customer message recorded.")
    st.markdown("**Agent notes**")
    st.write(ticket.get("agent_notes") or "No agent notes recorded.")
    created = pd.to_datetime(ticket.get("created_at"), utc=True).tz_convert("Asia/Kolkata")
    response = pd.to_datetime(ticket.get("first_response_at"), utc=True).tz_convert("Asia/Kolkata")
    st.caption(f"CREATED · {created:%d %b %Y %H:%M IST}  ───────── FIRST RESPONSE · {response:%d %b %Y %H:%M IST}")


@st.dialog("Agent profile", width="large")
def show_agent_dialog(profile: dict[str, Any], trend: pd.DataFrame) -> None:
    st.markdown(f"<div class='eyebrow'>Agent context · {profile.get('agent_id')}</div>", unsafe_allow_html=True)
    st.subheader(str(profile.get("agent_name", "Agent")))
    st.caption(f"{profile.get('roster_site')} · {profile.get('roster_team')} · {profile.get('roster_shift')}")
    cols = st.columns(4)
    cols[0].metric("Tickets", f"{int(profile.get('tickets', 0)):,}")
    cols[1].metric("Breach rate", f"{float(profile.get('breach_rate', 0)):.1%}")
    cols[2].metric("Median", f"{float(profile.get('median_response_minutes', 0)):.0f} min")
    cols[3].metric("P90", f"{float(profile.get('p90_response_minutes', 0)):.0f} min")
    if not trend.empty:
        fig = go.Figure(go.Scatter(x=trend["week_start"], y=trend["breach_rate"] * 100, mode="lines+markers", line={"color": "#68d4c9", "shape": "spline"}))
        fig.update_layout(yaxis_title="Weekly breach rate (%)", xaxis_title=None)
        st.plotly_chart(configure_plot(fig, 230), use_container_width=True)
    st.caption("Contextual workload measure only; not a performance ranking.")


def render_hero(tickets: pd.DataFrame, metrics: dict[str, Any]) -> None:
    rate = float(metrics["breach_rate"])
    progress = min(rate * 100, 100)
    status = "Attention required" if rate >= .15 else "Within proposed pilot goal"
    st.markdown(
        f"<div class='hero'><div><div class='eyebrow'>SLA Pulse · First-response breach rate</div><div class='hero-label'>Current filtered operating view</div><div class='hero-value'>{rate:.1%}</div><div class='hero-meta'>{metrics['breaches']:,} breached <span style='color:#45585e'>/</span> {metrics['tickets']:,} tickets</div><div class='status-line'><span class='status-attention'>● {status}</span><span>Median {metrics['median_response']:.0f} min · P90 {metrics['p90_response']:.0f} min</span></div></div><div class='pulse-ring' style='--progress:{progress}%'><div class='pulse-inner'><strong>{rate:.1%}</strong>BREACH RATE</div></div></div>",
        unsafe_allow_html=True,
    )
    st.caption("The 15% comparison is a proposed pilot goal, not a policy SLA threshold. Breach status is calculated per ticket using its channel-specific policy target.")


def render_timeline(tickets: pd.DataFrame, key: str = "timeline") -> None:
    if tickets.empty:
        st.info("No tickets match this view. Reset filters to restore the dataset.")
        return
    weekly = weekly_analysis(tickets)
    if weekly.empty:
        return
    week_strings = [pd.Timestamp(value).strftime("%Y-%m-%d") for value in weekly["week_start"]]
    window_key = f"{key}_window"
    current_window = st.session_state.get(window_key)
    if not current_window or any(value not in week_strings for value in current_window):
        st.session_state[window_key] = (week_strings[0], week_strings[-1])
    window = st.select_slider("Time window · week starting", options=week_strings, key=window_key)
    window_tickets = tickets[tickets["week_start"].dt.strftime("%Y-%m-%d").between(window[0], window[1])]
    selection = st.plotly_chart(timeline_figure(window_tickets), use_container_width=True, key=key, on_select="rerun", selection_mode="points")
    weekly = weekly_analysis(window_tickets)
    if weekly.empty:
        return
    clicked_week = None
    if selection and selection.selection.points:
        clicked_week = selection.selection.points[0].get("x")
    week_strings = [pd.Timestamp(value).strftime("%Y-%m-%d") for value in weekly["week_start"]]
    if clicked_week:
        try:
            clicked_str = pd.Timestamp(clicked_week).strftime("%Y-%m-%d")
            if clicked_str in week_strings:
                st.session_state["inspect_week"] = clicked_str
                st.session_state["week_inspector"] = clicked_str
        except (TypeError, ValueError):
            pass
    selected = st.selectbox("Inspect week", week_strings, index=week_strings.index(st.session_state["inspect_week"]) if st.session_state.get("inspect_week") in week_strings else len(week_strings) - 1, key="week_inspector")
    row = weekly.loc[weekly["week_start"].dt.strftime("%Y-%m-%d").eq(selected)].iloc[0]
    cols = st.columns(5)
    cols[0].metric("Week starting", pd.Timestamp(selected).strftime("%d %b %Y"))
    cols[1].metric("Tickets", f"{int(row['tickets']):,}")
    cols[2].metric("Breaches", f"{int(row['breaches']):,}")
    cols[3].metric("Breach rate", f"{row['breach_rate']:.1%}")
    cols[4].metric("Median / P90", f"{row['median_response_minutes']:.0f} / {row['p90_response_minutes']:.0f} min")


def render_shift_lanes(tickets: pd.DataFrame) -> None:
    shifts = shift_analysis(tickets)
    if shifts.empty:
        st.info("No tickets match this view.")
        return
    expected = ["Morning", "Day", "Night"]
    shifts = shifts.set_index("roster_shift").reindex(expected).dropna(how="all").reset_index()
    max_volume = max(float(shifts["tickets"].max()), 1)
    cols = st.columns(max(len(shifts), 1))
    week_count = min(12, tickets["week_start"].nunique())
    recent = tickets[tickets["week_start"].isin(sorted(tickets["week_start"].dropna().unique())[-week_count:])]
    baseline = float(recent["sla_breached"].mean()) if not recent.empty else 0.0
    for col, (_, row) in zip(cols, shifts.iterrows()):
        shift_tickets = tickets[tickets["roster_shift"].eq(row["roster_shift"])]
        recent_shift = recent[recent["roster_shift"].eq(row["roster_shift"])]
        elevated_weeks = int((weekly_analysis(recent_shift)["breach_rate"] > baseline).sum()) if not recent_shift.empty else 0
        intensity = min(float(row["breach_rate"]) * 1.15, .34)
        fill = min(float(row["tickets"]) / max_volume * 100, 100)
        col.markdown(
            f"<div class='lane' style='--intensity:{intensity:.2f}'><div class='lane-name'>{str(row['roster_shift']).upper()}</div><div class='lane-rate'>{row['breach_rate']:.1%}</div><div class='lane-meta'>{int(row['breaches']):,} breaches · {int(row['tickets']):,} tickets<br>Median {row['median_response_minutes']:.0f} min · P90 {row['p90_response_minutes']:.0f} min</div><div class='lane-track'><div class='lane-fill' style='width:{fill:.1f}%'></div></div><div class='lane-meta'>{elevated_weeks}/{week_count} recent weeks above filtered baseline<br><b>{week_count}-week pattern</b> · volume-scaled lane</div></div>",
            unsafe_allow_html=True,
        )
        if col.button(f"Focus {row['roster_shift']}", key=f"focus_{row['roster_shift']}", use_container_width=True):
            set_pending_shift(str(row["roster_shift"]))
            st.rerun()


def render_agent_lens(tickets: pd.DataFrame) -> None:
    grouped, matrix = agent_week_matrix(tickets)
    if matrix.empty:
        st.info("No agent-week observations match the active filters.")
        return
    st.caption("Each cell is that agent's weekly breach rate. Select a profile below to inspect its period context; this is not a punitive ranking.")
    total_agent = grouped.groupby(["agent_id", "agent_name"])["tickets"].sum().sort_values(ascending=False)
    visible_ids = set(total_agent.head(35).index.get_level_values(0))
    visible = grouped[grouped["agent_id"].isin(visible_ids)]
    matrix_rows = visible.groupby(["agent_id", "agent_name", "week_start"], dropna=False).agg(
        tickets=("tickets", "sum"),
        breaches=("breaches", "sum"),
        median_response_minutes=("median_response_minutes", "median"),
    ).reset_index()
    matrix_rows["breach_rate"] = matrix_rows["breaches"] / matrix_rows["tickets"]
    heat = matrix_rows.pivot_table(index=["agent_id", "agent_name"], columns="week_start", values="breach_rate", aggfunc="first") * 100
    lookup = matrix_rows.set_index(["agent_id", "agent_name", "week_start"])
    custom = []
    for agent_key in heat.index:
        agent_custom = []
        for week in heat.columns:
            key = (*agent_key, week)
            if key in lookup.index:
                values = lookup.loc[key]
                agent_custom.append([int(values["tickets"]), int(values["breaches"]), float(values["median_response_minutes"])])
            else:
                agent_custom.append([0, 0, 0])
        custom.append(agent_custom)
    fig = go.Figure(go.Heatmap(
        z=heat.to_numpy(), x=[pd.Timestamp(value).strftime("%d %b") for value in heat.columns],
        y=[f"{name} · {agent_id}" for agent_id, name in heat.index], customdata=custom,
        colorscale=[[0, "#17252a"], [.2, "#23605f"], [.5, "#c0924d"], [1, "#bd654f"]], zmin=0, zmax=100,
        colorbar={"title": "Rate %", "tickfont": {"color": "#9aaab3"}},
        hovertemplate="%{y}<br>Week %{x}<br>Rate %{z:.1f}%<br>Tickets %{customdata[0]}<br>Breaches %{customdata[1]}<br>Median %{customdata[2]:.0f} min<extra></extra>",
    ))
    fig.update_layout(title="Agent × week breach-rate matrix", xaxis_title=None, yaxis_title=None, xaxis={"tickangle": -45, "dtick": max(1, len(heat.columns) // 14)}, yaxis={"autorange": "reversed"})
    st.plotly_chart(configure_plot(fig, max(430, len(heat.index) * 23)), use_container_width=True)
    agents = grouped[["agent_id", "agent_name"]].drop_duplicates().sort_values("agent_name")
    options = {f"{row.agent_name} · {row.agent_id}": row.agent_id for row in agents.itertuples()}
    selected_agent = st.selectbox("Inspect agent profile", ["Select an agent…", *options.keys()], key="agent_profile_select")
    if selected_agent != "Select an agent…":
        agent_id = options[selected_agent]
        profile_tickets = tickets[tickets["agent_id"].eq(agent_id)]
        metrics = kpi_metrics(profile_tickets)
        first = profile_tickets.iloc[0]
        profile = {
            "agent_id": agent_id, "agent_name": first["agent_name"], "roster_site": first["roster_site"], "roster_team": first["roster_team"], "roster_shift": first["roster_shift"],
            "tickets": metrics["tickets"], "breach_rate": metrics["breach_rate"], "median_response_minutes": metrics["median_response"], "p90_response_minutes": metrics["p90_response"],
        }
        trend = weekly_analysis(profile_tickets)
        with st.container(border=True):
            st.markdown(f"### {first['agent_name']} <span class='quiet'>· {agent_id}</span>", unsafe_allow_html=True)
            st.caption(f"{first['roster_site']} · {first['roster_team']} · {first['roster_shift']} · assignment {first.get('roster_assignment_id', 'not available')}")
            a, b, c, d = st.columns(4)
            a.metric("Tickets", f"{metrics['tickets']:,}")
            b.metric("Breach rate", f"{metrics['breach_rate']:.1%}")
            c.metric("Median", f"{metrics['median_response']:.0f} min")
            d.metric("P90", f"{metrics['p90_response']:.0f} min")
            if st.button("Open agent detail", key="open_agent_dialog"):
                show_agent_dialog(profile, trend)


def render_ticket_explorer(tickets: pd.DataFrame) -> None:
    search_col, category_col, breach_col = st.columns([2.4, 1.5, 1])
    with search_col:
        query = st.text_input("Search tickets", key="ticket_query", placeholder="Ticket ID, agent, category, message, channel…")
    categories = ["All categories", *sorted(tickets["category"].dropna().astype(str).unique().tolist())]
    with category_col:
        category = st.selectbox("Category", categories, key="ticket_category_filter")
    with breach_col:
        breached = st.toggle("Breached only", key="ticket_breached_only")
    results = search_tickets(tickets, query, breached_only=breached, category=category, limit=250)
    if results.empty:
        st.info("No tickets match this view. Clear search or reset filters to restore results.")
        return
    display = results[["ticket_id", "sla_breached", "roster_shift", "channel", "response_minutes", "sla_threshold_minutes", "agent_id", "category", "priority", "created_at"]].copy()
    display["sla_breached"] = display["sla_breached"].map({True: "BREACHED", False: "WITHIN SLA"})
    display["created_at"] = pd.to_datetime(display["created_at"], utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%d %b %Y %H:%M")
    display = display.rename(columns={"ticket_id": "Ticket", "sla_breached": "SLA status", "roster_shift": "Shift", "channel": "Channel", "response_minutes": "Response (min)", "sla_threshold_minutes": "SLA target (min)", "agent_id": "Agent", "category": "Category", "priority": "Priority", "created_at": "Created (IST)"})
    st.caption(f"Showing {len(display):,} records in the result preview · full incident detail opens only on selection")
    st.dataframe(display, hide_index=True, use_container_width=True, height=390)
    ids = results["ticket_id"].astype(str).tolist()
    selected_id = st.selectbox("Open incident", ["Select a ticket…", *ids], key="ticket_detail_select")
    if selected_id != "Select a ticket…":
        record = results.loc[results["ticket_id"].eq(selected_id)].iloc[0]
        if st.button("Inspect ticket incident", type="primary", key="inspect_ticket"):
            show_ticket_dialog(record.to_dict())


def render_ai_insights(tickets: pd.DataFrame, data: dict[str, Any]) -> None:
    questions = [
        "Why are SLA breaches increasing?",
        "What is driving Morning shift breaches?",
        "Which categories contribute most?",
        "Are transfers associated with delays?",
        "What changed after June?",
    ]
    st.markdown("<div class='eyebrow'>AI Operations Analyst · Ask the dataset</div>", unsafe_allow_html=True)
    question = st.selectbox("Choose an evidence question", questions, key="ai_question")
    answer = build_ai_insight(tickets, question)
    with st.container(border=True):
        st.markdown("**INSIGHT**")
        st.write(answer["headline"])
        st.caption(f"Confidence · {answer['confidence']} · Source · {answer['source_count']:,} filtered tickets")
        evidence = answer["evidence"]
        shift_evidence = next((row for row in evidence if row.get("type") == "shift"), None)
        if shift_evidence:
            cols = st.columns(4)
            cols[0].metric("Tickets", f"{answer['source_count']:,}")
            cols[1].metric("Breaches", f"{answer['breach_count']:,}")
            cols[2].metric("Shift breach share", f"{shift_evidence['share_of_breaches']:.1%}")
            cols[3].metric("Shift ticket share", f"{shift_evidence['share_of_tickets']:.1%}")
        breakdown = [row for row in evidence if row.get("type") in {"category", "channel"}]
        if breakdown:
            st.markdown("**EVIDENCE**")
            st.dataframe(pd.DataFrame(breakdown), hide_index=True, use_container_width=True)
        elif evidence:
            st.markdown("**EVIDENCE**")
            st.dataframe(pd.DataFrame(evidence), hide_index=True, use_container_width=True)
        priority_evidence = next((row.get("distribution") for row in evidence if row.get("type") == "priority"), None)
        if priority_evidence:
            st.markdown("**PRIORITY MIX**")
            st.dataframe(pd.DataFrame(priority_evidence), hide_index=True, use_container_width=True)
        with st.expander("How was this calculated?"):
            st.write("The current global filter state is applied to ticket-level rows on the server. Counts and rates are grouped from the same filtered set. SLA breaches were calculated upstream against channel-specific thresholds. No LLM generates or changes numerical values.")
            st.json({"filtered_tickets": answer["source_count"], "breaches": answer["breach_count"], "evidence_rows": evidence})
    themes = data["themes"]
    st.markdown("#### Exploratory ticket-text themes")
    st.caption("TF-IDF + KMeans groups similar messages locally. The themes are unsupervised hints, not verified causes; inspect examples before acting.")
    if themes.empty:
        st.info("No stable text themes are available.")
    else:
        st.dataframe(themes.rename(columns={"theme_id": "Theme", "tickets": "Messages", "share": "Share", "top_terms": "Terms", "example_message": "Example"}), hide_index=True, use_container_width=True)
    ai_report = data["ai_validation"]
    st.caption(f"Keyword sample output coverage: {float(ai_report.get('keyword_label_coverage_rate', 0)):.1%}; semantic accuracy: not measured (no human-labeled benchmark).")


def render_data_quality(data: dict[str, Any], tickets: pd.DataFrame) -> None:
    report = data.get("validation", {})
    summary = report.get("summary", {})
    roster = data.get("roster", {})
    checks = {item["name"]: item for item in report.get("checks", [])}
    raw_rows = int(summary.get("raw_rows", len(tickets)))
    duplicate_ids = int(summary.get("duplicate_ticket_ids", 0))
    clean_rows = int(summary.get("clean_rows", len(tickets)))
    matched = clean_rows - int(roster.get("zero_match_cases", 0))
    missing_response = int(checks.get("invalid_timestamps", {}).get("details", {}).get("invalid_first_response_at", 0))
    invalid_csat = int(checks.get("impossible_csat_values", {}).get("details", {}).get("count", 0))
    stages = [
        ("RAW", f"{raw_rows:,} rows", "Source ticket export", "health-good"),
        ("DEDUPLICATION", f"{duplicate_ids:,} removed", f"{clean_rows:,} unique tickets", "health-good"),
        ("TIMEZONE NORMALIZATION", "UTC → IST", "SLA + roster timestamps", "health-good"),
        ("ROSTER MATCH", f"{matched:,} / {clean_rows:,}", f"{roster.get('zero_match_cases', 0)} unmatched", "health-warn" if roster.get("zero_match_cases", 0) else "health-good"),
        ("SLA ENGINE", "READY", "Channel-specific policy thresholds", "health-good"),
        ("ANALYSIS", "READY", "Weekly + shift + agent + AI themes", "health-good"),
    ]
    stage_cols = st.columns(6)
    for column, (name, value, detail, status_class) in zip(stage_cols, stages):
        column.markdown(f"<div class='health-stage'><b>{name}</b><strong class='{status_class}'>{value}</strong><small>{detail}</small></div>", unsafe_allow_html=True)
    st.markdown("#### Data quality checks")
    items = [
        ("Duplicate IDs", duplicate_ids, "Resolved by current-source precedence", True),
        ("Timestamp validity", checks.get("invalid_timestamps", {}).get("passed", False), checks.get("invalid_timestamps", {}).get("details", {}), False),
        ("First response missing", missing_response, "Missing first response timestamps in raw input", True),
        ("Roster assignment match", f"{matched:,}/{clean_rows:,}", roster, True),
        ("Invalid CSAT", invalid_csat, "Flagged legacy/out-of-range ratings", True),
        ("Invalid status / channel", checks.get("unexpected_status_values", {}).get("passed", False) and checks.get("unexpected_channel_values", {}).get("passed", False), "Allowed values validated", False),
    ]
    rows = []
    for name, value, detail, warning_on_nonzero in items:
        if isinstance(value, bool):
            status = "PASS" if value else "REVIEW"
        else:
            status = "REVIEW" if warning_on_nonzero and bool(value) else "PASS"
        rows.append({"Check": name, "Result": status, "Value": str(value), "Details": str(detail)})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    with st.expander("Validation report details"):
        st.json(report)
    with st.expander("Roster assignment audit"):
        st.json(roster)


def render_demo_guide(page: str) -> None:
    if not st.session_state.get("demo_mode"):
        return
    tour = ["Command Center", "SLA Timeline", "Shift Intelligence", "Agent Lens", "Ticket Explorer", "AI Insights", "Data Quality"]
    index = tour.index(page) if page in tour else 0
    st.info(f"**DEMO MODE · {index + 1}/7**  Overview → weekly spike → shift pattern → agent context → ticket inspection → evidence-backed insight → data trust")
    if st.button("Next demo stop →", key="demo_next"):
        advance_demo_tour(page)
        st.rerun()


def main() -> None:
    st.set_page_config(page_title="Vireo Pulse | Support Operations Intelligence", page_icon="◉", layout="wide", initial_sidebar_state="expanded")
    inject_theme()
    try:
        pipeline_path = ROOT / "data" / "clean_tickets_with_roster.csv"
        data = cached_dashboard_data(pipeline_path.stat().st_mtime)
    except (FileNotFoundError, ValueError) as error:
        st.error(str(error))
        st.code("python -m src.pipeline\nstreamlit run app.py", language="powershell")
        return
    all_tickets = data["tickets"]
    page = render_sidebar(data, all_tickets)
    filters = render_topbar(all_tickets)
    active = filter_tickets(all_tickets, filters)
    active_filter_labels = []
    for label, key in FILTER_KEYS.items():
        value = st.session_state.get(key, "All")
        if value != "All":
            active_filter_labels.append(f"<span class='filter-chip'>{label.upper()} · {value}</span>")
    if active_filter_labels:
        st.markdown("".join(active_filter_labels), unsafe_allow_html=True)
    render_demo_guide(page)
    metrics = kpi_metrics(active)

    if page == "Command Center":
        st.markdown("<div class='eyebrow'>Command Center / Current operating picture</div>", unsafe_allow_html=True)
        render_hero(active, metrics)
        st.markdown("### Weekly SLA timeline")
        render_timeline(active, key="command_timeline")
        st.markdown("### Shift intelligence")
        render_shift_lanes(active)
        left, right = st.columns([1.1, .9])
        with left:
            st.markdown("### Ticket categories · breach burden")
            cats = category_analysis(active).head(7)
            fig = go.Figure(go.Bar(x=cats["breaches"], y=cats["category"], orientation="h", marker_color="#54bdb4", customdata=cats[["tickets", "breach_rate"]], hovertemplate="%{y}<br>Breaches %{x}<br>Tickets %{customdata[0]}<br>Rate %{customdata[1]:.1%}<extra></extra>"))
            fig.update_layout(yaxis={"autorange": "reversed"}, xaxis_title="Breached tickets", title="Largest category counts")
            st.plotly_chart(configure_plot(fig, 280), use_container_width=True)
        with right:
            st.markdown("### Analyst readout")
            insight = build_ai_insight(active, "Why are SLA breaches increasing?")
            st.markdown(f"<div class='panel'><div class='eyebrow'>POTENTIAL PATTERN</div><p style='color:#dbe7e8'>{insight['headline']}</p><span class='quiet'>Evidence from {insight['source_count']:,} filtered tickets · association, not causation</span></div>", unsafe_allow_html=True)
            st.caption("Open AI Insights from the navigation rail for evidence and calculation details.")
    elif page == "SLA Timeline":
        st.markdown("<div class='eyebrow'>01 / When is it happening?</div>", unsafe_allow_html=True)
        st.title("SLA Timeline")
        st.caption("Weekly breach rate recalculated from the current shared filter state. The dotted line is the proposed 15% pilot goal, not a policy threshold.")
        render_timeline(active, key="timeline_page")
        st.dataframe(weekly_analysis(active).assign(breach_rate=lambda frame: frame["breach_rate"].map(lambda value: f"{value:.1%}")), hide_index=True, use_container_width=True)
    elif page == "Shift Intelligence":
        st.markdown("<div class='eyebrow'>02 / Which shifts?</div>", unsafe_allow_html=True)
        st.title("Shift Intelligence")
        st.caption("Volume-scaled lanes show burden, response distribution, and recent pattern relative to the filtered baseline.")
        render_shift_lanes(active)
        st.dataframe(shift_analysis(active).assign(breach_rate=lambda frame: frame["breach_rate"].map(lambda value: f"{value:.1%}")), hide_index=True, use_container_width=True)
    elif page == "Agent Lens":
        st.markdown("<div class='eyebrow'>03 / Which agents · workload context, not ranking</div>", unsafe_allow_html=True)
        st.title("Agent Lens")
        render_agent_lens(active)
    elif page == "Ticket Explorer":
        st.markdown("<div class='eyebrow'>04 / Underlying incident records</div>", unsafe_allow_html=True)
        st.title("Ticket Explorer")
        st.caption("Search ticket ID, agent, category, customer message, channel, or agent notes. Shared site/shift/team/channel/priority filters remain active.")
        render_ticket_explorer(active)
    elif page == "AI Insights":
        st.markdown("<div class='eyebrow'>05 / Why might it be happening?</div>", unsafe_allow_html=True)
        st.title("AI Operations Analyst")
        render_ai_insights(active, data)
    elif page == "Data Quality":
        st.markdown("<div class='eyebrow'>06 / Can I trust the numbers?</div>", unsafe_allow_html=True)
        st.title("Data Quality")
        render_data_quality(data, all_tickets)


if __name__ == "__main__":
    main()