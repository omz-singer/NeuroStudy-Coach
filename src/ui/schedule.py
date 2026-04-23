"""
src/ui/schedule.py
Study Schedule page: calendar view of generated study sessions,
plus controls to block off unavailable days and regenerate the schedule.
"""

import calendar
from datetime import date, timedelta
from collections import defaultdict

import streamlit as st

from src.db import (
    get_all_assignments,
    get_blocked_days,
    add_blocked_day,
    remove_blocked_day,
    save_study_sessions,
    get_study_sessions,
    get_user_profile,
)
from src.scheduler import generate_schedule

# ── Colour palette per priority ───────────────────────────────────────────────

PRIORITY_COLORS = {
    "High":   "#f87171",
    "Medium": "#facc15",
    "Low":    "#4ade80",
}

DAYS_OF_WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sessions_by_date(sessions: list[dict]) -> dict[str, list[dict]]:
    result = defaultdict(list)
    for s in sessions:
        result[s["session_date"]].append(s)
    return result


def _render_calendar(year: int, month: int, sessions_by_date: dict, blocked: set[str]) -> None:
    """Render a single month as an HTML-styled calendar grid."""
    cal = calendar.monthcalendar(year, month)
    month_name = date(year, month, 1).strftime("%B %Y")

    st.markdown(f"### {month_name}")

    # Header row
    cols = st.columns(7)
    for i, day_name in enumerate(DAYS_OF_WEEK):
        cols[i].markdown(f"<div style='text-align:center;font-weight:700;font-size:0.8rem;color:#94a3b8'>{day_name}</div>", unsafe_allow_html=True)

    today = date.today()

    for week in cal:
        cols = st.columns(7)
        for i, day_num in enumerate(week):
            with cols[i]:
                if day_num == 0:
                    st.markdown("<div style='min-height:80px'></div>", unsafe_allow_html=True)
                    continue

                d = date(year, month, day_num)
                d_str = d.isoformat()
                is_today = d == today
                is_blocked = d_str in blocked
                day_sessions = sessions_by_date.get(d_str, [])

                # Cell styling
                bg = "#1e293b"
                border = "1px solid #334155"
                if is_today:
                    border = "2px solid #6366f1"
                if is_blocked:
                    bg = "#450a0a"
                    border = "1px solid #7f1d1d"

                cell_html = f"""
                <div style="background:{bg};border:{border};border-radius:8px;
                            padding:6px;min-height:80px;margin:2px;">
                    <div style="font-size:0.85rem;font-weight:{'700' if is_today else '400'};
                                color:{'#6366f1' if is_today else '#e2e8f0'};margin-bottom:4px;">
                        {day_num}{'🚫' if is_blocked else ''}
                    </div>
                """

                for s in day_sessions[:3]:  # cap display at 3 per cell
                    color = PRIORITY_COLORS.get(s["priority"], "#94a3b8")
                    name_short = s["assignment_name"][:14] + "…" if len(s["assignment_name"]) > 14 else s["assignment_name"]
                    cell_html += f"""
                    <div style="background:{color}22;border-left:3px solid {color};
                                border-radius:3px;padding:2px 4px;margin-bottom:2px;
                                font-size:0.7rem;color:#e2e8f0;line-height:1.3;">
                        {name_short}<br>
                        <span style="color:{color};font-weight:600">{s['duration_mins']}min</span>
                    </div>
                    """

                if len(day_sessions) > 3:
                    cell_html += f"<div style='font-size:0.65rem;color:#94a3b8'>+{len(day_sessions)-3} more</div>"

                cell_html += "</div>"
                try:
                    st.html(cell_html)
                except AttributeError:
                    st.markdown(cell_html, unsafe_allow_html=True)


# ── Sub-sections ──────────────────────────────────────────────────────────────

def _regenerate_schedule() -> None:
    """Regenerate and save the study schedule using current assignments and blocked days."""
    assignments = get_all_assignments()
    blocked = get_blocked_days()
    profile = get_user_profile()
    new_sessions = generate_schedule(assignments, blocked, user_profile=profile or None)
    save_study_sessions(new_sessions)


def _render_settings_panel(blocked: list[str]) -> bool:
    """Render blocked days settings. Returns True if schedule should regenerate."""
    regenerate = False

    with st.expander("⚙️ Settings — Block Off Unavailable Days", expanded=False):
        st.caption("Mark days you can't study. The scheduler will skip these when building your plan.")

        col1, col2 = st.columns(2)
        new_blocked = col1.date_input("Block a day", min_value=date.today(), key="block_day_input")
        if col1.button("🚫 Block this day"):
            add_blocked_day(new_blocked)
            # Auto-regenerate schedule
            _regenerate_schedule()
            st.success(f"Blocked {new_blocked.strftime('%b %d, %Y')} and schedule updated!")
            st.rerun()

        if blocked:
            col2.markdown("**Currently blocked:**")
            for b in blocked:
                b_date = date.fromisoformat(b)
                bcol1, bcol2 = col2.columns([3, 1])
                bcol1.write(b_date.strftime("%b %d, %Y"))
                if bcol2.button("✕", key=f"unblock_{b}"):
                    remove_blocked_day(b_date)
                    # Auto-regenerate schedule
                    _regenerate_schedule()
                    st.rerun()
        else:
            col2.info("No days blocked yet.")

    return regenerate


def _render_session_list(sessions: list[dict]) -> None:
    """Render a compact list view of upcoming sessions."""
    st.subheader("📋 Upcoming Sessions")

    today = date.today()
    upcoming = [s for s in sessions if date.fromisoformat(s["session_date"]) >= today]

    if not upcoming:
        st.info("No upcoming sessions. Generate a schedule above!")
        return

    # Group by date
    by_date = _sessions_by_date(upcoming)

    for d_str in sorted(by_date.keys())[:14]:  # show next 2 weeks
        d = date.fromisoformat(d_str)
        label = "Today" if d == today else ("Tomorrow" if d == today + timedelta(days=1) else d.strftime("%A, %b %d"))
        st.markdown(f"**{label}**")

        for s in by_date[d_str]:
            color = PRIORITY_COLORS.get(s["priority"], "#94a3b8")
            total_mins = s["duration_mins"]
            hrs = total_mins // 60
            mins = total_mins % 60
            duration_str = f"{hrs}h {mins}m" if hrs else f"{mins}m"

            st.markdown(
                f"""<div style="background:#1e293b;border-left:4px solid {color};
                    border-radius:6px;padding:8px 12px;margin-bottom:6px;">
                    <span style="font-weight:600;color:#e2e8f0">{s['assignment_name']}</span>
                    &nbsp;·&nbsp;<span style="color:#94a3b8;font-size:0.85rem">{s['course']}</span>
                    &nbsp;·&nbsp;<span style="color:{color};font-weight:600">{duration_str}</span>
                    &nbsp;·&nbsp;<span style="color:#64748b;font-size:0.8rem">Session {s['session_number']}/{s['total_sessions']}</span>
                </div>""",
                unsafe_allow_html=True,
            )
        st.markdown("")


# ── Main entry point ──────────────────────────────────────────────────────────

def render_schedule_page() -> None:
    st.header("📅 Study Schedule")
    st.caption("Your personalised study plan, built around your assignments and availability.")

    assignments = get_all_assignments()
    blocked = get_blocked_days()
    sessions = get_study_sessions()

    # Settings panel
    _render_settings_panel(blocked)

    st.divider()

    # Generate / Regenerate button
    col1, col2 = st.columns([2, 1])
    with col1:
        if not assignments:
            st.warning("⚠️ No assignments found. Add some in the Assignments section first!")
            return
        st.markdown(f"**{len(assignments)} assignment(s)** loaded · **{len(blocked)} day(s)** blocked")

    with col2:
        if st.button("✨ Generate Schedule", use_container_width=True, type="primary"):
            with st.spinner("Building your optimal study plan..."):
                profile = get_user_profile()
                new_sessions = generate_schedule(assignments, blocked, user_profile=profile or None)
                save_study_sessions(new_sessions)
            st.success(f"Schedule generated — {len(new_sessions)} study session(s) planned!")
            st.rerun()

    if not sessions:
        st.info("Hit **Generate Schedule** to build your study plan.")
        return

    st.divider()

    # Calendar navigation
    if "cal_month_offset" not in st.session_state:
        st.session_state.cal_month_offset = 0

    today = date.today()
    target = date(today.year, today.month, 1) + timedelta(days=30 * st.session_state.cal_month_offset)

    nav_col1, nav_col2, nav_col3 = st.columns([1, 3, 1])
    if nav_col1.button("◀ Prev"):
        st.session_state.cal_month_offset -= 1
        st.rerun()
    if nav_col3.button("Next ▶"):
        st.session_state.cal_month_offset += 1
        st.rerun()

    sessions_by_date = _sessions_by_date(sessions)
    blocked_set = set(blocked)

    _render_calendar(target.year, target.month, sessions_by_date, blocked_set)

    st.divider()
    _render_session_list(sessions)
