"""
src/ui/profile.py
Student neurodivergent profile setup page.
This powers the TimePredictor so the scheduler can personalise session lengths
and time estimates for each student's profile.
"""

import streamlit as st
from src.db import get_user_profile, save_user_profile

ND_TYPES = ["ADHD", "Autism", "Dyslexia", "Dyscalculia", "ADHD+Dyslexia", "ADHD+Autism", "Other"]
WORKING_MEMORY = ["low", "medium", "high"]
STUDY_TIMES = ["morning", "afternoon", "evening", "night"]

ND_DESCRIPTIONS = {
    "ADHD":         "Shorter sessions (35 min), higher time multipliers for writing/projects",
    "Autism":       "Longer focused sessions (75 min), reduced time for structured tasks",
    "Dyslexia":     "Extra time for reading/writing tasks (up to 2.75x), standard for maths",
    "Dyscalculia":  "Extra time for problem sets (up to 2.8x), standard for reading",
    "ADHD+Dyslexia":"Combined profile — reading/writing adjustments plus executive function support",
    "ADHD+Autism":  "Combined profile — session length and task adjustments for both",
    "Other":        "Standard cognitive science scheduling with gentle adjustments",
}


def render_profile_page() -> None:
    st.header("👤 My Profile")
    st.caption("Tell us about yourself so the scheduler can personalise your study plan.")

    profile = get_user_profile()
    is_new = not profile

    if is_new:
        st.info("👋 Welcome! Set up your profile to get a personalised study schedule.")

    with st.form("profile_form"):
        st.subheader("🧠 Neurodivergent Profile")

        nd_type = st.selectbox(
            "My profile",
            ND_TYPES,
            index=ND_TYPES.index(profile.get("nd_type", "ADHD")) if profile.get("nd_type") in ND_TYPES else 0,
            help="Select the profile that best describes you. This adjusts time estimates and session lengths."
        )

        if nd_type in ND_DESCRIPTIONS:
            st.caption(f"ℹ️ {ND_DESCRIPTIONS[nd_type]}")

        st.divider()
        st.subheader("⚡ Daily Characteristics")
        st.caption("These help the scheduler adjust for your typical energy and focus levels.")

        col1, col2 = st.columns(2)

        exec_fn = col1.slider(
            "Executive function challenges",
            1, 5,
            value=profile.get("executive_function", 3),
            help="1 = minimal challenges, 5 = significant challenges with task initiation/planning"
        )
        working_mem = col1.select_slider(
            "Working memory",
            options=WORKING_MEMORY,
            value=profile.get("working_memory", "medium"),
        )
        time_blindness = col1.slider(
            "Time blindness",
            1, 5,
            value=profile.get("time_blindness", 3),
            help="How difficult is it to track time passing? 1 = easy, 5 = very difficult"
        )

        typical_stress = col2.slider(
            "Typical stress level",
            1, 5,
            value=profile.get("typical_stress", 3),
            help="Your baseline stress level during the semester"
        )
        typical_energy = col2.slider(
            "Typical energy level",
            1, 5,
            value=profile.get("typical_energy", 3),
            help="Your typical energy during study sessions"
        )

        st.divider()
        st.subheader("📅 Study Preferences")

        pref_col1, pref_col2 = st.columns(2)

        preferred_session_len = pref_col1.number_input(
            "Preferred session length (minutes)",
            min_value=15,
            max_value=120,
            value=profile.get("preferred_session_len", 50),
            step=5,
            help="How long do you like to study in one sitting before a break?"
        )
        max_daily_hours = pref_col1.number_input(
            "Max study hours per day",
            min_value=1.0,
            max_value=12.0,
            value=float(profile.get("max_daily_hours", 4.0)),
            step=0.5,
        )

        preferred_time = pref_col2.select_slider(
            "Best time to study",
            options=STUDY_TIMES,
            value=profile.get("preferred_study_times", "afternoon"),
        )
        break_frequency = pref_col2.number_input(
            "Break frequency (minutes between breaks)",
            min_value=10,
            max_value=120,
            value=profile.get("break_frequency", 50),
            step=5,
        )

        st.divider()
        saved = st.form_submit_button("💾 Save Profile", use_container_width=True, type="primary")

        if saved:
            save_user_profile(
                nd_type=nd_type,
                executive_function=exec_fn,
                working_memory=working_mem,
                time_blindness=time_blindness,
                typical_stress=typical_stress,
                typical_energy=typical_energy,
                preferred_session_len=int(preferred_session_len),
                preferred_study_times=preferred_time,
                max_daily_hours=max_daily_hours,
                break_frequency=int(break_frequency),
            )
            st.success("✅ Profile saved! Your study schedule will now be personalised for your profile.")
            st.rerun()

    # Show current profile summary if set
    if profile and not is_new:
        st.divider()
        st.subheader("📋 Current Profile Summary")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Profile", profile.get("nd_type", "—"))
        c2.metric("Session Length", f"{profile.get('preferred_session_len', 50)} min")
        c3.metric("Max Daily Hours", f"{profile.get('max_daily_hours', 4.0)}h")
        c4.metric("Best Study Time", profile.get("preferred_study_times", "—").capitalize())
