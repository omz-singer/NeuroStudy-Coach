"""
Neural Network Model for Predicting Study Time for Neurodivergent Students
Uses PyTorch to build a deep learning model that learns complex patterns.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
import matplotlib.pyplot as plt
import json


class StudyTimeDataset(Dataset):
    """PyTorch Dataset for study time prediction."""
    
    def __init__(self, features, targets):
        """
        Args:
            features: numpy array of input features
            targets: numpy array of target values (time multipliers)
        """
        self.features = torch.FloatTensor(features)
        self.targets = torch.FloatTensor(targets)
    
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        return self.features[idx], self.targets[idx]


class StudyTimeNN(nn.Module):
    """
    Neural Network for predicting study time multipliers.
    
    Architecture:
    - Input layer: Multiple features (nd_profile, task_type, interest, etc.)
    - Hidden layers: Multiple fully connected layers with ReLU, Dropout, BatchNorm
    - Output layer: Single neuron for time multiplier prediction
    
    This architecture learns complex non-linear relationships between
    neurodivergent characteristics and task completion times.
    """
    
    def __init__(self, input_size, hidden_sizes=[128, 64, 32], dropout_rate=0.3):
        """
        Initialize the neural network.
        
        Args:
            input_size: Number of input features
            hidden_sizes: List of hidden layer sizes
            dropout_rate: Dropout probability for regularization
        """
        super(StudyTimeNN, self).__init__()
        
        layers = []
        prev_size = input_size
        
        # Build hidden layers with BatchNorm and Dropout
        for i, hidden_size in enumerate(hidden_sizes):
            # Fully connected layer
            layers.append(nn.Linear(prev_size, hidden_size))
            # Batch normalization for stable training
            layers.append(nn.BatchNorm1d(hidden_size))
            # ReLU activation for non-linearity
            layers.append(nn.ReLU())
            # Dropout for regularization
            layers.append(nn.Dropout(dropout_rate))
            prev_size = hidden_size
        
        # Output layer (single neuron for regression)
        layers.append(nn.Linear(prev_size, 1))
        # ReLU to ensure positive time multipliers
        layers.append(nn.ReLU())
        
        self.network = nn.Sequential(*layers)
        
        # Initialize weights using He initialization (good for ReLU)
        self._init_weights()
    
    def _init_weights(self):
        """Initialize network weights."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_in', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
    
    def forward(self, x):
        """Forward pass through the network."""
        return self.network(x)


class NeuralTimePredictor:
    """
    Neural network-based time predictor for neurodivergent students.
    Wraps the PyTorch model for easy use in the scheduling system.
    """
    
    def __init__(self, model_path=None):
        """
        Initialize the predictor.
        
        Args:
            model_path: Path to saved model (optional)
        """
        self.model = None
        self.encoders = {}
        self.scaler = None
        self.feature_names = []
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        if model_path and Path(model_path).exists():
            self.load_model(model_path)
    
    def prepare_data(self, df):
        """
        Prepare data for neural network training.
        
        Args:
            df: pandas DataFrame with training data
        
        Returns:
            X: Feature array
            y: Target array (time multipliers) or None if not in df
        """
        # Encode categorical features
        categorical_cols = ['nd_profile', 'working_memory', 'subject', 'task_type', 'time_of_day']
        
        df_encoded = df.copy()
        
        for col in categorical_cols:
            if col in df.columns:
                if col not in self.encoders:
                    self.encoders[col] = LabelEncoder()
                    df_encoded[f'{col}_encoded'] = self.encoders[col].fit_transform(df[col])
                else:
                    df_encoded[f'{col}_encoded'] = self.encoders[col].transform(df[col])
        
        # Select features
        self.feature_names = [
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
        
        X = df_encoded[self.feature_names].values
        
        # Target might not exist for inference
        if 'time_multiplier' in df_encoded.columns:
            y = df_encoded['time_multiplier'].values
        else:
            y = None
        
        # Standardize features for better neural network training
        if self.scaler is None:
            self.scaler = StandardScaler()
            X = self.scaler.fit_transform(X)
        else:
            X = self.scaler.transform(X)
        
        return X, y
    
    def train(self, df, epochs=100, batch_size=32, learning_rate=0.001, 
              hidden_sizes=[128, 64, 32], validation_split=0.2):
        """
        Train the neural network.
        
        Args:
            df: pandas DataFrame with training data
            epochs: Number of training epochs
            batch_size: Batch size for training
            learning_rate: Learning rate for optimizer
            hidden_sizes: List of hidden layer sizes
            validation_split: Fraction of data for validation
        
        Returns:
            Dict with training history
        """
        print("\n" + "="*70)
        print("TRAINING NEURAL NETWORK FOR TIME PREDICTION")
        print("="*70)
        
        # Prepare data
        print("\nPreparing data...")
        X, y = self.prepare_data(df)
        
        # Split into train and validation
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42
        )
        
        print(f"Training samples: {len(X_train)}")
        print(f"Validation samples: {len(X_val)}")
        
        # Create datasets and dataloaders
        train_dataset = StudyTimeDataset(X_train, y_train)
        val_dataset = StudyTimeDataset(X_val, y_val)
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        
        # Initialize model
        input_size = X.shape[1]
        self.model = StudyTimeNN(input_size, hidden_sizes=hidden_sizes).to(self.device)
        
        print(f"\nModel Architecture:")
        print(f"  Input size: {input_size} features")
        print(f"  Hidden layers: {hidden_sizes}")
        print(f"  Output: 1 (time multiplier)")
        print(f"  Total parameters: {sum(p.numel() for p in self.model.parameters()):,}")
        
        # Loss function and optimizer
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', 
                                                           factor=0.5, patience=10)
        
        # Training history
        history = {
            'train_loss': [],
            'val_loss': [],
            'train_mae': [],
            'val_mae': []
        }
        
        print(f"\nTraining for {epochs} epochs...")
        print("-" * 70)
        
        best_val_loss = float('inf')
        patience_counter = 0
        early_stopping_patience = 20
        
        for epoch in range(epochs):
            # Training phase
            self.model.train()
            train_losses = []
            train_maes = []
            
            for batch_features, batch_targets in train_loader:
                batch_features = batch_features.to(self.device)
                batch_targets = batch_targets.to(self.device)
                
                # Forward pass
                optimizer.zero_grad()
                predictions = self.model(batch_features).squeeze()
                loss = criterion(predictions, batch_targets)
                
                # Backward pass
                loss.backward()
                optimizer.step()
                
                # Track metrics
                train_losses.append(loss.item())
                mae = torch.abs(predictions - batch_targets).mean().item()
                train_maes.append(mae)
            
            # Validation phase
            self.model.eval()
            val_losses = []
            val_maes = []
            
            with torch.no_grad():
                for batch_features, batch_targets in val_loader:
                    batch_features = batch_features.to(self.device)
                    batch_targets = batch_targets.to(self.device)
                    
                    predictions = self.model(batch_features).squeeze()
                    loss = criterion(predictions, batch_targets)
                    
                    val_losses.append(loss.item())
                    mae = torch.abs(predictions - batch_targets).mean().item()
                    val_maes.append(mae)
            
            # Calculate epoch metrics
            train_loss = np.mean(train_losses)
            val_loss = np.mean(val_losses)
            train_mae = np.mean(train_maes)
            val_mae = np.mean(val_maes)
            
            history['train_loss'].append(train_loss)
            history['val_loss'].append(val_loss)
            history['train_mae'].append(train_mae)
            history['val_mae'].append(val_mae)
            
            # Learning rate scheduling
            scheduler.step(val_loss)
            
            # Print progress
            if (epoch + 1) % 10 == 0 or epoch == 0:
                print(f"Epoch {epoch+1:3d}/{epochs} | "
                      f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | "
                      f"Train MAE: {train_mae:.3f}x | Val MAE: {val_mae:.3f}x")
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # Save best model
                self.save_model('best_model.pth')
            else:
                patience_counter += 1
                if patience_counter >= early_stopping_patience:
                    print(f"\nEarly stopping at epoch {epoch+1}")
                    break
        
        print("-" * 70)
        print(f"\nTraining Complete!")
        print(f"Best Validation Loss: {best_val_loss:.4f}")
        print(f"Final Validation MAE: {history['val_mae'][-1]:.3f}x")
        
        # Load best model
        self.load_model('best_model.pth')
        
        return history
    
    def predict(self, features):
        """
        Predict time multiplier for new data.
        
        Args:
            features: Dict or DataFrame with feature values
        
        Returns:
            float: Predicted time multiplier
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        # Convert dict to DataFrame if needed
        if isinstance(features, dict):
            features = pd.DataFrame([features])
        
        # Prepare features
        X, _ = self.prepare_data(features)
        
        # Predict
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X).to(self.device)
            prediction = self.model(X_tensor).squeeze().cpu().numpy()
        
        return float(prediction)
    
    def save_model(self, path):
        """Save model and preprocessing objects."""
        save_dict = {
            'model_state_dict': self.model.state_dict(),
            'encoders': self.encoders,
            'scaler': self.scaler,
            'feature_names': self.feature_names
        }
        torch.save(save_dict, path)
    
    def load_model(self, path):
        """Load model and preprocessing objects."""
        checkpoint =torch.load(path, map_location=self.device, weights_only=False)
        
        self.encoders = checkpoint['encoders']
        self.scaler = checkpoint['scaler']
        self.feature_names = checkpoint['feature_names']
        
        input_size = len(self.feature_names)
        self.model = StudyTimeNN(input_size).to(self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
    
    def plot_training_history(self, history, save_path=None):
        """Plot training history."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Loss plot
        ax1.plot(history['train_loss'], label='Train Loss', linewidth=2)
        ax1.plot(history['val_loss'], label='Validation Loss', linewidth=2)
        ax1.set_xlabel('Epoch', fontsize=12)
        ax1.set_ylabel('MSE Loss', fontsize=12)
        ax1.set_title('Training and Validation Loss', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # MAE plot
        ax2.plot(history['train_mae'], label='Train MAE', linewidth=2)
        ax2.plot(history['val_mae'], label='Validation MAE', linewidth=2)
        ax2.set_xlabel('Epoch', fontsize=12)
        ax2.set_ylabel('MAE (multiplier)', fontsize=12)
        ax2.set_title('Mean Absolute Error', fontsize=14, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"\nTraining plot saved to: {save_path}")
        
        plt.show()


if __name__ == "__main__":
    # Load data
    data_path = Path(__file__).parent.parent / "data" / "neurodivergent_study_patterns.csv"
    
    print("Loading data...")
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} records\n")
    
    # Initialize predictor
    predictor = NeuralTimePredictor()
    
    # Train the model
    history = predictor.train(
        df,
        epochs=100,
        batch_size=32,
        learning_rate=0.001,
        hidden_sizes=[128, 64, 32],
        validation_split=0.2
    )
    
    # Plot training history
    predictor.plot_training_history(history, 'training_history.png')
    
    # Test prediction
    print("\n" + "="*70)
    print("TESTING PREDICTIONS")
    print("="*70)
    
    test_case = {
        'nd_profile': 'ADHD',
        'executive_function_score': 4,
        'working_memory': 'low',
        'subject': 'Mathematics',
        'task_type': 'reading',
        'neurotypical_base_minutes': 60,
        'difficulty': 3,
        'interest_level': 2,
        'days_until_due': 3,
        'time_of_day': 'evening',
        'stress_level': 4,
        'energy_level': 3
    }
    
    prediction = predictor.predict(test_case)
    predicted_time = int(test_case['neurotypical_base_minutes'] * prediction)
    
    print(f"\nTest Case:")
    print(f"  Profile: {test_case['nd_profile']}")
    print(f"  Task: {test_case['task_type']} ({test_case['neurotypical_base_minutes']} min neurotypical)")
    print(f"  Interest: {test_case['interest_level']}/5")
    print(f"  Stress: {test_case['stress_level']}/5")
    print(f"\nNeural Network Prediction:")
    print(f"  Time multiplier: {prediction:.2f}x")
    print(f"  Predicted time: {predicted_time} minutes")
    
    print("\n" + "="*70)
    print("✅ Neural network training complete!")
    print("="*70)
