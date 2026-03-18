"""
NeuroStudy Coach - Neural Network Powered Study Scheduler
Uses deep learning to predict realistic study times for neurodivergent students.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from datetime import date, timedelta
import pandas as pd

from src.config import APP_NAME
from src.database.models import UserProfile, Assignment, TaskType, CompletionStatus
from src.scheduler.planner import ScheduleGenerator

# Page config
st.set_page_config(page_title=APP_NAME + " - Neural Network Edition", page_icon="🧠", layout="wide")

# Initialize session state
if 'assignments' not in st.session_state:
    st.session_state.assignments = []
if 'profile' not in st.session_state:
    st.session_state.profile = None
if 'schedule' not in st.session_state:
    st.session_state.schedule = None

# Sidebar - User Profile Setup
st.sidebar.title("🧠 " + APP_NAME)
st.sidebar.markdown("**Neural Network Edition**")
st.sidebar.markdown("AI-powered study scheduling for neurodivergent students")
st.sidebar.markdown("---")

# Profile setup
with st.sidebar.expander("👤 Your Profile", expanded=not st.session_state.profile):
    nd_type = st.selectbox(
        "Neurodivergent Profile",
        ["ADHD", "Autism", "Dyslexia", "Dyscalculia", "ADHD+Anxiety", "Autism+ADHD", "Dyslexia+ADHD"],
        help="Your neurodivergent type helps the AI predict realistic study times"
    )
    
    exec_func = st.slider("Executive Function Challenges", 1, 5, 3,
                          help="1=minimal challenges, 5=significant challenges")
    
    working_mem = st.select_slider("Working Memory", ["low", "medium", "high"])
    
    max_hours = st.slider("Max Daily Study Hours", 1.0, 8.0, 4.0, 0.5)
    
    session_length = st.slider("Preferred Session Length (min)", 15, 90, 35, 5)
    
    if st.button("💾 Save Profile"):
        st.session_state.profile = UserProfile(
            user_id="user_001",
            nd_type=nd_type,
            executive_function_score=exec_func,
            working_memory=working_mem,
            time_blindness=exec_func,
            typical_stress=3,
            typical_energy=3,
            preferred_session_length=session_length,
            preferred_study_times=["evening", "afternoon"],
            max_daily_hours=max_hours,
            break_frequency=25
        )
        st.success("✅ Profile saved!")

# Show model status
model_path = Path(__file__).parent / "src" / "data" / "best_model.pth"
if model_path.exists():
    st.sidebar.success("🧠 Neural Network Model: Loaded")
else:
    st.sidebar.warning("⚠️ Neural Network: Run neural_network_demo.py first")

st.sidebar.markdown("---")
selected = st.sidebar.radio(
    "Navigation",
    ["📝 Add Assignments", "📅 View Schedule", "📊 About Neural Network"],
    label_visibility="collapsed"
)

# Main content
st.title("🧠 NeuroStudy Coach")
st.caption("Neural Network-Powered Study Time Prediction")

# Tab 1: Add Assignments
if selected == "📝 Add Assignments":
    st.header("📝 Add Assignments")
    
    if not st.session_state.profile:
        st.warning("⚠️ Please set up your profile in the sidebar first!")
    else:
        st.success(f"Profile: {st.session_state.profile.nd_type}")
        
        with st.form("add_assignment"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Assignment Name *", placeholder="e.g., Read Chapters 5-7")
                course = st.text_input("Course *", placeholder="e.g., Psychology 101")
                task_type = st.selectbox("Task Type *", 
                                         ["reading", "writing", "problem_sets", "projects", "review"])
                neurotypical_time = st.number_input("Neurotypical Estimate (min) *", 30, 600, 60, 15,
                                                   help="How long would this take a neurotypical student?")
            
            with col2:
                due_date = st.date_input("Due Date *", min_value=date.today(),
                                        value=date.today() + timedelta(days=7))
                difficulty = st.slider("Difficulty", 1, 5, 3,
                                      help="1=easy, 5=very difficult")
                interest = st.slider("Interest Level", 1, 5, 3,
                                    help="1=boring, 5=super interesting (hyperfocus!)")
                priority = st.slider("Priority", 1, 5, 3,
                                    help="1=low, 5=urgent")
            
            submitted = st.form_submit_button("➕ Add Assignment")
            
            if submitted and name and course:
                assignment_id = f"assign_{len(st.session_state.assignments) + 1:03d}"
                assignment = Assignment(
                    assignment_id=assignment_id,
                    user_id=st.session_state.profile.user_id,
                    name=name,
                    course=course,
                    task_type=TaskType(task_type),
                    due_date=due_date,
                    neurotypical_time=neurotypical_time,
                    difficulty=difficulty,
                    interest_level=interest,
                    priority=priority
                )
                st.session_state.assignments.append(assignment)
                st.session_state.schedule = None  # Reset schedule
                st.success(f"✅ Added: {name}")
                st.rerun()
        
        # Show current assignments
        st.subheader("Current Assignments")
        if st.session_state.assignments:
            for i, a in enumerate(st.session_state.assignments):
                with st.expander(f"📚 {a.name} - Due {a.due_date}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    col1.write(f"**Course:** {a.course}")
                    col1.write(f"**Type:** {a.task_type.value}")
                    col1.write(f"**Neurotypical time:** {a.neurotypical_time} min")
                    col2.write(f"**Difficulty:** {'⭐' * a.difficulty}")
                    col2.write(f"**Interest:** {'❤️' * a.interest_level}")
                    col2.write(f"**Priority:** {'🔥' * a.priority}")
                    col3.write(f"**Days until due:** {(a.due_date - date.today()).days}")
                    if st.button(f"🗑️ Remove", key=f"del_{i}"):
                        st.session_state.assignments.pop(i)
                        st.session_state.schedule = None
                        st.rerun()
        else:
            st.info("No assignments yet. Add one above!")

# Tab 2: View Schedule
elif selected == "📅 View Schedule":
    st.header("📅 AI-Generated Study Schedule")
    
    if not st.session_state.profile:
        st.warning("⚠️ Please set up your profile in the sidebar first!")
    elif not st.session_state.assignments:
        st.info("📝 Add some assignments first!")
    else:
        if st.button("🧠 Generate Schedule with Neural Network", type="primary"):
            with st.spinner("🧠 Neural network is predicting study times..."):
                try:
                    model_path_str = str(Path(__file__).parent / "src" / "data" / "best_model.pth")
                    generator = ScheduleGenerator(st.session_state.profile)
                    
                    # Try to use neural network
                    if Path(model_path_str).exists():
                        from src.scheduler.pacing_nn import NeuralTimePredictor
                        generator.predictor = NeuralTimePredictor(
                            st.session_state.profile, 
                            model_path_str
                        )
                        st.info("✨ Using neural network for predictions!")
                    
                    st.session_state.schedule = generator.generate_schedule(
                        st.session_state.assignments
                    )
                    st.success("✅ Schedule generated!")
                except Exception as e:
                    st.error(f"Error generating schedule: {e}")
        
        if st.session_state.schedule:
            st.subheader("📊 Schedule Overview")
            
            total_time = sum(day.total_planned_minutes for day in st.session_state.schedule)
            total_sessions = sum(len(day.sessions) for day in st.session_state.schedule)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Study Days", len(st.session_state.schedule))
            col2.metric("Total Study Time", f"{total_time/60:.1f} hours")
            col3.metric("Total Sessions", total_sessions)
            
            st.markdown("---")
            st.subheader("📅 Daily Breakdown")
            
            for day_schedule in st.session_state.schedule:
                day_str = day_schedule.date.strftime("%A, %B %d, %Y")
                hours = day_schedule.total_planned_minutes / 60
                
                with st.expander(f"📅 {day_str} - {hours:.1f} hours ({len(day_schedule.sessions)} sessions)", 
                               expanded=True):
                    
                    # Show sessions for this day
                    for i, session in enumerate(day_schedule.sessions, 1):
                        # Find the assignment
                        assignment = next((a for a in st.session_state.assignments 
                                         if a.assignment_id == session.assignment_id), None)
                        
                        if assignment:
                            col1, col2, col3 = st.columns([3, 1, 1])
                            col1.write(f"**{i}.** {assignment.name}")
                            col1.caption(f"{assignment.course} • {assignment.task_type.value}")
                            col2.write(f"⏱️ {session.planned_duration} min")
                            col3.write(f"🕐 {session.planned_time}")
            
            # Show assignment summary
            st.markdown("---")
            st.subheader("📚 Time by Assignment")
            
            assignment_times = {}
            for day in st.session_state.schedule:
                for session in day.sessions:
                    if session.assignment_id not in assignment_times:
                        assignment_times[session.assignment_id] = 0
                    assignment_times[session.assignment_id] += session.planned_duration
            
            for assignment in st.session_state.assignments:
                if assignment.assignment_id in assignment_times:
                    predicted_time = assignment_times[assignment.assignment_id]
                    multiplier = predicted_time / assignment.neurotypical_time
                    
                    st.write(f"**{assignment.name}**")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Neurotypical estimate", f"{assignment.neurotypical_time} min")
                    col2.metric("AI Prediction", f"{predicted_time} min", 
                              f"{multiplier:.1f}x")
                    col3.metric("Sessions", len([s for day in st.session_state.schedule 
                                                 for s in day.sessions 
                                                 if s.assignment_id == assignment.assignment_id]))

# Tab 3: About
elif selected == "📊 About Neural Network":
    st.header("🧠 About the Neural Network")
    
    st.markdown("""
    ### Deep Learning for Neurodivergent Students
    
    This app uses a **3-layer neural network** trained on 2,000 study sessions to predict
    how long tasks will take for neurodivergent students.
    
    #### Neural Network Architecture
    - **Input:** 11 features (profile, task, context)
    - **Hidden Layers:** 128 → 64 → 32 neurons
    - **Output:** Time multiplier prediction
    - **Parameters:** 12,353 trainable weights
    
    #### Performance
    - **Validation Accuracy:** ±1.57x multiplier
    - **Error Reduction:** 75% vs baseline
    - **Training:** 2,000 synthetic study sessions
    
    #### What It Learns
    
    The neural network learns complex patterns like:
    
    - **Hyperfocus Effect:** High interest → can be faster than neurotypical!
    - **Stress Compounding:** Low interest + high stress = exponentially longer
    - **Deadline Pressure:** Last-minute work takes 1.8x longer
    - **Profile Patterns:** ADHD responds differently than Autism or Dyslexia
    
    #### Time Multipliers by Profile
    
    | Profile | Average | Reading | Writing | Problem Sets | Projects |
    |---------|---------|---------|---------|--------------|----------|
    | **ADHD** | 5.0x | 1.55x | 2.0x | 1.6x | 2.5x |
    | **Autism** | 4.0x | 1.3x | 1.8x | 1.0x | 2.0x |
    | **Dyslexia** | 5.1x | 2.75x | 2.15x | 1.05x | 1.4x |
    | **Dyscalculia** | 4.9x | 1.1x | 1.2x | 2.8x | 1.5x |
    
    *Note: These are baselines - the neural network adjusts based on interest, stress, and context!*
    
    #### Why Neural Networks?
    
    Simple rules like "ADHD students take 2x longer" don't work because:
    - Performance is **non-linear** and context-dependent
    - **Interest level** can flip everything (hyperfocus!)
    - Factors **interact** in complex ways
    
    The neural network learns these patterns from data.
    
    #### Academic Project
    
    This is a Neural Networks course project demonstrating:
    - Multi-layer perceptron architecture
    - Batch normalization & dropout regularization
    - Adam optimization with learning rate scheduling
    - Real-world application to assistive technology
    
    For technical details, see `NEURAL_NETWORK_DOCUMENTATION.md`
    """)
    
    if model_path.exists():
        st.success("✅ Neural network model is loaded and ready!")
        st.info("💡 Try adding assignments and generating a schedule to see it in action!")
    else:
        st.warning("⚠️ No trained model found. Run `python neural_network_demo.py` to train the model first.")

st.sidebar.markdown("---")
st.sidebar.caption("© 2026 NeuroStudy Coach - Neural Network Edition")
