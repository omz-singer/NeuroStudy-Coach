"""
src/ui/dashboard.py
Progress Dashboard page.
"""

from datetime import date, datetime
import streamlit as st

from src.db import (
    get_all_assignments, get_today_sessions, get_completed_session_ids,
    mark_session_complete, unmark_session_complete, get_all_progress,
    upsert_assignment_progress, delete_assignment, get_blocked_days, save_study_sessions,
    get_user_profile,
)
from src.scheduler import generate_schedule

PRIORITY_COLORS = {"High": "#f87171", "Medium": "#facc15", "Low": "#4ade80"}
DIFFICULTY_OPTIONS = ["Easy", "Medium", "Hard"]
DIFFICULTY_COLORS = {"Easy": "#4ade80", "Medium": "#facc15", "Hard": "#f87171"}


def _html(content: str) -> None:
    try:
        st.html(content)
    except AttributeError:
        st.markdown(content, unsafe_allow_html=True)


def _progress_bar_html(pct: float, color: str) -> str:
    pct = min(100.0, max(0.0, pct))
    return f"""<div style="background:#334155;border-radius:999px;height:12px;width:100%;margin:6px 0;">
        <div style="background:{color};width:{pct:.1f}%;height:12px;border-radius:999px;"></div>
    </div>
    <div style="font-size:0.75rem;color:#94a3b8;text-align:right">{pct:.0f}% complete</div>"""


def _difficulty_badge(difficulty: str) -> str:
    color = DIFFICULTY_COLORS.get(difficulty, "#94a3b8")
    return f'<span style="background:{color}22;color:{color};padding:2px 10px;border-radius:999px;font-size:0.75rem;font-weight:700;border:1px solid {color}44">{difficulty}</span>'


def _render_today(completed_ids: set) -> None:
    st.subheader("📌 Today's Study Sessions")
    today_sessions = get_today_sessions()

    if not today_sessions:
        st.info("No sessions scheduled for today. Head to the Study Schedule to generate a plan!")
        return

    total_mins = sum(s["duration_mins"] for s in today_sessions)
    done_mins = sum(s["duration_mins"] for s in today_sessions if s["id"] in completed_ids)
    pct = (done_mins / total_mins * 100) if total_mins else 0

    _html(f"""<div style="background:#1e293b;border-radius:12px;padding:12px 16px;margin-bottom:16px;">
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
            <span style="color:#e2e8f0;font-weight:600">Today's Progress</span>
            <span style="color:#94a3b8;font-size:0.85rem">{done_mins}min / {total_mins}min</span>
        </div>
        {_progress_bar_html(pct, "#6366f1")}
    </div>""")

    for s in today_sessions:
        is_done = s["id"] in completed_ids
        color = PRIORITY_COLORS.get(s["priority"], "#94a3b8")
        hrs = s["duration_mins"] // 60
        mins = s["duration_mins"] % 60
        duration_str = f"{hrs}h {mins}m" if hrs else f"{mins}m"

        col1, col2 = st.columns([5, 1])
        with col1:
            _html(f"""<div style="background:#1e293b;border-left:4px solid {color};border-radius:8px;padding:10px 14px;margin-bottom:6px;opacity:{'0.5' if is_done else '1'};">
                <span style="font-weight:600;color:#e2e8f0;text-decoration:{'line-through' if is_done else 'none'}">{s['assignment_name']}</span>
                &nbsp;·&nbsp;<span style="color:#94a3b8;font-size:0.85rem">{s['course']}</span>
                &nbsp;·&nbsp;<span style="color:{color};font-weight:600">{duration_str}</span>
                &nbsp;·&nbsp;<span style="color:#64748b;font-size:0.8rem">Session {s['session_number']}/{s['total_sessions']}</span>
            </div>""")
        with col2:
            label = "✅ Done" if not is_done else "↩️ Undo"
            if st.button(label, key=f"tog_{s['id']}"):
                if not is_done:
                    mark_session_complete(s["id"])
                else:
                    unmark_session_complete(s["id"])
                st.rerun()


def _render_assignment_cards(assignments: list, progress: dict, completed_ids: set) -> None:
    st.subheader("📚 Assignment Progress")

    if not assignments:
        st.info("No active assignments. Add some in the Assignments section!")
        return

    for a in assignments:
        aid = a["id"]
        p = progress.get(aid, {})
        actual_hours = float(p.get("actual_hours", 0))
        est_hours = float(a["est_hours"])
        actual_diff = p.get("actual_difficulty", None)
        saved_pct = float(p.get("completion_pct", 0))
        hours_pct = min(100.0, (actual_hours / est_hours * 100)) if est_hours else 0
        pct = saved_pct if saved_pct > 0 else hours_pct

        if pct >= 100:
            delete_assignment(aid)
            st.rerun()

        due = date.fromisoformat(a["due_date"][:10])
        days_left = (due - date.today()).days
        bar_color = "#f87171" if days_left <= 2 else "#facc15" if days_left <= 7 else "#4ade80"

        with st.container(border=True):
            header_col, badge_col = st.columns([4, 1])
            with header_col:
                st.markdown(f"**{a['name']}** &nbsp;·&nbsp; `{a['course']}` &nbsp;·&nbsp; *{a['type']}*", unsafe_allow_html=True)
                due_str = due.strftime("%b %d, %Y")
                days_str = "⚠️ Overdue!" if days_left < 0 else "⚠️ Due today!" if days_left == 0 else f"{days_left} day(s) left"
                st.caption(f"📅 Due {due_str} · {days_str}")
            with badge_col:
                if actual_diff:
                    _html(_difficulty_badge(actual_diff))

            _html(_progress_bar_html(pct, bar_color))

            h_col1, h_col2, h_col3 = st.columns(3)
            h_col1.metric("Estimated", f"{est_hours}h")
            h_col2.metric("Logged", f"{actual_hours:.1f}h")
            diff_delta = actual_hours - est_hours
            h_col3.metric("Difference", f"{abs(diff_delta):.1f}h",
                delta=f"{'Over' if diff_delta > 0 else 'Under'} by {abs(diff_delta):.1f}h", delta_color="inverse")

            with st.expander("✏️ Log Progress", expanded=False):
                log_col1, log_col2 = st.columns(2)
                new_hours = log_col1.number_input("Actual hours spent so far", min_value=0.0, max_value=200.0, value=actual_hours, step=0.25, key=f"hours_{aid}")
                diff_index = DIFFICULTY_OPTIONS.index(actual_diff) if actual_diff in DIFFICULTY_OPTIONS else 1
                new_diff = log_col2.select_slider("Actual difficulty", options=DIFFICULTY_OPTIONS, value=DIFFICULTY_OPTIONS[diff_index], key=f"diff_{aid}")
                new_pct = st.slider("% Completed", min_value=0, max_value=100, value=int(pct), step=5, key=f"pct_{aid}",
                    help="Drag to set how much of this assignment you have completed. This drives the progress bar above.")

                if st.button("💾 Save Progress", key=f"save_{aid}", use_container_width=True):
                    upsert_assignment_progress(assignment_id=aid, actual_hours=new_hours, actual_difficulty=new_diff, completion_pct=float(new_pct))
                    all_assignments = get_all_assignments()
                    all_progress = get_all_progress()
                    blocked = get_blocked_days()
                    adjusted = []
                    for asn in all_assignments:
                        prog = all_progress.get(asn["id"], {})
                        done_pct = float(prog.get("completion_pct", 0)) / 100.0
                        remaining_hours = round(float(asn["est_hours"]) * (1.0 - done_pct), 2)
                        if remaining_hours > 0:
                            adjusted.append({**asn, "est_hours": remaining_hours})
                    new_sessions = generate_schedule(adjusted, blocked, user_profile=get_user_profile() or None)
                    save_study_sessions(new_sessions)
                    st.session_state.cal_month_offset = 0
                    st.success("Progress saved and schedule updated!")
                    st.rerun()


def _render_summary(assignments: list, progress: dict) -> None:
    st.subheader("📊 Overview")
    total = len(assignments)
    if total == 0:
        return
    total_est = sum(float(a["est_hours"]) for a in assignments)
    total_actual = sum(float(p.get("actual_hours", 0)) for p in progress.values())
    over_count = sum(1 for a in assignments if progress.get(a["id"], {}).get("actual_hours", 0) > a["est_hours"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Assignments", total)
    c2.metric("Total Est. Hours", f"{total_est:.1f}h")
    c3.metric("Total Logged Hours", f"{total_actual:.1f}h")
    c4.metric("Running Over Estimate", over_count)


def render_dashboard_page() -> None:
    st.header("📈 Progress Dashboard")
    st.caption("Track your study sessions, log actual time, and see how your estimates compare.")
    assignments = get_all_assignments()
    progress = get_all_progress()
    completed_ids = get_completed_session_ids()
    _render_summary(assignments, progress)
    st.divider()
    _render_today(completed_ids)
    st.divider()
    _render_assignment_cards(assignments, progress, completed_ids)
