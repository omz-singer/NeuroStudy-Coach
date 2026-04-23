"""
src/ui/assignments.py
Assignments page: manual form entry, PDF syllabus import, edit/delete table.
"""

import re
from datetime import datetime, date, time

import streamlit as st

from src.db import (
    add_assignment,
    get_all_assignments,
    update_assignment,
    delete_assignment,
)

# ── Constants ──────────────────────────────────────────────────────────────────

PRIORITIES = ["Low", "Medium", "High"]
TYPES = ["Essay", "Exam", "Project", "Lab", "Reading", "Other"]

PRIORITY_COLORS = {
    "Low":    "#4ade80",   # green
    "Medium": "#facc15",   # yellow
    "High":   "#f87171",   # red
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def _priority_badge(priority: str) -> str:
    color = PRIORITY_COLORS.get(priority, "#94a3b8")
    return (
        f'<span style="background:{color};color:#0f172a;padding:2px 10px;'
        f'border-radius:999px;font-size:0.75rem;font-weight:700;">'
        f"{priority}</span>"
    )


def _parse_syllabus_text(text: str) -> list[dict]:
    """
    Very lightweight heuristic: look for lines that contain a date-like pattern
    and treat the surrounding text as a potential assignment.
    Returns a list of partial dicts with 'name' and 'due_date_str' keys.
    """
    date_pattern = re.compile(
        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:,?\s*\d{4})?)\b",
        re.IGNORECASE,
    )
    found = []
    for line in text.splitlines():
        m = date_pattern.search(line)
        if m:
            name_part = line[: m.start()].strip(" :-–")
            if len(name_part) > 3:
                found.append({"name": name_part[:120], "due_date_str": m.group()})
    return found[:20]  # cap at 20 suggestions


# ── Sub-sections ───────────────────────────────────────────────────────────────

def _render_add_form() -> None:
    st.subheader("➕ Add Assignment")

    with st.form("add_assignment_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Assignment Name *", placeholder="e.g. Research Paper Draft")
            course = st.text_input("Course *", placeholder="e.g. BIO 201")
            assignment_type = st.selectbox("Type", TYPES)

        with col2:
            due_date = st.date_input("Due Date *", min_value=date.today())
            due_time = st.time_input("Due Time", value=time(23, 59))
            est_hours = st.number_input(
                "Estimated Hours *", min_value=0.5, max_value=200.0, value=2.0, step=0.5
            )

        priority = st.select_slider("Priority", options=PRIORITIES, value="Medium")
        interest_level = st.select_slider(
            "Interest Level",
            options=[1, 2, 3, 4, 5],
            value=3,
            help="How interested are you in this assignment? Higher interest = faster completion. Used to personalise your schedule."
        )

        submitted = st.form_submit_button("💾 Save Assignment", use_container_width=True)

        if submitted:
            if not name.strip() or not course.strip():
                st.error("Assignment Name and Course are required.")
            else:
                due_dt = datetime.combine(due_date, due_time)
                add_assignment(
                    name=name.strip(),
                    course=course.strip(),
                    due_date=due_dt,
                    est_hours=est_hours,
                    priority=priority,
                    assignment_type=assignment_type,
                )
                st.success(f"✅ **{name}** added successfully!")
                st.rerun()


def _render_syllabus_import() -> None:
    with st.expander("📄 Import from Syllabus PDF", expanded=False):
        st.caption(
            "Upload a syllabus PDF and the app will try to detect assignments from it. "
            "You can review and confirm each one before saving."
        )

        uploaded = st.file_uploader("Upload Syllabus PDF", type=["pdf"], key="syllabus_upload")

        if uploaded is not None:
            # Try pdfplumber first, fall back to PyPDF2, then raw bytes decode
            text = ""
            try:
                import pdfplumber
                with pdfplumber.open(uploaded) as pdf:
                    text = "\n".join(p.extract_text() or "" for p in pdf.pages)
            except Exception:
                try:
                    import PyPDF2
                    reader = PyPDF2.PdfReader(uploaded)
                    text = "\n".join(
                        page.extract_text() or "" for page in reader.pages
                    )
                except Exception:
                    st.warning("Could not extract text from this PDF. Try a text-based (non-scanned) PDF.")
                    return

            suggestions = _parse_syllabus_text(text)

            if not suggestions:
                st.info("No assignments with recognisable due dates were found. You can still add them manually above.")
                return

            st.markdown(f"**{len(suggestions)} potential assignment(s) detected.** Review and import:")

            for i, s in enumerate(suggestions):
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 2, 1])
                    imp_name = c1.text_input("Name", value=s["name"], key=f"imp_name_{i}")
                    imp_course = c1.text_input("Course", key=f"imp_course_{i}", placeholder="Fill in course")
                    imp_date_str = c2.text_input("Due date (detected)", value=s["due_date_str"], key=f"imp_date_{i}")
                    imp_hours = c2.number_input("Est. Hours", value=2.0, step=0.5, key=f"imp_hours_{i}", min_value=0.5)
                    imp_priority = c2.selectbox("Priority", PRIORITIES, index=1, key=f"imp_pri_{i}")
                    imp_type = c2.selectbox("Type", TYPES, key=f"imp_type_{i}")

                    if c3.button("Import", key=f"imp_btn_{i}"):
                        try:
                            from dateutil import parser as dateparser
                            due_dt = dateparser.parse(imp_date_str, fuzzy=True)
                        except Exception:
                            due_dt = datetime.combine(date.today(), time(23, 59))

                        if not imp_course.strip():
                            st.error("Please fill in the course name before importing.")
                        else:
                            add_assignment(
                                name=imp_name.strip(),
                                course=imp_course.strip(),
                                due_date=due_dt,
                                est_hours=imp_hours,
                                priority=imp_priority,
                                assignment_type=imp_type,
                            )
                            st.success(f"Imported **{imp_name}**")
                            st.rerun()


def _render_assignment_table() -> None:
    st.subheader("📋 Your Assignments")

    assignments = get_all_assignments()

    if not assignments:
        st.info("No assignments yet — add one above or import from a syllabus.")
        return

    # ── Edit modal stored in session state ──
    if "edit_id" not in st.session_state:
        st.session_state.edit_id = None

    # Edit form (shown above the table when active)
    if st.session_state.edit_id is not None:
        a = next((x for x in assignments if x["id"] == st.session_state.edit_id), None)
        if a:
            st.markdown("---")
            st.markdown("#### ✏️ Edit Assignment")
            with st.form("edit_form"):
                c1, c2 = st.columns(2)
                e_name = c1.text_input("Name", value=a["name"])
                e_course = c1.text_input("Course", value=a["course"])
                e_type = c1.selectbox("Type", TYPES, index=TYPES.index(a["type"]) if a["type"] in TYPES else 0)

                existing_dt = datetime.fromisoformat(a["due_date"])
                e_date = c2.date_input("Due Date", value=existing_dt.date())
                e_time = c2.time_input("Due Time", value=existing_dt.time())
                e_hours = c2.number_input("Est. Hours", value=float(a["est_hours"]), step=0.5, min_value=0.5)
                e_priority = st.select_slider(
                    "Priority", options=PRIORITIES,
                    value=a["priority"] if a["priority"] in PRIORITIES else "Medium"
                )

                save_col, cancel_col = st.columns(2)
                if save_col.form_submit_button("💾 Save Changes", use_container_width=True):
                    update_assignment(
                        assignment_id=a["id"],
                        name=e_name.strip(),
                        course=e_course.strip(),
                        due_date=datetime.combine(e_date, e_time),
                        est_hours=e_hours,
                        priority=e_priority,
                        assignment_type=e_type,
                    )
                    st.session_state.edit_id = None
                    st.rerun()
                if cancel_col.form_submit_button("✖ Cancel", use_container_width=True):
                    st.session_state.edit_id = None
                    st.rerun()
            st.markdown("---")

    # ── Assignment cards ──
    for a in assignments:
        due_dt = datetime.fromisoformat(a["due_date"])
        days_left = (due_dt.date() - date.today()).days
        urgency = "🔴" if days_left <= 2 else "🟡" if days_left <= 7 else "🟢"

        with st.container(border=True):
            left, right = st.columns([5, 1])
            with left:
                st.markdown(
                    f"**{a['name']}** &nbsp;·&nbsp; `{a['course']}` &nbsp;·&nbsp; "
                    f"*{a['type']}* &nbsp; {_priority_badge(a['priority'])}",
                    unsafe_allow_html=True,
                )
                due_label = due_dt.strftime("%b %d, %Y at %I:%M %p")
                if days_left < 0:
                    days_str = f"⚠️ Overdue by {abs(days_left)} day(s)"
                elif days_left == 0:
                    days_str = "⚠️ Due today!"
                else:
                    days_str = f"{urgency} {days_left} day(s) left"

                st.caption(f"📅 {due_label} &nbsp;·&nbsp; {days_str} &nbsp;·&nbsp; ⏱ {a['est_hours']}h estimated")

            with right:
                if st.button("✏️", key=f"edit_{a['id']}", help="Edit"):
                    st.session_state.edit_id = a["id"]
                    st.rerun()
                if st.button("🗑️", key=f"del_{a['id']}", help="Delete"):
                    delete_assignment(a["id"])
                    st.rerun()


# ── Main entry point ───────────────────────────────────────────────────────────

def render_assignments_page() -> None:
    st.header("📚 Assignments")
    st.caption("Track all your assignments in one place. Add them manually or extract them from a syllabus PDF.")

    _render_add_form()
    st.divider()
    _render_syllabus_import()
    st.divider()
    _render_assignment_table()
