"""
Example: Using ML Models for Study Schedule Prediction
Demonstrates how to integrate trained models into the scheduler.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Simulated model interface (replace with actual trained model)
class StudyTimePredictor:
    """
    Predicts study time needed for neurodivergent students.
    This is a simplified example - real implementation would load trained models.
    """
    
    # Research-based baseline multipliers
    BASELINE_MULTIPLIERS = {
        "ADHD": {"reading": 1.55, "writing": 2.0, "problem_sets": 1.6, "projects": 2.5, "review": 1.7},
        "Autism": {"reading": 1.3, "writing": 1.8, "problem_sets": 1.0, "projects": 2.0, "review": 1.2},
        "Dyslexia": {"reading": 2.75, "writing": 2.15, "problem_sets": 1.05, "projects": 1.4, "review": 2.0},
        "Dyscalculia": {"reading": 1.1, "writing": 1.2, "problem_sets": 2.8, "projects": 1.5, "review": 2.2},
        "ADHD+Anxiety": {"reading": 1.8, "writing": 2.3, "problem_sets": 1.9, "projects": 2.8, "review": 2.0},
    }
    
    def __init__(self, student_profile):
        """
        Initialize predictor for a specific student.
        
        Args:
            student_profile: Dict with keys:
                - nd_type: str (e.g., "ADHD", "Autism")
                - executive_function: int 1-5
                - working_memory: str ("low", "medium", "high")
                - typical_stress: int 1-5
                - typical_energy: int 1-5
        """
        self.profile = student_profile
        self.nd_type = student_profile.get("nd_type", "ADHD")
        self.history = []  # Store actual times for learning
    
    def predict_time(self, assignment):
        """
        Predict how long an assignment will take.
        
        Args:
            assignment: Dict with keys:
                - task_type: str ("reading", "writing", "problem_sets", "projects", "review")
                - neurotypical_time: int (minutes)
                - difficulty: int 1-5
                - interest_level: int 1-5
                - days_until_due: int
                - time_of_day: str (optional)
                - current_stress: int 1-5 (optional)
        
        Returns:
            int: Predicted time in minutes
        """
        base_time = assignment["neurotypical_time"]
        task_type = assignment["task_type"]
        
        # Get base multiplier for profile and task
        multipliers = self.BASELINE_MULTIPLIERS.get(self.nd_type, self.BASELINE_MULTIPLIERS["ADHD"])
        base_mult = multipliers.get(task_type, 1.5)
        
        # Adjust for interest (HUGE factor for ADHD/neurodivergent)
        interest = assignment.get("interest_level", 3)
        interest_factor = self._interest_adjustment(interest)
        
        # Adjust for stress
        stress = assignment.get("current_stress", self.profile.get("typical_stress", 3))
        stress_factor = 1.0 + (stress - 3) * 0.15  # Each point above 3 adds 15%
        
        # Adjust for time until due
        days_until = assignment.get("days_until_due", 7)
        deadline_factor = self._deadline_adjustment(days_until)
        
        # Adjust for difficulty
        difficulty = assignment.get("difficulty", 3)
        difficulty_factor = 1.0 + (difficulty - 3) * 0.1
        
        # Combine factors
        final_multiplier = base_mult * interest_factor * stress_factor * deadline_factor * difficulty_factor
        
        # Apply personal learning from history
        if self.history:
            personal_adj = self._personal_adjustment(task_type)
            final_multiplier *= personal_adj
        
        predicted_time = int(base_time * final_multiplier)
        
        return predicted_time
    
    def _interest_adjustment(self, interest_level):
        """High interest can dramatically reduce time due to hyperfocus."""
        # Interest scale: 1=lowest, 5=highest
        adjustments = {
            1: 1.5,   # Very boring = 50% longer
            2: 1.2,
            3: 1.0,   # Neutral
            4: 0.85,  # Interesting = 15% faster
            5: 0.7    # Very interesting = 30% faster (hyperfocus!)
        }
        return adjustments.get(interest_level, 1.0)
    
    def _deadline_adjustment(self, days_until):
        """Last minute panic OR too-far-away procrastination."""
        if days_until <= 1:
            return 1.8  # Last minute stress
        elif days_until <= 3:
            return 1.3  # Rushed
        elif days_until <= 7:
            return 1.0  # Sweet spot
        elif days_until <= 14:
            return 1.2  # Slight procrastination
        else:
            return 1.4  # Too far, hard to start
    
    def _personal_adjustment(self, task_type):
        """Learn from actual performance history."""
        # Filter history for this task type
        task_history = [h for h in self.history if h["task_type"] == task_type]
        
        if len(task_history) < 3:
            return 1.0  # Not enough data
        
        # Calculate average ratio of actual/predicted
        ratios = [h["actual_time"] / h["predicted_time"] for h in task_history]
        avg_ratio = np.mean(ratios)
        
        # Smooth adjustment (don't overreact to outliers)
        return 0.7 + 0.3 * avg_ratio  # Blend: 70% new data, 30% baseline
    
    def record_actual_time(self, assignment, actual_time, predicted_time):
        """Record actual time for learning."""
        self.history.append({
            "task_type": assignment["task_type"],
            "predicted_time": predicted_time,
            "actual_time": actual_time,
            "interest": assignment.get("interest_level", 3),
            "stress": assignment.get("current_stress", 3)
        })
        
        # Keep only recent history (last 50 sessions)
        if len(self.history) > 50:
            self.history = self.history[-50:]
    
    def get_optimal_study_time(self):
        """Suggest best time of day based on profile."""
        # These could be learned from data
        optimal_times = {
            "ADHD": "evening",  # Often better focus after medication peak
            "Autism": "morning",  # Consistent routine
            "Dyslexia": "morning",  # Best cognitive function
            "Dyscalculia": "late_morning"
        }
        return optimal_times.get(self.nd_type, "late_morning")
    
    def suggest_session_length(self, task_type, total_time):
        """Suggest optimal session length based on profile."""
        # ADHD: shorter sessions
        if "ADHD" in self.nd_type:
            if total_time <= 45:
                return [total_time]  # One session
            else:
                # Break into 25-45 min chunks
                num_sessions = (total_time + 35) // 40
                session_len = total_time // num_sessions
                return [session_len] * num_sessions
        
        # Autism: longer, focused sessions
        elif "Autism" in self.nd_type:
            if total_time <= 90:
                return [total_time]
            else:
                # 60-90 min sessions
                num_sessions = (total_time + 60) // 75
                session_len = total_time // num_sessions
                return [session_len] * num_sessions
        
        # Default: 45-60 min sessions
        else:
            if total_time <= 60:
                return [total_time]
            num_sessions = (total_time + 45) // 50
            session_len = total_time // num_sessions
            return [session_len] * num_sessions


def example_usage():
    """Demonstrate predictor usage."""
    print("="*70)
    print("Study Time Predictor - Example Usage")
    print("="*70)
    
    # Create student profile
    student = {
        "nd_type": "ADHD",
        "executive_function": 4,
        "working_memory": "low",
        "typical_stress": 3,
        "typical_energy": 3
    }
    
    predictor = StudyTimePredictor(student)
    
    # Example assignments
    assignments = [
        {
            "name": "Chapter 5-7 Reading (boring textbook)",
            "task_type": "reading",
            "neurotypical_time": 60,
            "difficulty": 3,
            "interest_level": 1,  # Very boring!
            "days_until_due": 2
        },
        {
            "name": "Creative Writing Essay (favorite topic)",
            "task_type": "writing",
            "neurotypical_time": 120,
            "difficulty": 4,
            "interest_level": 5,  # Love this topic!
            "days_until_due": 5
        },
        {
            "name": "Math Problem Set",
            "task_type": "problem_sets",
            "neurotypical_time": 90,
            "difficulty": 4,
            "interest_level": 3,
            "days_until_due": 1,  # Due tomorrow!
            "current_stress": 5
        }
    ]
    
    # Predict time for each
    print("\nPredictions:")
    print("-" * 70)
    for assignment in assignments:
        predicted = predictor.predict_time(assignment)
        neurotypical = assignment["neurotypical_time"]
        multiplier = predicted / neurotypical
        
        print(f"\n{assignment['name']}")
        print(f"  Neurotypical estimate: {neurotypical} minutes")
        print(f"  Predicted for ADHD student: {predicted} minutes ({multiplier:.1f}x)")
        print(f"  Interest level: {assignment['interest_level']}/5")
        print(f"  Days until due: {assignment['days_until_due']}")
        
        # Suggest session breakdown
        sessions = predictor.suggest_session_length(assignment["task_type"], predicted)
        print(f"  Suggested sessions: {len(sessions)} × {sessions[0]} min")
    
    # Demonstrate learning from feedback
    print("\n" + "="*70)
    print("Learning from Actual Performance")
    print("="*70)
    
    # Simulate: student actually takes 150 minutes on reading (vs predicted ~90)
    assignment_1 = assignments[0]
    predicted_1 = predictor.predict_time(assignment_1)
    actual_1 = 150
    
    print(f"\nFirst reading assignment:")
    print(f"  Predicted: {predicted_1} min")
    print(f"  Actual: {actual_1} min")
    
    predictor.record_actual_time(assignment_1, actual_1, predicted_1)
    
    # Now predict similar assignment - should be adjusted
    assignment_2 = {
        "name": "Chapter 8-10 Reading",
        "task_type": "reading",
        "neurotypical_time": 60,
        "difficulty": 3,
        "interest_level": 1,
        "days_until_due": 3
    }
    
    predicted_2 = predictor.predict_time(assignment_2)
    print(f"\nSecond similar reading assignment:")
    print(f"  Predicted: {predicted_2} min")
    print(f"  (Model learned from first assignment and adjusted)")
    
    print("\n" + "="*70)
    print("Recommendations")
    print("="*70)
    print(f"Best study time: {predictor.get_optimal_study_time()}")
    print(f"Session length: Short bursts (25-45 min) for ADHD")
    print(f"Strategy: Schedule high-interest tasks when energy is low")
    

def integrate_with_scheduler_example():
    """Show how to integrate with scheduler/planner.py."""
    print("\n" + "="*70)
    print("Integration with Scheduler")
    print("="*70)
    
    print("""
    # In scheduler/planner.py
    
    from utils.model_usage_example import StudyTimePredictor
    
    def generate_schedule(user_id, assignments, preferences):
        # Load user profile
        user_profile = get_user_profile(user_id)
        
        # Create predictor
        predictor = StudyTimePredictor(user_profile)
        
        # For each assignment, predict realistic time
        scheduled_tasks = []
        for assignment in assignments:
            predicted_time = predictor.predict_time(assignment)
            sessions = predictor.suggest_session_length(
                assignment['task_type'], 
                predicted_time
            )
            
            # Schedule sessions based on optimal times
            optimal_time = predictor.get_optimal_study_time()
            
            for session_duration in sessions:
                scheduled_tasks.append({
                    'assignment': assignment,
                    'duration': session_duration,
                    'preferred_time': optimal_time
                })
        
        # Pack into calendar considering constraints
        schedule = pack_into_calendar(scheduled_tasks, preferences)
        
        return schedule
    """)
    

if __name__ == "__main__":
    example_usage()
    integrate_with_scheduler_example()
    
    print("\n" + "="*70)
    print("Next Steps")
    print("="*70)
    print("""
    1. Replace simplified model with actual trained RandomForest/GradientBoosting
    2. Add database persistence for user history
    3. Implement feedback collection in UI
    4. Add confidence intervals to predictions
    5. Create dashboard showing prediction accuracy over time
    6. A/B test different scheduling strategies
    """)
