"""
Database schema and model definitions for NeuroStudy Coach.
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import List, Optional
from enum import Enum


class TaskType(Enum):
    """Types of academic tasks."""
    READING = "reading"
    WRITING = "writing"
    PROBLEM_SETS = "problem_sets"
    PROJECTS = "projects"
    REVIEW = "review"


class CompletionStatus(Enum):
    """Status of a study session or assignment."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


@dataclass
class UserProfile:
    """User profile with neurodivergent characteristics."""
    user_id: str
    nd_type: str  # "ADHD", "Autism", "Dyslexia", "Dyscalculia", or combinations
    executive_function_score: int  # 1-5, higher = more challenges
    working_memory: str  # "low", "medium", "high"
    time_blindness: int  # 1-5
    typical_stress: int  # 1-5
    typical_energy: int  # 1-5
    
    # Preferences
    preferred_session_length: int  # minutes
    preferred_study_times: List[str]  # ["morning", "afternoon", "evening"]
    max_daily_hours: float  # Maximum study hours per day
    break_frequency: int  # Minutes between breaks
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "nd_type": self.nd_type,
            "executive_function_score": self.executive_function_score,
            "working_memory": self.working_memory,
            "time_blindness": self.time_blindness,
            "typical_stress": self.typical_stress,
            "typical_energy": self.typical_energy,
            "preferred_session_length": self.preferred_session_length,
            "preferred_study_times": self.preferred_study_times,
            "max_daily_hours": self.max_daily_hours,
            "break_frequency": self.break_frequency
        }


@dataclass
class Assignment:
    """An academic assignment or task."""
    assignment_id: str
    user_id: str
    name: str
    course: str
    task_type: TaskType
    due_date: date
    
    # Estimates
    neurotypical_time: int  # minutes (from syllabus/instructor)
    predicted_time: Optional[int] = None  # minutes (calculated for this student)
    
    # Attributes
    difficulty: int = 3  # 1-5
    interest_level: int = 3  # 1-5
    priority: int = 3  # 1-5
    
    # Status
    status: CompletionStatus = CompletionStatus.NOT_STARTED
    completion_percentage: int = 0
    time_spent: int = 0  # minutes actually spent
    
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self):
        return {
            "assignment_id": self.assignment_id,
            "user_id": self.user_id,
            "name": self.name,
            "course": self.course,
            "task_type": self.task_type.value,
            "due_date": self.due_date.isoformat(),
            "neurotypical_time": self.neurotypical_time,
            "predicted_time": self.predicted_time,
            "difficulty": self.difficulty,
            "interest_level": self.interest_level,
            "priority": self.priority,
            "status": self.status.value,
            "completion_percentage": self.completion_percentage,
            "time_spent": self.time_spent,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class StudySession:
    """A planned or completed study session."""
    session_id: str
    assignment_id: str
    user_id: str
    
    # Planning
    planned_date: date
    planned_time: str  # "morning", "afternoon", "evening"
    planned_duration: int  # minutes
    
    # Actual (filled after completion)
    actual_start: Optional[datetime] = None
    actual_duration: Optional[int] = None  # minutes
    completion_percentage: Optional[int] = None
    breaks_taken: Optional[int] = None
    
    # Self-reported feedback
    energy_level: Optional[int] = None  # 1-5
    stress_level: Optional[int] = None  # 1-5
    focus_quality: Optional[int] = None  # 1-5
    
    status: CompletionStatus = CompletionStatus.NOT_STARTED
    notes: Optional[str] = None
    
    def to_dict(self):
        return {
            "session_id": self.session_id,
            "assignment_id": self.assignment_id,
            "user_id": self.user_id,
            "planned_date": self.planned_date.isoformat(),
            "planned_time": self.planned_time,
            "planned_duration": self.planned_duration,
            "actual_start": self.actual_start.isoformat() if self.actual_start else None,
            "actual_duration": self.actual_duration,
            "completion_percentage": self.completion_percentage,
            "breaks_taken": self.breaks_taken,
            "energy_level": self.energy_level,
            "stress_level": self.stress_level,
            "focus_quality": self.focus_quality,
            "status": self.status.value,
            "notes": self.notes
        }


@dataclass
class DailySchedule:
    """A day's worth of study sessions."""
    date: date
    user_id: str
    sessions: List[StudySession]
    total_planned_minutes: int
    
    def to_dict(self):
        return {
            "date": self.date.isoformat(),
            "user_id": self.user_id,
            "sessions": [s.to_dict() for s in self.sessions],
            "total_planned_minutes": self.total_planned_minutes
        }
