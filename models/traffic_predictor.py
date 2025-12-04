"""
Traffic prediction ML model
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from typing import Dict, List
import joblib
import os

class TrafficPredictor:
    """ML model for predicting traffic conditions"""
    
    def __init__(self):
        """Initialize the traffic predictor"""
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.location_encoder = LabelEncoder()
        self.weather_encoder = LabelEncoder()
        self.is_trained = False
    
    def prepare_features(self, data: List[Dict]) -> tuple:
        """
        Prepare features for training/prediction
        
        Args:
            data: List of dictionaries with traffic data
        
        Returns:
            Tuple of (X, y) for training or X for prediction
        """
        df = pd.DataFrame(data)
        
        # Encode categorical variables
        if not self.is_trained:
            df['location_encoded'] = self.location_encoder.fit_transform(df['location'])
            df['weather_encoded'] = self.weather_encoder.fit_transform(df['weather'])
        else:
            df['location_encoded'] = self.location_encoder.transform(df['location'])
            df['weather_encoded'] = self.weather_encoder.transform(df['weather'])
        
        # Select features
        feature_columns = [
            'location_encoded', 'hour', 'day_of_week', 'weather_encoded',
            'is_weekend', 'is_rush_hour'
        ]
        
        X = df[feature_columns].values
        
        if 'traffic_multiplier' in df.columns:
            y = df['traffic_multiplier'].values
            return X, y
        
        return X, None
    
    def train(self, training_data: List[Dict]) -> Dict:
        """
        Train the traffic prediction model
        
        Args:
            training_data: List of training samples
        
        Returns:
            Dictionary with training metrics
        """
        X, y = self.prepare_features(training_data)
        
        # Train model
        self.model.fit(X, y)
        self.is_trained = True
        
        # Calculate training score
        train_score = self.model.score(X, y)
        
        return {
            'train_score': train_score,
            'num_samples': len(training_data),
            'model_type': 'RandomForestRegressor'
        }
    
    def predict(self, location: str, hour: int, day_of_week: int, 
                weather: str = 'clear') -> float:
        """
        Predict traffic multiplier for given conditions
        
        Args:
            location: Location name
            hour: Hour of day (0-23)
            day_of_week: Day of week (0=Monday, 6=Sunday)
            weather: Weather condition
        
        Returns:
            Predicted traffic multiplier
        """
        if not self.is_trained:
            return 1.0
        
        # Prepare input
        is_weekend = 1 if day_of_week >= 5 else 0
        is_rush_hour = 1 if hour in [7, 8, 9, 17, 18, 19] else 0
        
        input_data = [{
            'location': location,
            'hour': hour,
            'day_of_week': day_of_week,
            'weather': weather,
            'is_weekend': is_weekend,
            'is_rush_hour': is_rush_hour
        }]
        
        X, _ = self.prepare_features(input_data)
        prediction = self.model.predict(X)[0]
        
        return max(0.5, min(3.0, prediction))  # Clamp between 0.5 and 3.0
    
    def save_model(self, filepath: str):
        """Save trained model to disk"""
        model_data = {
            'model': self.model,
            'location_encoder': self.location_encoder,
            'weather_encoder': self.weather_encoder,
            'is_trained': self.is_trained
        }
        joblib.dump(model_data, filepath)
    
    def load_model(self, filepath: str):
        """Load trained model from disk"""
        if os.path.exists(filepath):
            model_data = joblib.load(filepath)
            self.model = model_data['model']
            self.location_encoder = model_data['location_encoder']
            self.weather_encoder = model_data['weather_encoder']
            self.is_trained = model_data['is_trained']
            return True
        return False
