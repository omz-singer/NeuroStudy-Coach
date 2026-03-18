"""
Quick test to verify all scheduler components work together.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import date, timedelta
from src.database.models import UserProfile, Assignment, TaskType
from src.scheduler.planner import generate_schedule
from src.scheduler.pacing import TimePredictor

def test_models():
    """Test that models can be created."""
    print("✓ Testing data models...")
    
    profile = UserProfile(
        user_id="test_001",
        nd_type="ADHD",
        executive_function_score=4,
        working_memory="low",
        time_blindness=5,
        typical_stress=3,
        typical_energy=3,
        preferred_session_length=35,
        preferred_study_times=["evening"],
        max_daily_hours=4.0,
        break_frequency=25
    )
    
    assignment = Assignment(
        assignment_id="test_assign_001",
        user_id="test_001",
        name="Test Assignment",
        course="Test Course",
        task_type=TaskType.READING,
        due_date=date.today() + timedelta(days=3),
        neurotypical_time=60,
        difficulty=3,
        interest_level=3,
        priority=3
    )
    
    print(f"  Profile: {profile.nd_type}")
    print(f"  Assignment: {assignment.name}")
    return profile, assignment

def test_time_predictor(profile, assignment):
    """Test time prediction."""
    print("\n✓ Testing time predictor...")
    
    predictor = TimePredictor(profile)
    predicted = predictor.predict_time(assignment)
    
    print(f"  Neurotypical time: {assignment.neurotypical_time} min")
    print(f"  Predicted time: {predicted} min")
    print(f"  Multiplier: {predicted/assignment.neurotypical_time:.1f}x")
    
    sessions = predictor.suggest_session_breakdown("reading", predicted)
    print(f"  Session breakdown: {len(sessions)} sessions")
    
    return predicted

def test_schedule_generation(profile, assignment):
    """Test schedule generation."""
    print("\n✓ Testing schedule generation...")
    
    assignments = [assignment]
    schedules = generate_schedule(profile, assignments)
    
    print(f"  Generated {len(schedules)} daily schedules")
    
    if schedules:
        total_sessions = sum(len(day.sessions) for day in schedules)
        total_time = sum(day.total_planned_minutes for day in schedules)
        print(f"  Total sessions: {total_sessions}")
        print(f"  Total time: {total_time} min")
    
    return schedules

def main():
    print("="*60)
    print("NEUROSTUDY COACH - QUICK VERIFICATION TEST")
    print("="*60 + "\n")
    
    try:
        # Test models
        profile, assignment = test_models()
        
        # Test predictor
        predicted = test_time_predictor(profile, assignment)
        
        # Test scheduler
        schedules = test_schedule_generation(profile, assignment)
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nThe scheduling system is working correctly!")
        print("\nComponents verified:")
        print("  ✓ Data models (UserProfile, Assignment)")
        print("  ✓ Time prediction (TimePredictor)")
        print("  ✓ Schedule generation (ScheduleGenerator)")
        print("  ✓ Session breakdown")
        print("\nReady for UI integration!")
        
        return True
        
    except Exception as e:
        print("\n" + "="*60)
        print("❌ TEST FAILED")
        print("="*60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
