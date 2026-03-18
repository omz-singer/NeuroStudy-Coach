"""
Synthetic Data Generator for Neurodivergent Study Patterns
Generates realistic training data based on educational research.
"""

import json
import random
import csv
from datetime import datetime, timedelta
from pathlib import Path

# Research-based time multipliers (mean, std_dev)
TIME_MULTIPLIERS = {
    "ADHD": {
        "reading": (1.55, 0.25),
        "writing": (2.0, 0.5),
        "problem_sets": (1.6, 0.4),
        "projects": (2.5, 0.5),
        "review": (1.7, 0.3)
    },
    "Autism": {
        "reading": (1.3, 0.3),
        "writing": (1.8, 0.4),
        "problem_sets": (1.0, 0.3),  # Can be equal or better with structure
        "projects": (2.0, 0.5),
        "review": (1.2, 0.3)
    },
    "Dyslexia": {
        "reading": (2.75, 0.75),
        "writing": (2.15, 0.4),
        "problem_sets": (1.05, 0.15),
        "projects": (1.4, 0.3),
        "review": (2.0, 0.5)
    },
    "Dyscalculia": {
        "reading": (1.1, 0.2),
        "writing": (1.2, 0.25),
        "problem_sets": (2.8, 0.6),
        "projects": (1.5, 0.3),
        "review": (2.2, 0.4)
    }
}

# Modifiers based on conditions
CONDITION_MODIFIERS = {
    "time_of_day": {
        "early_morning": (0.9, 1.3),  # (min, max) range
        "late_morning": (0.85, 1.1),  # Peak time for many
        "afternoon": (1.1, 1.4),      # Post-lunch dip
        "evening": (0.95, 1.25),
        "night": (1.0, 1.6)           # Variable, depends on chronotype
    },
    "interest_level": {
        1: (1.5, 2.0),   # Very low interest = much slower
        2: (1.2, 1.5),
        3: (1.0, 1.2),
        4: (0.85, 1.1),  # High interest = can hyperfocus
        5: (0.7, 1.0)    # Very high interest = hyperfocus advantage
    },
    "stress_level": {
        1: (0.9, 1.1),
        2: (1.0, 1.2),
        3: (1.1, 1.3),
        4: (1.3, 1.7),
        5: (1.5, 2.5)    # High stress severely impacts neurodivergent performance
    },
    "days_until_due": {
        "range": [(0, 1, 1.8, 2.5),   # Last minute panic (min_days, max_days, min_mult, max_mult)
                  (2, 3, 1.3, 1.8),   # Rushed
                  (4, 7, 1.0, 1.4),   # Moderate pressure
                  (8, 14, 1.1, 1.5),  # Comfortable but procrastination
                  (15, 999, 1.3, 2.0)] # Too far = hard to start
    }
}

SUBJECTS = ["Mathematics", "English Literature", "Chemistry", "History", 
            "Computer Science", "Biology", "Psychology", "Physics", "Art", "Economics"]

TASK_TYPES = ["reading", "writing", "problem_sets", "projects", "review"]

NEURODIVERGENT_TYPES = ["ADHD", "Autism", "Dyslexia", "Dyscalculia", 
                        "ADHD+Anxiety", "Autism+ADHD", "Dyslexia+ADHD"]


def get_base_multiplier(nd_type, task_type):
    """Get base time multiplier for neurodivergent type and task."""
    if "+" in nd_type:
        # Combined conditions: average the multipliers with slight increase
        types = nd_type.split("+")
        primary = types[0]
        multipliers = TIME_MULTIPLIERS.get(primary, TIME_MULTIPLIERS["ADHD"])
    else:
        multipliers = TIME_MULTIPLIERS.get(nd_type, TIME_MULTIPLIERS["ADHD"])
    
    mean, std = multipliers.get(task_type, (1.5, 0.3))
    return max(0.5, random.gauss(mean, std))


def apply_condition_modifiers(base_mult, time_of_day, interest, stress, days_until):
    """Apply contextual modifiers to base multiplier."""
    # Time of day
    tod_range = CONDITION_MODIFIERS["time_of_day"][time_of_day]
    tod_mult = random.uniform(*tod_range)
    
    # Interest level (high interest can counteract ADHD issues)
    interest_range = CONDITION_MODIFIERS["interest_level"][interest]
    interest_mult = random.uniform(*interest_range)
    
    # Stress level
    stress_range = CONDITION_MODIFIERS["stress_level"][stress]
    stress_mult = random.uniform(*stress_range)
    
    # Days until due
    due_mult = 1.0
    for min_d, max_d, min_m, max_m in CONDITION_MODIFIERS["days_until_due"]["range"]:
        if min_d <= days_until <= max_d:
            due_mult = random.uniform(min_m, max_m)
            break
    
    # Combine multiplicatively
    final_mult = base_mult * tod_mult * interest_mult * stress_mult * due_mult
    
    # Add some random noise
    noise = random.gauss(1.0, 0.1)
    return max(0.3, final_mult * noise)  # Minimum 0.3x (rare cases where student is faster)


def generate_student_session(student_id):
    """Generate one study session data point."""
    nd_type = random.choice(NEURODIVERGENT_TYPES)
    subject = random.choice(SUBJECTS)
    task_type = random.choice(TASK_TYPES)
    
    # Assignment characteristics
    neurotypical_time = random.randint(20, 180)  # 20 min to 3 hours
    difficulty = random.randint(1, 5)
    interest = random.randint(1, 5)
    days_until = random.choices(
        [0, 1, 2, 3, 5, 7, 10, 14, 21],
        weights=[5, 10, 15, 20, 25, 15, 5, 3, 2]
    )[0]
    
    # Session conditions
    time_of_day = random.choice(["early_morning", "late_morning", "afternoon", "evening", "night"])
    stress = random.randint(1, 5)
    energy = random.randint(1, 5)
    
    # Calculate time multiplier
    base_mult = get_base_multiplier(nd_type, task_type)
    final_mult = apply_condition_modifiers(base_mult, time_of_day, interest, stress, days_until)
    
    actual_time = int(neurotypical_time * final_mult)
    
    # Session planning
    planned_duration = random.choice([25, 30, 45, 50, 60, 90])
    completion_pct = min(100, int((planned_duration / actual_time) * 100 * random.uniform(0.85, 1.15)))
    
    # Breaks (more for longer sessions and ADHD)
    break_base = planned_duration // 30
    if "ADHD" in nd_type:
        breaks = break_base + random.randint(0, 2)
    else:
        breaks = break_base + random.randint(-1, 1)
    breaks = max(0, breaks)
    
    return {
        "student_id": f"student_{student_id:04d}",
        "nd_profile": nd_type,
        "executive_function_score": random.randint(1, 5),
        "working_memory": random.choice(["low", "medium", "high"]),
        "subject": subject,
        "task_type": task_type,
        "neurotypical_base_minutes": neurotypical_time,
        "difficulty": difficulty,
        "interest_level": interest,
        "days_until_due": days_until,
        "time_of_day": time_of_day,
        "planned_duration_minutes": planned_duration,
        "actual_duration_minutes": actual_time,
        "completion_percentage": completion_pct,
        "breaks_taken": breaks,
        "energy_level": energy,
        "stress_level": stress,
        "focus_quality": max(1, min(5, 6 - stress + (interest - 3))),
        "time_multiplier": round(final_mult, 3)
    }


def generate_dataset(n_students=100, sessions_per_student=20):
    """Generate complete synthetic dataset."""
    data = []
    for student_id in range(1, n_students + 1):
        for _ in range(sessions_per_student):
            data.append(generate_student_session(student_id))
    return data


def save_as_csv(data, filepath):
    """Save dataset as CSV."""
    if not data:
        return
    
    fieldnames = data[0].keys()
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def save_as_json(data, filepath):
    """Save dataset as JSON."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    print("Generating synthetic neurodivergent study pattern data...")
    
    # Generate data
    dataset = generate_dataset(n_students=100, sessions_per_student=20)
    
    print(f"Generated {len(dataset)} study session records")
    
    # Save in multiple formats
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    csv_path = data_dir / "neurodivergent_study_patterns.csv"
    json_path = data_dir / "neurodivergent_study_patterns.json"
    
    save_as_csv(dataset, csv_path)
    save_as_json(dataset, json_path)
    
    print(f"Saved to:\n  - {csv_path}\n  - {json_path}")
    
    # Print sample statistics
    multipliers = [d["time_multiplier"] for d in dataset]
    print(f"\nDataset Statistics:")
    print(f"  Mean time multiplier: {sum(multipliers) / len(multipliers):.2f}")
    print(f"  Min multiplier: {min(multipliers):.2f}")
    print(f"  Max multiplier: {max(multipliers):.2f}")
    
    # Profile distribution
    profiles = {}
    for d in dataset:
        profiles[d["nd_profile"]] = profiles.get(d["nd_profile"], 0) + 1
    print(f"\nProfile distribution:")
    for profile, count in sorted(profiles.items()):
        print(f"  {profile}: {count} sessions")
