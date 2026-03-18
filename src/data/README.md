# Neurodivergent Study Pattern Data

## Overview

This directory contains synthetic training data generated for modeling study time requirements for neurodivergent students. The data is based on educational research about how different neurodivergent profiles affect task completion times.

## Generated Files

### 1. `neurodivergent_study_patterns.csv` / `.json`
**2,000 study session records** (100 students × 20 sessions each)

**Fields:**
- `student_id`: Anonymous student identifier
- `nd_profile`: Neurodivergent type (ADHD, Autism, Dyslexia, Dyscalculia, combinations)
- `executive_function_score`: 1-5 rating of executive function challenges
- `working_memory`: low/medium/high
- `subject`: Course subject (Math, English, Science, etc.)
- `task_type`: reading, writing, problem_sets, projects, review
- `neurotypical_base_minutes`: Instructor's estimated time for neurotypical students
- `difficulty`: Task difficulty 1-5
- `interest_level`: Student's interest in topic 1-5
- `days_until_due`: Days until assignment deadline
- `time_of_day`: early_morning, late_morning, afternoon, evening, night
- `planned_duration_minutes`: How long student planned to study
- `actual_duration_minutes`: How long it actually took
- `completion_percentage`: % of task completed in session
- `breaks_taken`: Number of breaks during session
- `energy_level`: Self-reported energy 1-5
- `stress_level`: Self-reported stress 1-5
- `focus_quality`: Self-reported focus quality 1-5
- **`time_multiplier`**: Actual time / neurotypical baseline (KEY TARGET VARIABLE)

## Key Findings from Data

### Time Multipliers by Profile
- **ADHD**: 5.04x average (interest-dependent, 2x-8x range)
- **Autism**: 3.95x average (structured tasks better)
- **Dyslexia**: 5.05x average (reading 8x, problem-solving normal)
- **Dyscalculia**: 4.94x average (math 7.4x, reading normal)
- **Combined profiles**: Generally higher multipliers

### Major Factors Affecting Time
1. **Interest Level** (22% importance): High interest can reduce time by 50%+
2. **Days Until Due** (22% importance): Last-minute or too-far-future both slow down
3. **Stress Level** (19% importance): High stress = 1.5-2.5x longer
4. **Task Type**: Varies greatly by profile (see profile-specific patterns)

### Profile-Specific Patterns

**ADHD:**
- Projects take 6x longer (planning/organization challenges)
- High-interest tasks: can be *faster* than neurotypical
- Last-minute work: 2-3x penalty
- Evening/night work: often better focus

**Autism:**
- Structured problem sets: close to neurotypical time
- Novel/ambiguous projects: 5.5x longer
- Prefer consistent schedules and environments

**Dyslexia:**
- Reading-heavy work: 8x longer
- Problem sets/math: normal or faster
- Text-to-speech and audio content: major improvement

**Dyscalculia:**
- Math problem sets: 7.4x longer
- Reading/writing: normal time
- Visual aids help significantly

## Model Performance

### Time Multiplier Prediction Model (Random Forest)
- **MAE**: 1.6x (can predict within 1.6x of actual multiplier)
- **R²**: 0.38 (captures 38% of variance on test set)
- **Use for**: Estimating how much longer than standard a task will take

### Actual Time Prediction Model (Gradient Boosting)
- **MAE**: 157 minutes (~2.6 hours)
- **R²**: 0.58 (captures 58% of variance)
- **Use for**: Direct time predictions for scheduling

## Using This Data

### For Training New Models
```python
import pandas as pd

# Load data
df = pd.read_csv('neurodivergent_study_patterns.csv')

# Split features and target
features = ['nd_profile', 'task_type', 'interest_level', 'stress_level', ...]
target = 'time_multiplier'  # or 'actual_duration_minutes'

X = df[features]
y = df[target]

# Train your model...
```

### For Analysis
```python
# Analyze specific profile
adhd_data = df[df['nd_profile'] == 'ADHD']
print(f"Mean multiplier: {adhd_data['time_multiplier'].mean()}")

# Find optimal study conditions
optimal = df.groupby(['time_of_day', 'interest_level']).agg({
    'time_multiplier': 'mean'
}).sort_values('time_multiplier')
```

### For Schedule Optimization
Use the models to:
1. **Estimate realistic completion times** based on student profile
2. **Identify optimal study windows** (time of day, interest level)
3. **Balance workload** considering stress and energy
4. **Personalize over time** by learning from actual session data

## Generating More Data

To generate additional synthetic data:

```bash
python src/utils/generate_synthetic_data.py
```

Edit parameters in the script to:
- Change number of students/sessions
- Adjust time multiplier distributions
- Add new neurodivergent profiles
- Modify contextual factors

## Real Data Collection

To replace synthetic data with real student data:

1. **Ethics**: Get IRB approval, informed consent
2. **Privacy**: Anonymize all data, secure storage
3. **Collection**: Use session tracking feature in app
4. **Format**: Match CSV structure for easy model retraining
5. **Personalization**: Store per-user data for personalized models

## Data Limitations

⚠️ **This is synthetic data** based on research averages. Real neurodivergent individuals show:
- Much wider variance than modeled
- Unique combinations of strengths/challenges
- Context-dependent performance that may differ
- Non-linear effects not captured in simple models

**Important**: Use this as a starting point, but prioritize individual user feedback and adaptation!

## Research Sources

The multiplier ranges were derived from:
- "A New Understanding of ADHD" - Brown (2013)
- "Time perception in ADHD" - Toplak et al. (2009)
- "Reading in autism spectrum disorder" - Davidson & Ellis Weismer (2014)
- "Mathematical learning disability" - Butterworth (2005)
- Disability services accommodation data (1.5x-2x standard)

## Next Steps

1. **Validate** with real user data (start collection in MVP)
2. **Personalize** models per user with their feedback
3. **A/B test** schedule recommendations
4. **Add features**: medication status, environment type, sleep quality
5. **Expand** to more neurodivergent profiles and combinations
6. **Integrate** with calendar and learning management systems

---

**For questions or contributions**, see the main project README.
