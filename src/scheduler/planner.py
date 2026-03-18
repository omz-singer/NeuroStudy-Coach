"""
Adaptive study schedule generation for neurodivergent students.
Distributes assignments into day-by-day study blocks using AI-powered time predictions.
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import uuid

from ..database.models import Assignment, StudySession, DailySchedule, UserProfile, CompletionStatus
from .pacing import TimePredictor


class ScheduleGenerator:
    """Generates optimized study schedules for neurodivergent students."""
    
    def __init__(self, user_profile: UserProfile):
        """
        Initialize scheduler with user profile.
        
        Args:
            user_profile: UserProfile with student characteristics
        """
        self.profile = user_profile
        self.predictor = TimePredictor(user_profile)
    
    def generate_schedule(
        self,
        assignments: List[Assignment],
        start_date: Optional[date] = None,
        existing_sessions: Optional[List[StudySession]] = None
    ) -> List[DailySchedule]:
        """
        Generate a complete study schedule for all assignments.
        
        Args:
            assignments: List of Assignment objects to schedule
            start_date: Date to start scheduling from (default: today)
            existing_sessions: Previously scheduled sessions to avoid conflicts
        
        Returns:
            List of DailySchedule objects, one per day
        """
        if start_date is None:
            start_date = date.today()
        
        # Filter out completed assignments
        pending_assignments = [
            a for a in assignments
            if a.status != CompletionStatus.COMPLETED
        ]
        
        if not pending_assignments:
            return []
        
        # Predict time for each assignment
        for assignment in pending_assignments:
            if assignment.predicted_time is None:
                assignment.predicted_time = self.predictor.predict_time(assignment)
        
        # Sort assignments by priority and deadline
        sorted_assignments = self._prioritize_assignments(pending_assignments, start_date)
        
        # Generate sessions for each assignment
        all_sessions = []
        for assignment in sorted_assignments:
            sessions = self._create_sessions_for_assignment(assignment, start_date)
            all_sessions.extend(sessions)
        
        # Distribute sessions across days
        daily_schedules = self._distribute_sessions_to_days(
            all_sessions,
            start_date,
            existing_sessions or []
        )
        
        return daily_schedules
    
    def _prioritize_assignments(
        self,
        assignments: List[Assignment],
        start_date: date
    ) -> List[Assignment]:
        """
        Sort assignments by urgency and priority.
        
        Formula: urgency_score = (priority * 2 + difficulty) / days_until_due
        """
        def urgency_score(assignment):
            days_until = (assignment.due_date - start_date).days
            if days_until <= 0:
                return 1000  # Overdue - highest priority
            elif days_until == 1:
                return 100   # Due tomorrow
            else:
                # Balance priority, difficulty, and deadline
                return (assignment.priority * 2 + assignment.difficulty) / days_until
        
        return sorted(assignments, key=urgency_score, reverse=True)
    
    def _create_sessions_for_assignment(
        self,
        assignment: Assignment,
        start_date: date
    ) -> List[StudySession]:
        """
        Break assignment into optimal study sessions.
        
        Args:
            assignment: Assignment to schedule
            start_date: Earliest date to schedule
        
        Returns:
            List of StudySession objects (not yet assigned to specific days)
        """
        remaining_time = assignment.predicted_time
        if assignment.time_spent > 0:
            remaining_time = max(0, remaining_time - assignment.time_spent)
        
        if remaining_time <= 0:
            return []
        
        # Get optimal session breakdown
        task_type = assignment.task_type.value if hasattr(assignment.task_type, 'value') else assignment.task_type
        session_durations = self.predictor.suggest_session_breakdown(
            task_type,
            remaining_time
        )
        
        # Create session objects
        sessions = []
        for duration in session_durations:
            session = StudySession(
                session_id=str(uuid.uuid4()),
                assignment_id=assignment.assignment_id,
                user_id=assignment.user_id,
                planned_date=start_date,  # Will be adjusted during distribution
                planned_time=self._get_preferred_time(),
                planned_duration=duration,
                status=CompletionStatus.NOT_STARTED
            )
            sessions.append(session)
        
        return sessions
    
    def _get_preferred_time(self) -> str:
        """Get student's preferred study time."""
        if self.profile.preferred_study_times:
            return self.profile.preferred_study_times[0]
        
        # Default based on neurodivergent type
        if "ADHD" in self.profile.nd_type:
            return "evening"
        elif "Autism" in self.profile.nd_type:
            return "morning"
        else:
            return "afternoon"
    
    def _distribute_sessions_to_days(
        self,
        sessions: List[StudySession],
        start_date: date,
        existing_sessions: List[StudySession]
    ) -> List[DailySchedule]:
        """
        Distribute sessions across days, respecting daily limits.
        
        Uses a greedy algorithm: fill each day up to max_daily_hours,
        prioritizing urgent assignments.
        """
        max_daily_minutes = int(self.profile.max_daily_hours * 60)
        
        # Build mapping of existing load per day
        existing_load = {}
        for session in existing_sessions:
            day = session.planned_date
            existing_load[day] = existing_load.get(day, 0) + session.planned_duration
        
        # Distribute sessions
        daily_schedules = {}
        current_date = start_date
        session_idx = 0
        
        while session_idx < len(sessions):
            session = sessions[session_idx]
            
            # Get assignment for this session to check deadline
            # (In real implementation, would look up from database)
            assignment_due_date = None  # Would be fetched
            
            # Calculate available time for this day
            used_time = existing_load.get(current_date, 0)
            daily_load = daily_schedules.get(current_date, {}).get('total_minutes', 0)
            available_time = max_daily_minutes - used_time - daily_load
            
            # Can we fit this session today?
            if session.planned_duration <= available_time:
                # Yes - schedule it
                session.planned_date = current_date
                
                if current_date not in daily_schedules:
                    daily_schedules[current_date] = {
                        'sessions': [],
                        'total_minutes': 0
                    }
                
                daily_schedules[current_date]['sessions'].append(session)
                daily_schedules[current_date]['total_minutes'] += session.planned_duration
                
                session_idx += 1
            else:
                # No - move to next day
                current_date += timedelta(days=1)
                
                # Safety check: don't schedule too far in future
                if (current_date - start_date).days > 90:
                    break
        
        # Convert to DailySchedule objects
        result = []
        for day in sorted(daily_schedules.keys()):
            schedule = DailySchedule(
                date=day,
                user_id=self.profile.user_id,
                sessions=daily_schedules[day]['sessions'],
                total_planned_minutes=daily_schedules[day]['total_minutes']
            )
            result.append(schedule)
        
        return result
    
    def reschedule_session(
        self,
        session: StudySession,
        new_date: date,
        daily_schedules: List[DailySchedule]
    ) -> bool:
        """
        Move a session to a different date.
        
        Args:
            session: Session to move
            new_date: Target date
            daily_schedules: Current schedule
        
        Returns:
            bool: True if successful, False if can't fit
        """
        # Check if new date has capacity
        max_daily_minutes = int(self.profile.max_daily_hours * 60)
        
        new_day_schedule = next((s for s in daily_schedules if s.date == new_date), None)
        if new_day_schedule:
            if new_day_schedule.total_planned_minutes + session.planned_duration > max_daily_minutes:
                return False  # No capacity
        
        # Remove from old date
        old_date = session.planned_date
        old_day_schedule = next((s for s in daily_schedules if s.date == old_date), None)
        if old_day_schedule:
            old_day_schedule.sessions.remove(session)
            old_day_schedule.total_planned_minutes -= session.planned_duration
        
        # Add to new date
        session.planned_date = new_date
        if new_day_schedule:
            new_day_schedule.sessions.append(session)
            new_day_schedule.total_planned_minutes += session.planned_duration
        else:
            # Create new day schedule
            new_schedule = DailySchedule(
                date=new_date,
                user_id=self.profile.user_id,
                sessions=[session],
                total_planned_minutes=session.planned_duration
            )
            daily_schedules.append(new_schedule)
        
        return True


def generate_schedule(
    user_profile: UserProfile,
    assignments: List[Assignment],
    preferences: Optional[Dict] = None
) -> List[DailySchedule]:
    """
    Main entry point for schedule generation.
    
    Args:
        user_profile: User's neurodivergent profile
        assignments: List of assignments to schedule
        preferences: Additional scheduling preferences (optional)
    
    Returns:
        List of DailySchedule objects
    """
    generator = ScheduleGenerator(user_profile)
    return generator.generate_schedule(assignments)


def get_placeholder_schedule():
    """Return empty placeholder schedule for UI (deprecated)."""
    return []
