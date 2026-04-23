"""
NeuroStudy Coach – Streamlit entry point.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from src.config import APP_NAME
from src.db import init_db, get_user_profile
from src.ui.components import render_placeholder_section
from src.ui.assignments import render_assignments_page
from src.ui.schedule import render_schedule_page
from src.ui.dashboard import render_dashboard_page
from src.ui.profile import render_profile_page

# Initialise DB on startup
init_db()

# Page config
st.set_page_config(page_title=APP_NAME, page_icon="📚", layout="wide")

# Check if profile is set up
profile = get_user_profile()

# Sidebar navigation
SECTION_OPTIONS = [
    "Progress Dashboard",
    "Assignments",
    "Study Schedule",
    "Learning Materials",
    "My Profile",
]

st.sidebar.title(APP_NAME)
st.sidebar.markdown("Adaptive study planning for neurodivergent students.")

# Show profile badge in sidebar if set
if profile:
    st.sidebar.markdown(
        f'<div style="background:#1e293b;border-radius:8px;padding:6px 12px;'
        f'margin-bottom:8px;font-size:0.8rem;color:#94a3b8;">'
        f'🧠 Profile: <strong style="color:#e2e8f0">{profile.get("nd_type","—")}</strong></div>',
        unsafe_allow_html=True,
    )

# If no profile set, nudge toward profile page
if not profile:
    st.sidebar.warning("⚠️ Set up your profile to personalise your schedule!")

selected = st.sidebar.radio("Section", SECTION_OPTIONS, label_visibility="collapsed")

# Route to pages
if selected == "Progress Dashboard":
    render_dashboard_page()
elif selected == "Assignments":
    render_assignments_page()
elif selected == "Study Schedule":
    render_schedule_page()
elif selected == "Learning Materials":
    render_placeholder_section("Learning Materials", "Coming soon. Upload and search course materials here.")
elif selected == "My Profile":
    render_profile_page()
