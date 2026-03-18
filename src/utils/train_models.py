"""
Simple ML Model for Predicting Study Time for Neurodivergent Students
Uses the synthetic training data to build a time estimation model.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import json

# File paths
DATA_DIR = Path(__file__).parent.parent / "data"
CSV_PATH = DATA_DIR / "neurodivergent_study_patterns.csv"
MODEL_SAVE_PATH = DATA_DIR / "time_multiplier_model.json"


def load_and_prepare_data():
    """Load CSV data and prepare for training."""
    print(f"Loading data from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    
    print(f"Loaded {len(df)} records")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nSample data:")
    print(df.head())
    
    return df


def encode_categorical_features(df):
    """Encode categorical variables."""
    encoders = {}
    categorical_cols = ['nd_profile', 'working_memory', 'subject', 'task_type', 'time_of_day']
    
    df_encoded = df.copy()
    
    for col in categorical_cols:
        if col in df.columns:
            le = LabelEncoder()
            df_encoded[f'{col}_encoded'] = le.fit_transform(df[col])
            encoders[col] = le
    
    return df_encoded, encoders


def train_time_multiplier_model(df):
    """Train model to predict time multiplier."""
    print("\n" + "="*60)
    print("Training Time Multiplier Prediction Model")
    print("="*60)
    
    # Encode categorical features
    df_encoded, encoders = encode_categorical_features(df)
    
    # Select features for training
    feature_cols = [
        'nd_profile_encoded',
        'executive_function_score',
        'working_memory_encoded',
        'task_type_encoded',
        'neurotypical_base_minutes',
        'difficulty',
        'interest_level',
        'days_until_due',
        'time_of_day_encoded',
        'stress_level',
        'energy_level'
    ]
    
    X = df_encoded[feature_cols]
    y = df_encoded['time_multiplier']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"\nTraining set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    
    # Train Random Forest model
    print("\nTraining Random Forest model...")
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=15,
        min_samples_split=10,
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)
    
    # Predictions
    y_pred_train = rf_model.predict(X_train)
    y_pred_test = rf_model.predict(X_test)
    
    # Evaluate
    print("\n" + "-"*60)
    print("Model Performance:")
    print("-"*60)
    print(f"Training Set:")
    print(f"  MAE: {mean_absolute_error(y_train, y_pred_train):.3f}")
    print(f"  RMSE: {np.sqrt(mean_squared_error(y_train, y_pred_train)):.3f}")
    print(f"  R²: {r2_score(y_train, y_pred_train):.3f}")
    
    print(f"\nTest Set:")
    print(f"  MAE: {mean_absolute_error(y_test, y_pred_test):.3f}")
    print(f"  RMSE: {np.sqrt(mean_squared_error(y_test, y_pred_test)):.3f}")
    print(f"  R²: {r2_score(y_test, y_pred_test):.3f}")
    
    # Feature importance
    print("\n" + "-"*60)
    print("Feature Importance:")
    print("-"*60)
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': rf_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for _, row in feature_importance.iterrows():
        print(f"  {row['feature']:30s}: {row['importance']:.4f}")
    
    return rf_model, encoders, feature_cols


def train_actual_time_model(df):
    """Train model to directly predict actual time needed."""
    print("\n" + "="*60)
    print("Training Actual Time Prediction Model")
    print("="*60)
    
    df_encoded, encoders = encode_categorical_features(df)
    
    feature_cols = [
        'nd_profile_encoded',
        'executive_function_score',
        'working_memory_encoded',
        'task_type_encoded',
        'neurotypical_base_minutes',
        'difficulty',
        'interest_level',
        'days_until_due',
        'time_of_day_encoded',
        'stress_level',
        'energy_level'
    ]
    
    X = df_encoded[feature_cols]
    y = df_encoded['actual_duration_minutes']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"\nTraining set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    
    # Train Gradient Boosting model
    print("\nTraining Gradient Boosting model...")
    gb_model = GradientBoostingRegressor(
        n_estimators=100,
        max_depth=7,
        learning_rate=0.1,
        random_state=42
    )
    gb_model.fit(X_train, y_train)
    
    # Predictions
    y_pred_test = gb_model.predict(X_test)
    
    # Evaluate
    print("\n" + "-"*60)
    print("Model Performance (Test Set):")
    print("-"*60)
    print(f"  MAE: {mean_absolute_error(y_test, y_pred_test):.2f} minutes")
    print(f"  RMSE: {np.sqrt(mean_squared_error(y_test, y_pred_test)):.2f} minutes")
    print(f"  R²: {r2_score(y_test, y_pred_test):.3f}")
    
    # Show some example predictions
    print("\n" + "-"*60)
    print("Sample Predictions (first 10 test samples):")
    print("-"*60)
    comparison = pd.DataFrame({
        'Actual (min)': y_test.values[:10],
        'Predicted (min)': y_pred_test[:10],
        'Error (min)': y_test.values[:10] - y_pred_test[:10]
    })
    print(comparison.to_string(index=False))
    
    return gb_model, encoders, feature_cols


def analyze_patterns_by_profile(df):
    """Analyze patterns by neurodivergent profile."""
    print("\n" + "="*60)
    print("Analysis by Neurodivergent Profile")
    print("="*60)
    
    for profile in df['nd_profile'].unique():
        profile_data = df[df['nd_profile'] == profile]
        print(f"\n{profile}:")
        print(f"  Samples: {len(profile_data)}")
        print(f"  Mean multiplier: {profile_data['time_multiplier'].mean():.2f}x")
        print(f"  Median multiplier: {profile_data['time_multiplier'].median():.2f}x")
        print(f"  Std dev: {profile_data['time_multiplier'].std():.2f}")
        
        # Best and worst conditions
        best_task = profile_data.groupby('task_type')['time_multiplier'].mean().idxmin()
        worst_task = profile_data.groupby('task_type')['time_multiplier'].mean().idxmax()
        print(f"  Best task type: {best_task} ({profile_data[profile_data['task_type']==best_task]['time_multiplier'].mean():.2f}x)")
        print(f"  Worst task type: {worst_task} ({profile_data[profile_data['task_type']==worst_task]['time_multiplier'].mean():.2f}x)")


def analyze_interest_impact(df):
    """Analyze how interest level affects time multiplier."""
    print("\n" + "="*60)
    print("Impact of Interest Level on Time Multiplier")
    print("="*60)
    
    interest_analysis = df.groupby('interest_level').agg({
        'time_multiplier': ['mean', 'median', 'std', 'count']
    }).round(3)
    print(interest_analysis)
    
    print("\nKey Insight: Higher interest often reduces time multiplier,")
    print("especially for ADHD students who can hyperfocus on engaging tasks.")


if __name__ == "__main__":
    # Load data
    df = load_and_prepare_data()
    
    # Analyze patterns
    analyze_patterns_by_profile(df)
    analyze_interest_impact(df)
    
    # Train models
    multiplier_model, encoders_1, features_1 = train_time_multiplier_model(df)
    time_model, encoders_2, features_2 = train_actual_time_model(df)
    
    print("\n" + "="*60)
    print("Training Complete!")
    print("="*60)
    print("\nThese models can now be used to:")
    print("  1. Predict time multipliers for new assignments")
    print("  2. Directly predict actual time needed")
    print("  3. Adapt to individual student patterns over time")
    print("  4. Optimize study schedules based on context")
    
    print("\nNext steps:")
    print("  - Integrate models into scheduler/planner.py")
    print("  - Add personalized learning from user feedback")
    print("  - Create A/B testing framework for schedule optimization")
