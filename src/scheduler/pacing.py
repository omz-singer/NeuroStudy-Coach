"""
Personalized pacing based on study session feedback.
Learns from actual performance to improve future time estimates.
"""

import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta


# Research-based baseline multipliers by neurodivergent type and task
BASELINE_MULTIPLIERS = {
    "ADHD": {
        "reading": 1.55,
        "writing": 2.0,
        "problem_sets": 1.6,
        "projects": 2.5,
        "review": 1.7
    },
    "Autism": {
        "reading": 1.3,
        "writing": 1.8,
        "problem_sets": 1.0,
        "projects": 2.0,
        "review": 1.2
    },
    "Dyslexia": {
        "reading": 2.75,
        "writing": 2.15,
        "problem_sets": 1.05,
        "projects": 1.4,
        "review": 2.0
    },
    "Dyscalculia": {
        "reading": 1.1,
        "writing": 1.2,
        "problem_sets": 2.8,
        "projects": 1.5,
        "review": 2.2
    }
}


class TimePredictor:
    """Predicts study time needed for neurodivergent students."""
    
    def __init__(self, user_profile):
        """
        Initialize predictor for a specific student.
        
        Args:
            user_profile: UserProfile object with neurodivergent characteristics
        """
        self.profile = user_profile
        self.nd_type = user_profile.nd_type
        self.history = []  # Will be populated from database
    
    def predict_time(self, assignment) -> int:
        """
        Predict how long an assignment will take.
        
        Args:
            assignment: Assignment object
        
        Returns:
            int: Predicted time in minutes
        """
        base_time = assignment.neurotypical_time
        task_type = assignment.task_type.value if hasattr(assignment.task_type, 'value') else assignment.task_type
        
        # Get base multiplier for profile and task
        multipliers = self._get_multipliers_for_profile()
        base_mult = multipliers.get(task_type, 1.5)
        
        # Apply contextual adjustments
        interest_factor = self._interest_adjustment(assignment.interest_level)
        stress_factor = self._stress_adjustment(self.profile.typical_stress)
        deadline_factor = self._deadline_adjustment(
            (assignment.due_date - datetime.now().date()).days
        )
        difficulty_factor = 1.0 + (assignment.difficulty - 3) * 0.1
        
        # Combine factors
        final_multiplier = base_mult * interest_factor * stress_factor * deadline_factor * difficulty_factor
        
        # Apply personal learning from history
        if self.history:
            personal_adj = self._personal_adjustment(task_type)
            final_multiplier *= personal_adj
        
        predicted_time = int(base_time * final_multiplier)
        
        return max(5, predicted_time)  # Minimum 5 minutes
    
    def _get_multipliers_for_profile(self):
        """Get baseline multipliers, handling combined profiles."""
        if "+" in self.nd_type:
            # Combined conditions: average the multipliers
            types = self.nd_type.split("+")
            primary = types[0]
            return BASELINE_MULTIPLIERS.get(primary, BASELINE_MULTIPLIERS["ADHD"])
        return BASELINE_MULTIPLIERS.get(self.nd_type, BASELINE_MULTIPLIERS["ADHD"])
    
    def _interest_adjustment(self, interest_level: int) -> float:
        """High interest can dramatically reduce time due to hyperfocus."""
        adjustments = {1: 1.5, 2: 1.2, 3: 1.0, 4: 0.85, 5: 0.7}
        return adjustments.get(interest_level, 1.0)
    
    def _stress_adjustment(self, stress_level: int) -> float:
        """Stress impacts neurodivergent performance significantly."""
        return 1.0 + (stress_level - 3) * 0.15
    
    def _deadline_adjustment(self, days_until: int) -> float:
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
    
    def _personal_adjustment(self, task_type: str) -> float:
        """Learn from actual performance history."""
        task_history = [h for h in self.history if h.get("task_type") == task_type]
        
        if len(task_history) < 3:
            return 1.0  # Not enough data
        
        # Calculate average ratio of actual/predicted
        ratios = [
            h["actual_time"] / h["predicted_time"]
            for h in task_history
            if h.get("predicted_time", 0) > 0
        ]
        
        if not ratios:
            return 1.0
        
        avg_ratio = np.mean(ratios)
        
        # Smooth adjustment (don't overreact to outliers)
        return 0.7 + 0.3 * avg_ratio
    
    def suggest_session_breakdown(self, task_type: str, total_time: int) -> List[int]:
        """
        Suggest optimal session lengths based on profile.
        
        Args:
            task_type: Type of task
            total_time: Total predicted time in minutes
        
        Returns:
            List of session durations in minutes
        """
        # ADHD: shorter sessions
        if "ADHD" in self.nd_type:
            target_length = 35
            if total_time <= 45:
                return [total_time]
            num_sessions = max(1, (total_time + target_length - 1) // target_length)
            session_len = total_time // num_sessions
            return [session_len] * num_sessions
        
        # Autism: longer, focused sessions
        elif "Autism" in self.nd_type:
            target_length = 75
            if total_time <= 90:
                return [total_time]
            num_sessions = max(1, (total_time + target_length - 1) // target_length)
            session_len = total_time // num_sessions
            return [session_len] * num_sessions
        
        # Default: medium sessions
        else:
            target_length = 50
            if total_time <= 60:
                return [total_time]
            num_sessions = max(1, (total_time + target_length - 1) // target_length)
            session_len = total_time // num_sessions
            return [session_len] * num_sessions
    
    def load_history(self, sessions: List[Dict]):
        """Load historical session data for learning."""
        self.history = sessions
    
    def record_session_feedback(self, session_data: Dict):
        """Record actual session outcome for learning."""
        self.history.append(session_data)
        # Keep only recent history
        if len(self.history) > 50:
            self.history = self.history[-50:]


def compute_pacing_multiplier(estimated_minutes: int, actual_minutes: int) -> float:
    """
    Compute pacing multiplier from actual performance.
    
    Args:
        estimated_minutes: Predicted time
        actual_minutes: Actual time taken
    
    Returns:
        float: Multiplier (actual/estimated)
    """
    if estimated_minutes <= 0:
        return 1.0
    return actual_minutes / estimated_minutes


def apply_pacing_to_estimate(base_minutes: int, multiplier: float) -> int:
    """
    Apply personal pacing multiplier to time estimate.
    
    Args:
        base_minutes: Base time estimate
        multiplier: Personal pacing multiplier
    
    Returns:
        int: Adjusted time estimate
    """
    return int(base_minutes * multiplier)
