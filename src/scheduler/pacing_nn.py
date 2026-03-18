"""
Neural Network Integration with Scheduler
Updates the TimePredictor to use trained neural network models.
"""

import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from src.utils.neural_network_model import NeuralTimePredictor as NNPredictor
    NEURAL_NETWORK_AVAILABLE = True
except ImportError:
    NEURAL_NETWORK_AVAILABLE = False
    print("Warning: Neural network not available, using baseline multipliers")


# Research-based baseline multipliers (fallback if NN not available)
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


class NeuralTimePredictor:
    """
    Neural network-powered time predictor for neurodivergent students.
    Uses deep learning to learn complex patterns in study behavior.
    """
    
    def __init__(self, user_profile, model_path=None, use_neural_network=True):
        """
        Initialize predictor with optional neural network.
        
        Args:
            user_profile: UserProfile object with neurodivergent characteristics
            model_path: Path to trained neural network model
            use_neural_network: Whether to use neural network (vs baseline)
        """
        self.profile = user_profile
        self.nd_type = user_profile.nd_type
        self.history = []
        
        # Try to load neural network model
        self.nn_model = None
        self.use_nn = use_neural_network and NEURAL_NETWORK_AVAILABLE
        
        if self.use_nn:
            try:
                if model_path and Path(model_path).exists():
                    self.nn_model = NNPredictor(model_path)
                    print(f"✓ Loaded neural network model from {model_path}")
                else:
                    # Try default location
                    default_path = Path(__file__).parent.parent / "data" / "best_model.pth"
                    if default_path.exists():
                        self.nn_model = NNPredictor(str(default_path))
                        print(f"✓ Loaded neural network model from {default_path}")
                    else:
                        print("⚠ No neural network model found, using baseline multipliers")
                        self.use_nn = False
            except Exception as e:
                print(f"⚠ Error loading neural network: {e}")
                print("  Falling back to baseline multipliers")
                self.use_nn = False
    
    def predict_time(self, assignment) -> int:
        """
        Predict how long an assignment will take using neural network.
        
        Args:
            assignment: Assignment object
        
        Returns:
            int: Predicted time in minutes
        """
        task_type = assignment.task_type.value if hasattr(assignment.task_type, 'value') else assignment.task_type
        
        # Use neural network if available
        if self.use_nn and self.nn_model is not None:
            try:
                prediction = self._predict_with_neural_network(assignment, task_type)
                return max(5, prediction)
            except Exception as e:
                print(f"⚠ Neural network prediction failed: {e}")
                print("  Falling back to baseline method")
        
        # Fallback to baseline method
        return self._predict_with_baseline(assignment, task_type)
    
    def _predict_with_neural_network(self, assignment, task_type: str) -> int:
        """Use neural network for prediction."""
        # Prepare features for neural network
        features = {
            'nd_profile': self.nd_type,
            'executive_function_score': self.profile.executive_function_score,
            'working_memory': self.profile.working_memory,
            'subject': assignment.course if hasattr(assignment, 'course') else 'General',
            'task_type': task_type,
            'neurotypical_base_minutes': assignment.neurotypical_time,
            'difficulty': assignment.difficulty,
            'interest_level': assignment.interest_level,
            'days_until_due': (assignment.due_date - datetime.now().date()).days,
            'time_of_day': self._get_preferred_time(),
            'stress_level': self.profile.typical_stress,
            'energy_level': self.profile.typical_energy
        }
        
        # Get neural network prediction
        multiplier = self.nn_model.predict(features)
        
        # Apply personal learning adjustment if we have history
        if self.history:
            personal_adj = self._personal_adjustment(task_type)
            multiplier *= personal_adj
        
        predicted_time = int(assignment.neurotypical_time * multiplier)
        
        return predicted_time
    
    def _predict_with_baseline(self, assignment, task_type: str) -> int:
        """Fallback to baseline multiplier method."""
        base_time = assignment.neurotypical_time
        
        # Get base multiplier
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
        
        # Apply personal learning
        if self.history:
            personal_adj = self._personal_adjustment(task_type)
            final_multiplier *= personal_adj
        
        predicted_time = int(base_time * final_multiplier)
        
        return max(5, predicted_time)
    
    def _get_multipliers_for_profile(self):
        """Get baseline multipliers for fallback."""
        if "+" in self.nd_type:
            types = self.nd_type.split("+")
            primary = types[0]
            return BASELINE_MULTIPLIERS.get(primary, BASELINE_MULTIPLIERS["ADHD"])
        return BASELINE_MULTIPLIERS.get(self.nd_type, BASELINE_MULTIPLIERS["ADHD"])
    
    def _interest_adjustment(self, interest_level: int) -> float:
        """Interest adjustment for baseline method."""
        adjustments = {1: 1.5, 2: 1.2, 3: 1.0, 4: 0.85, 5: 0.7}
        return adjustments.get(interest_level, 1.0)
    
    def _stress_adjustment(self, stress_level: int) -> float:
        """Stress adjustment for baseline method."""
        return 1.0 + (stress_level - 3) * 0.15
    
    def _deadline_adjustment(self, days_until: int) -> float:
        """Deadline adjustment for baseline method."""
        if days_until <= 1:
            return 1.8
        elif days_until <= 3:
            return 1.3
        elif days_until <= 7:
            return 1.0
        elif days_until <= 14:
            return 1.2
        else:
            return 1.4
    
    def _personal_adjustment(self, task_type: str) -> float:
        """Learn from actual performance history."""
        task_history = [h for h in self.history if h.get("task_type") == task_type]
        
        if len(task_history) < 3:
            return 1.0
        
        ratios = [
            h["actual_time"] / h["predicted_time"]
            for h in task_history
            if h.get("predicted_time", 0) > 0
        ]
        
        if not ratios:
            return 1.0
        
        avg_ratio = np.mean(ratios)
        return 0.7 + 0.3 * avg_ratio
    
    def _get_preferred_time(self) -> str:
        """Get student's preferred study time."""
        if hasattr(self.profile, 'preferred_study_times') and self.profile.preferred_study_times:
            return self.profile.preferred_study_times[0]
        
        # Default based on neurodivergent type
        if "ADHD" in self.nd_type:
            return "evening"
        elif "Autism" in self.nd_type:
            return "morning"
        else:
            return "afternoon"
    
    def suggest_session_breakdown(self, task_type: str, total_time: int) -> List[int]:
        """
        Suggest optimal session lengths based on profile.
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
        if len(self.history) > 50:
            self.history = self.history[-50:]
    
    def get_model_info(self) -> Dict:
        """Get information about the current model."""
        return {
            "using_neural_network": self.use_nn,
            "model_loaded": self.nn_model is not None,
            "profile": self.nd_type,
            "history_size": len(self.history)
        }


# Legacy functions for backward compatibility
def compute_pacing_multiplier(estimated_minutes: int, actual_minutes: int) -> float:
    """Compute pacing multiplier from actual performance."""
    if estimated_minutes <= 0:
        return 1.0
    return actual_minutes / estimated_minutes


def apply_pacing_to_estimate(base_minutes: int, multiplier: float) -> int:
    """Apply personal pacing multiplier to time estimate."""
    return int(base_minutes * multiplier)


# Alias for backward compatibility
TimePredictor = NeuralTimePredictor
