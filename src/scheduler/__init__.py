"""
src/scheduler/__init__.py

Adaptive study session scheduler integrating the team's TimePredictor
from pacing.py for neurodivergent-aware time estimation.

Falls back to cognitive-science baseline if no profile is set.
"""

import math
from datetime import date, timedelta
from typing import Optional

# Import team's pacing module
try:
    from src.scheduler.pacing import TimePredictor, BASELINE_MULTIPLIERS
    PACING_AVAILABLE = True
except ImportError:
    PACING_AVAILABLE = False

MAX_SESSIONS_PER_DAY = 4
MIN_SESSION_MINS = 20
DEFAULT_MAX_SESSION_MINS = 60

# Map our assignment types to team's task types
TYPE_MAP = {
    "Essay":    "writing",
    "Exam":     "review",
    "Project":  "projects",
    "Lab":      "problem_sets",
    "Reading":  "reading",
    "Other":    "review",
}

# Profile-based session length targets (from pacing.py logic)
SESSION_TARGETS = {
    "ADHD":        35,
    "Autism":      75,
    "Dyslexia":    45,
    "Dyscalculia": 45,
}


class SimpleProfile:
    """Minimal profile object compatible with TimePredictor."""
    def __init__(self, profile_dict: dict):
        self.nd_type              = profile_dict.get("nd_type", "ADHD")
        self.executive_function_score = profile_dict.get("executive_function", 3)
        self.working_memory       = profile_dict.get("working_memory", "medium")
        self.typical_stress       = profile_dict.get("typical_stress", 3)
        self.typical_energy       = profile_dict.get("typical_energy", 3)
        self.preferred_study_times = [profile_dict.get("preferred_study_times", "afternoon")]
        self.max_daily_hours      = float(profile_dict.get("max_daily_hours", 4.0))
        self.preferred_session_length = int(profile_dict.get("preferred_session_len", 50))
        self.break_frequency      = int(profile_dict.get("break_frequency", 50))


class SimpleAssignment:
    """Minimal assignment object compatible with TimePredictor."""
    def __init__(self, a: dict):
        self.task_type        = TYPE_MAP.get(a.get("type", "Other"), "review")
        self.neurotypical_time = int(float(a.get("est_hours", 2)) * 60)
        self.difficulty       = _priority_to_int(a.get("priority", "Medium"))
        self.interest_level   = int(a.get("interest_level", 3))
        self.due_date         = date.fromisoformat(a["due_date"][:10])
        self.course           = a.get("course", "General")


def _priority_to_int(priority: str) -> int:
    return {"Low": 2, "Medium": 3, "High": 4}.get(priority, 3)


def _available_days(start: date, end: date, blocked: set) -> list:
    days, current = [], start
    while current < end:
        if current.isoformat() not in blocked:
            days.append(current)
        current += timedelta(days=1)
    return days


def _backload_weights(n: int) -> list:
    if n == 1:
        return [1.0]
    raw = [math.exp(0.3 * i) for i in range(n)]
    total = sum(raw)
    return [w / total for w in raw]


def _get_session_target(nd_type: str, preferred_len: int) -> int:
    """Get target session length based on neurodivergent profile."""
    profile_target = SESSION_TARGETS.get(nd_type, DEFAULT_MAX_SESSION_MINS)
    # Use preferred if set meaningfully, else profile default
    if 15 <= preferred_len <= 90:
        return preferred_len
    return profile_target


def _adjust_hours_with_predictor(
    assignment: dict,
    profile: Optional[SimpleProfile],
) -> float:
    """
    Use TimePredictor to adjust estimated hours based on ND profile.
    Falls back to original est_hours if predictor unavailable.
    """
    if not PACING_AVAILABLE or profile is None:
        return float(assignment.get("est_hours", 2))

    try:
        predictor = TimePredictor(profile)
        simple_asn = SimpleAssignment(assignment)
        predicted_mins = predictor.predict_time(simple_asn)
        return predicted_mins / 60.0
    except Exception as e:
        print(f"TimePredictor error: {e}, using original estimate")
        return float(assignment.get("est_hours", 2))


def generate_schedule(
    assignments: list,
    blocked_days: list,
    user_profile: Optional[dict] = None,
) -> list:
    """
    Generate study sessions for all assignments.

    Args:
        assignments: list of assignment dicts from DB
        blocked_days: list of ISO date strings to skip
        user_profile: dict from DB user_profile table (optional)

    Returns:
        list of session dicts ready to insert into study_sessions table
    """
    blocked = set(blocked_days)
    today = date.today()
    sessions = []
    day_load: dict = {}

    # Build profile object if available
    profile = SimpleProfile(user_profile) if user_profile else None
    nd_type = user_profile.get("nd_type", "ADHD") if user_profile else "ADHD"
    preferred_len = user_profile.get("preferred_session_len", DEFAULT_MAX_SESSION_MINS) if user_profile else DEFAULT_MAX_SESSION_MINS
    max_session_mins = _get_session_target(nd_type, preferred_len)
    max_daily_mins = int((user_profile.get("max_daily_hours", 4.0) if user_profile else 4.0) * 60)

    # Sort by priority (high first)
    order = {"High": 0, "Medium": 1, "Low": 2}
    sorted_assignments = sorted(assignments, key=lambda a: order.get(a.get("priority", "Medium"), 1))

    for a in sorted_assignments:
        assignment_id = a["id"]
        due = date.fromisoformat(a["due_date"][:10])

        if due <= today:
            continue

        # Get ND-adjusted time estimate
        adjusted_hours = _adjust_hours_with_predictor(a, profile)
        total_mins = int(adjusted_hours * 60)

        if total_mins <= 0:
            continue

        available = _available_days(today, due, blocked)
        if not available:
            continue

        # Number of sessions needed
        min_sessions = math.ceil(total_mins / max_session_mins)
        ideal_sessions = max(min_sessions, min(len(available), max(2, len(available) * 2 // 3)))
        n_sessions = min(ideal_sessions, len(available))

        # Pick spread-out days respecting daily load
        candidate_days = []
        step = max(1, len(available) // n_sessions)
        for i in range(n_sessions):
            idx = min(i * step, len(available) - 1)
            d = available[idx]
            if day_load.get(d.isoformat(), 0) < MAX_SESSIONS_PER_DAY:
                candidate_days.append(d)

        if len(candidate_days) < n_sessions:
            used = set(d.isoformat() for d in candidate_days)
            for d in available:
                if d.isoformat() not in used and day_load.get(d.isoformat(), 0) < MAX_SESSIONS_PER_DAY:
                    candidate_days.append(d)
                if len(candidate_days) >= n_sessions:
                    break

        candidate_days = sorted(candidate_days)[:n_sessions]
        if not candidate_days:
            continue

        # Distribute minutes with backloading curve
        weights = _backload_weights(len(candidate_days))
        raw_mins = [w * total_mins for w in weights]
        clamped = [max(MIN_SESSION_MINS, min(max_session_mins, round(m))) for m in raw_mins]
        diff = total_mins - sum(clamped[:-1])
        clamped[-1] = max(MIN_SESSION_MINS, min(max_session_mins, diff))

        for i, (d, mins) in enumerate(zip(candidate_days, clamped)):
            sessions.append({
                "assignment_id": assignment_id,
                "session_date":  d.isoformat(),
                "duration_mins": mins,
                "session_number": i + 1,
                "total_sessions": len(candidate_days),
            })
            day_load[d.isoformat()] = day_load.get(d.isoformat(), 0) + 1

    return sessions
