# Data Collection Guide for Neurodivergent Study Patterns

## Overview
This guide outlines data needed to train models for adaptive study scheduling for neurodivergent students.

## Key Data Categories

### 1. Student Profile Characteristics
- **Neurodivergent Profile Type**: ADHD, Autism, Dyslexia, Dyscalculia, combinations
- **Age/Grade Level**: High school, undergraduate, graduate
- **Executive Function Metrics**:
  - Task initiation difficulty (1-5 scale)
  - Working memory capacity (low/medium/high)
  - Time blindness severity (1-5 scale)
  - Hyperfocus tendency (yes/no, frequency)
  - Sensory processing sensitivity (low/medium/high)

### 2. Course/Assignment Attributes
- **Subject Domain**: STEM, Humanities, Arts, Languages, Social Sciences
- **Task Type**: Reading, Problem sets, Writing, Projects, Labs, Presentations
- **Cognitive Load**:
  - Working memory required (low/medium/high)
  - Novel vs familiar material
  - Abstract vs concrete concepts
  - Sequential vs simultaneous processing needed

### 3. Time Estimation Data (Critical for Training)
- **Neurotypical baseline time** (from course syllabi/instructor estimates)
- **Actual completion time** for neurodivergent students
- **Variance factors**:
  - Time of day (morning/afternoon/evening/night)
  - Day of week (weekday vs weekend)
  - Proximity to deadline (days remaining)
  - Concurrent stressors (other deadlines, life events)
  - Medication status (if applicable and consented)
  - Environment (library, home, quiet room, etc.)

### 4. Session Performance Metrics
- **Planned session duration** vs **actual duration**
- **Breaks taken** (frequency, duration)
- **Completion percentage** per session
- **Self-reported**: 
  - Energy level (1-5)
  - Focus quality (1-5)
  - Stress/anxiety level (1-5)
  - Task engagement/interest (1-5)

### 5. Accommodation Preferences
- **Preferred session length**: Short (15-25 min), Medium (25-45 min), Long (45+ min)
- **Break structure**: Pomodoro, flexible, scheduled
- **Best study times**: Early morning, late morning, afternoon, evening, night
- **Context switching tolerance**: Low/medium/high
- **Multi-tasking vs single-task preference**

## Research-Based Time Multipliers

Based on educational research, neurodivergent students often need:

### ADHD Students
- **Reading comprehension**: 1.3-1.8x neurotypical time
- **Writing tasks**: 1.5-2.5x (especially initial drafts)
- **Problem sets**: 1.2-2.0x (varies by interest level)
- **Project planning**: 2.0-3.0x (executive function challenges)
- **Proofreading**: 1.5-2.0x

### Autistic Students
- **Novel/ambiguous tasks**: 1.5-2.5x
- **Social/collaborative work**: 1.8-2.8x
- **Pattern-based problems**: 0.8-1.2x (may be faster!)
- **Open-ended assignments**: 1.5-2.5x
- **Structured/algorithmic tasks**: 0.9-1.3x

### Dyslexic Students
- **Reading-heavy assignments**: 2.0-3.5x
- **Writing with complex grammar**: 1.8-2.5x
- **Math/logical problems**: 0.9-1.2x
- **Audio/video content**: 1.0-1.3x
- **Hands-on/practical work**: 0.9-1.1x

### Combined Profiles (ADHD + Dyslexia, etc.)
- Effects often **multiplicative** rather than additive
- Individual calibration essential

## Recommended Data Sources

### 1. Academic Research Databases
- **PubMed**: Search "ADHD academic performance time", "autism study completion time"
- **ERIC (Education Resources)**: Special education accommodations data
- **Google Scholar**: "neurodivergent students time management", "ADHD task duration"

### 2. Disability Services Data
- Contact university disability services offices (anonymized aggregated data)
- Extended time accommodation ratios (commonly 1.5x or 2.0x standardized)

### 3. Self-Reported Surveys
- r/ADHD, r/autism, r/dyslexia communities (with permission)
- Neurodivergent student organizations
- CHADD (Children and Adults with ADHD) forums

### 4. Educational Apps & Platforms
- Forest, Habitica, Notion (productivity app analytics)
- Canvas LMS data (if available from institutions)
- RescueTime user statistics

### 5. Synthetic Data Generation
- Use research-based distributions
- Monte Carlo simulation with known parameters
- Vary by conditions (time of day, stress, interest)

## Sample Data Structure for Collection

```json
{
  "student_id": "anon_001",
  "profile": {
    "neurodivergent_type": ["ADHD-combined", "anxiety"],
    "age": 20,
    "education_level": "undergraduate",
    "executive_function": {
      "task_initiation": 4,
      "working_memory": "low",
      "time_blindness": 5
    }
  },
  "assignment": {
    "course": "Organic Chemistry",
    "type": "problem_set",
    "estimated_time_neurotypical": 120,
    "difficulty": 4,
    "interest_level": 2,
    "due_in_days": 5
  },
  "session": {
    "planned_duration": 45,
    "actual_duration": 73,
    "time_of_day": "evening",
    "completion_percentage": 60,
    "breaks_count": 4,
    "self_report": {
      "energy": 3,
      "focus": 2,
      "stress": 4,
      "engagement": 2
    }
  },
  "multiplier_computed": 1.82
}
```

## Ethical Considerations

1. **Privacy**: All data must be anonymized, consent obtained
2. **Representation**: Ensure diverse neurodivergent profiles represented
3. **Avoid Stereotyping**: Individual variation is enormous
4. **Strengths-Based**: Capture when neurodivergent students are faster/better
5. **Intersectionality**: Consider race, class, gender, culture alongside neurodivergence

## Next Steps

1. Start with synthetic data based on research multipliers
2. Build MVP with adjustable parameters
3. Collect real user feedback data (with consent)
4. Continuously refine model with actual usage data
5. Implement personalized learning: each user's data improves their own model

## Useful Research Papers

- Brown, T. E. (2013). A New Understanding of ADHD in Children and Adults: Executive Function Impairments
- Sedgwick et al. (2019). "The role of executive function in academic achievement in autism spectrum disorder"
- Reid & Lienemann (2006). "Strategy Instruction for Students with Learning Disabilities"
- Toplak et al. (2009). "Time perception in ADHD: findings and clinical implications"

