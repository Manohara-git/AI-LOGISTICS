"""
Delivery time estimation ML model
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
from typing import Dict, List
import joblib
import os

class DeliveryEstimator:
    """ML model for estimating delivery times"""
    
    def __init__(self):
        """Initialize the delivery estimator"""
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        self.package_encoder = LabelEncoder()
        self.weather_encoder = LabelEncoder()
        self.is_trained = False
    
    def prepare_features(self, data: List[Dict]) -> tuple:
        """
        Prepare features for training/prediction
        
        Args:
            data: List of dictionaries with delivery data
        
        Returns:
            Tuple of (X, y) for training or X for prediction
        """
        df = pd.DataFrame(data)
        
        # Encode categorical variables
        if not self.is_trained:
            df['package_encoded'] = self.package_encoder.fit_transform(df['package_size'])
            df['weather_encoded'] = self.weather_encoder.fit_transform(df['weather'])
        else:
            df['package_encoded'] = self.package_encoder.transform(df['package_size'])
            df['weather_encoded'] = self.weather_encoder.transform(df['weather'])
        
        # Select features
        feature_columns = [
            'distance_km', 'num_stops', 'hour', 'day_of_week',
            'package_encoded', 'weather_encoded', 'is_weekend', 'is_rush_hour'
        ]
        
        X = df[feature_columns].values
        
        if 'delivery_time_minutes' in df.columns:
            y = df['delivery_time_minutes'].values
            return X, y
        
        return X, None
    
    def train(self, training_data: List[Dict]) -> Dict:
        """
        Train the delivery estimation model
        
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
        
        # Calculate mean absolute error
        predictions = self.model.predict(X)
        mae = np.mean(np.abs(predictions - y))
        
        return {
            'train_score': train_score,
            'mean_absolute_error': mae,
            'num_samples': len(training_data),
            'model_type': 'GradientBoostingRegressor'
        }
    
    def predict(self, distance_km: float, num_stops: int, hour: int,
                day_of_week: int, package_size: str = 'medium',
                weather: str = 'clear') -> float:
        """
        Predict delivery time in minutes
        
        Args:
            distance_km: Total distance in kilometers
            num_stops: Number of delivery stops
            hour: Hour of day (0-23)
            day_of_week: Day of week (0=Monday, 6=Sunday)
            package_size: Size of package ('small', 'medium', 'large')
            weather: Weather condition
        
        Returns:
            Predicted delivery time in minutes
        """
        if not self.is_trained:
            # Fallback calculation
            base_time = (distance_km / 30) * 60  # 30 km/h average
            stop_time = num_stops * 5  # 5 minutes per stop
            return base_time + stop_time
        
        # Prepare input
        is_weekend = 1 if day_of_week >= 5 else 0
        is_rush_hour = 1 if hour in [7, 8, 9, 17, 18, 19] else 0
        
        input_data = [{
            'distance_km': distance_km,
            'num_stops': num_stops,
            'hour': hour,
            'day_of_week': day_of_week,
            'package_size': package_size,
            'weather': weather,
            'is_weekend': is_weekend,
            'is_rush_hour': is_rush_hour
        }]
        
        X, _ = self.prepare_features(input_data)
        prediction = self.model.predict(X)[0]
        
        return max(5, prediction)  # Minimum 5 minutes
    
    def save_model(self, filepath: str):
        """Save trained model to disk"""
        model_data = {
            'model': self.model,
            'package_encoder': self.package_encoder,
            'weather_encoder': self.weather_encoder,
            'is_trained': self.is_trained
        }
        joblib.dump(model_data, filepath)
    
    def load_model(self, filepath: str):
        """Load trained model from disk"""
        if os.path.exists(filepath):
            model_data = joblib.load(filepath)
            self.model = model_data['model']
            self.package_encoder = model_data['package_encoder']
            self.weather_encoder = model_data['weather_encoder']
            self.is_trained = model_data['is_trained']
            return True
        return False
