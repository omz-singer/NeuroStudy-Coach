"""
Demonstration of the complete scheduling system.
Shows how the scheduler works with example assignments.
"""

from datetime import date, timedelta
from src.database.models import UserProfile, Assignment, TaskType, CompletionStatus
from src.scheduler.planner import ScheduleGenerator


def create_sample_user_profile():
    """Create a sample ADHD student profile."""
    return UserProfile(
        user_id="demo_user_001",
        nd_type="ADHD",
        executive_function_score=4,
        working_memory="low",
        time_blindness=5,
        typical_stress=3,
        typical_energy=3,
        preferred_session_length=35,
        preferred_study_times=["evening", "afternoon"],
        max_daily_hours=4.0,
        break_frequency=25
    )


def create_sample_assignments():
    """Create sample assignments for testing."""
    today = date.today()
    
    assignments = [
        Assignment(
            assignment_id="assign_001",
            user_id="demo_user_001",
            name="Read Chapters 5-7 (Psychology)",
            course="Introduction to Psychology",
            task_type=TaskType.READING,
            due_date=today + timedelta(days=3),
            neurotypical_time=90,  # Instructor estimates 90 min
            difficulty=3,
            interest_level=4,  # Pretty interesting!
            priority=4
        ),
        Assignment(
            assignment_id="assign_002",
            user_id="demo_user_001",
            name="Math Problem Set 8",
            course="Calculus I",
            task_type=TaskType.PROBLEM_SETS,
            due_date=today + timedelta(days=2),
            neurotypical_time=120,
            difficulty=5,
            interest_level=2,  # Not very interesting
            priority=5,  # High priority - due soon!
            status=CompletionStatus.IN_PROGRESS,
            time_spent=30  # Already spent 30 min
        ),
        Assignment(
            assignment_id="assign_003",
            user_id="demo_user_001",
            name="Essay: The American Revolution",
            course="U.S. History",
            task_type=TaskType.WRITING,
            due_date=today + timedelta(days=7),
            neurotypical_time=180,  # 3 hours
            difficulty=4,
            interest_level=5,  # Super interesting topic!
            priority=3
        ),
        Assignment(
            assignment_id="assign_004",
            user_id="demo_user_001",
            name="Review for Midterm",
            course="Biology",
            task_type=TaskType.REVIEW,
            due_date=today + timedelta(days=5),
            neurotypical_time=150,
            difficulty=4,
            interest_level=3,
            priority=5
        ),
        Assignment(
            assignment_id="assign_005",
            user_id="demo_user_001",
            name="Lab Report: Chemical Reactions",
            course="Chemistry",
            task_type=TaskType.PROJECTS,
            due_date=today + timedelta(days=10),
            neurotypical_time=240,  # 4 hours
            difficulty=5,
            interest_level=2,
            priority=3
        )
    ]
    
    return assignments


def print_schedule(daily_schedules, user_profile):
    """Pretty print the generated schedule."""
    print("\n" + "="*80)
    print("GENERATED STUDY SCHEDULE")
    print("="*80)
    print(f"Student Profile: {user_profile.nd_type}")
    print(f"Max daily study hours: {user_profile.max_daily_hours}")
    print(f"Preferred session length: {user_profile.preferred_session_length} min")
    print("="*80)
    
    if not daily_schedules:
        print("No sessions scheduled.")
        return
    
    total_study_time = 0
    
    for day_schedule in daily_schedules:
        print(f"\n📅 {day_schedule.date.strftime('%A, %B %d, %Y')}")
        print(f"   Total: {day_schedule.total_planned_minutes} minutes ({day_schedule.total_planned_minutes/60:.1f} hours)")
        print("-" * 80)
        
        for i, session in enumerate(day_schedule.sessions, 1):
            # In real app, would look up assignment details from database
            print(f"   {i}. [{session.planned_time.upper()}] {session.planned_duration} min")
            print(f"      Assignment ID: {session.assignment_id}")
            print(f"      Session ID: {session.session_id[:8]}...")
        
        total_study_time += day_schedule.total_planned_minutes
    
    print("\n" + "="*80)
    print(f"📊 SUMMARY")
    print(f"   Total scheduled days: {len(daily_schedules)}")
    print(f"   Total study time: {total_study_time} minutes ({total_study_time/60:.1f} hours)")
    print(f"   Average per day: {total_study_time/len(daily_schedules):.0f} minutes")
    print("="*80)


def demo_time_predictions():
    """Show time predictions for different scenarios."""
    print("\n" + "="*80)
    print("TIME PREDICTIONS FOR ADHD STUDENT")
    print("="*80)
    
    profile = create_sample_user_profile()
    assignments = create_sample_assignments()
    
    generator = ScheduleGenerator(profile)
    
    print("\n" + "-"*80)
    print("Assignment Predictions:")
    print("-"*80)
    
    for assignment in assignments:
        predicted = generator.predictor.predict_time(assignment)
        multiplier = predicted / assignment.neurotypical_time
        
        print(f"\n{assignment.name}")
        print(f"  Course: {assignment.course}")
        print(f"  Task Type: {assignment.task_type.value}")
        print(f"  Neurotypical estimate: {assignment.neurotypical_time} min")
        print(f"  Predicted for ADHD: {predicted} min ({multiplier:.1f}x)")
        print(f"  Interest: {assignment.interest_level}/5, Difficulty: {assignment.difficulty}/5")
        print(f"  Days until due: {(assignment.due_date - date.today()).days}")
        
        # Show session breakdown
        sessions = generator.predictor.suggest_session_breakdown(
            assignment.task_type.value,
            predicted
        )
        print(f"  Suggested breakdown: {len(sessions)} sessions × {sessions[0] if sessions else 0} min")


def demo_complete_schedule():
    """Generate and display complete schedule."""
    print("\n" + "="*80)
    print("COMPLETE SCHEDULE GENERATION DEMO")
    print("="*80)
    
    # Create profile and assignments
    profile = create_sample_user_profile()
    assignments = create_sample_assignments()
    
    # Generate schedule
    print("\n🔄 Generating schedule...")
    generator = ScheduleGenerator(profile)
    daily_schedules = generator.generate_schedule(assignments)
    
    # Display schedule
    print_schedule(daily_schedules, profile)
    
    # Show detailed breakdown by assignment
    print("\n" + "="*80)
    print("BREAKDOWN BY ASSIGNMENT")
    print("="*80)
    
    # Count sessions per assignment
    assignment_sessions = {}
    for day in daily_schedules:
        for session in day.sessions:
            aid = session.assignment_id
            if aid not in assignment_sessions:
                assignment_sessions[aid] = []
            assignment_sessions[aid].append(session)
    
    for assignment in assignments:
        sessions = assignment_sessions.get(assignment.assignment_id, [])
        if sessions:
            total_time = sum(s.planned_duration for s in sessions)
            print(f"\n{assignment.name}")
            print(f"  Status: {assignment.status.value}")
            print(f"  Due: {assignment.due_date}")
            print(f"  Predicted time: {assignment.predicted_time or generator.predictor.predict_time(assignment)} min")
            print(f"  Scheduled: {len(sessions)} sessions, {total_time} min total")
            print(f"  Dates: {sessions[0].planned_date} to {sessions[-1].planned_date}")


def demo_adaptive_learning():
    """Show how the system learns from actual performance."""
    print("\n" + "="*80)
    print("ADAPTIVE LEARNING DEMONSTRATION")
    print("="*80)
    
    profile = create_sample_user_profile()
    generator = ScheduleGenerator(profile)
    
    # Create an assignment
    assignment = Assignment(
        assignment_id="learn_demo_001",
        user_id=profile.user_id,
        name="Reading Assignment",
        course="Test Course",
        task_type=TaskType.READING,
        due_date=date.today() + timedelta(days=5),
        neurotypical_time=60,
        difficulty=3,
        interest_level=2,
        priority=3
    )
    
    print("\n📖 Assignment: 60-minute reading (neurotypical estimate)")
    
    # Initial prediction
    initial_prediction = generator.predictor.predict_time(assignment)
    print(f"\n1️⃣  Initial prediction (no history): {initial_prediction} min")
    
    # Simulate: student actually took 120 minutes
    print(f"\n✅ Student completes it: Actually took 120 minutes")
    
    # Record feedback
    generator.predictor.history.append({
        "task_type": "reading",
        "predicted_time": initial_prediction,
        "actual_time": 120,
        "interest": 2,
        "stress": 3
    })
    
    # Create similar assignment
    assignment2 = Assignment(
        assignment_id="learn_demo_002",
        user_id=profile.user_id,
        name="Another Reading Assignment",
        course="Test Course",
        task_type=TaskType.READING,
        due_date=date.today() + timedelta(days=5),
        neurotypical_time=60,
        difficulty=3,
        interest_level=2,
        priority=3
    )
    
    # New prediction with learning
    new_prediction = generator.predictor.predict_time(assignment2)
    print(f"\n2️⃣  New prediction (after 1 data point): {new_prediction} min")
    print(f"     (Model hasn't adapted yet - needs 3+ data points)")
    
    # Add more history
    for i in range(3):
        generator.predictor.history.append({
            "task_type": "reading",
            "predicted_time": initial_prediction,
            "actual_time": 115 + i * 5,
            "interest": 2,
            "stress": 3
        })
    
    # Predict again
    final_prediction = generator.predictor.predict_time(assignment2)
    print(f"\n3️⃣  Final prediction (after 4 data points): {final_prediction} min")
    print(f"     Model learned! Adjusted based on actual performance.")
    
    improvement = abs(120 - final_prediction)
    print(f"\n📈 Prediction improvement: Now only {improvement} min off from actual performance!")


if __name__ == "__main__":
    print("\n" + "🧠 NEUROSTUDY COACH - SCHEDULING SYSTEM DEMO " + "🧠")
    
    # Run all demos
    demo_time_predictions()
    demo_complete_schedule()
    demo_adaptive_learning()
    
    print("\n" + "="*80)
    print("✅ DEMO COMPLETE")
    print("="*80)
    print("\nThe scheduling system is now fully operational!")
    print("\nFeatures demonstrated:")
    print("  ✓ Time predictions based on neurodivergent profiles")
    print("  ✓ Contextual adjustments (interest, stress, deadlines)")
    print("  ✓ Optimal session breakdown")
    print("  ✓ Daily schedule generation with workload limits")
    print("  ✓ Priority-based assignment scheduling")
    print("  ✓ Adaptive learning from actual performance")
    print("\nReady to integrate with the UI!")
    print("="*80 + "\n")
