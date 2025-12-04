"""
Data generator for creating synthetic training data
"""
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict
import os

class DataGenerator:
    """Generate synthetic data for ML model training"""
    
    def __init__(self, locations_file: str, traffic_file: str):
        """Initialize with location and traffic data"""
        with open(locations_file, 'r') as f:
            self.locations = json.load(f)
        with open(traffic_file, 'r') as f:
            self.traffic_data = json.load(f)
    
    def generate_traffic_samples(self, num_samples: int = 1000) -> List[Dict]:
        """
        Generate synthetic traffic data samples
        
        Returns:
            List of dictionaries with features and target (traffic_multiplier)
        """
        samples = []
        locations = list(self.locations.keys())
        
        for _ in range(num_samples):
            location = random.choice(locations)
            hour = random.randint(0, 23)
            day = random.randint(0, 6)  # 0=Monday, 6=Sunday
            weather = random.choice(['clear', 'rain', 'heavy_rain', 'fog'])
            
            # Calculate traffic multiplier based on patterns
            base_traffic = self.traffic_data['area_base_traffic'].get(location, 1.0)
            multiplier = 1.0
            
            patterns = self.traffic_data['traffic_patterns']
            
            # Morning rush
            if hour in patterns['weekday_morning_rush']['hours'] and day < 5:
                if location in patterns['weekday_morning_rush']['affected_areas']:
                    multiplier *= patterns['weekday_morning_rush']['multiplier']
            
            # Evening rush
            if hour in patterns['weekday_evening_rush']['hours'] and day < 5:
                if location in patterns['weekday_evening_rush']['affected_areas']:
                    multiplier *= patterns['weekday_evening_rush']['multiplier']
            
            # Night minimal
            if hour in patterns['night_minimal']['hours']:
                multiplier *= patterns['night_minimal']['multiplier']
            
            # Weekend
            if day in patterns['weekend_light']['days']:
                multiplier *= patterns['weekend_light']['multiplier']
            
            # Weather
            weather_mult = self.traffic_data['weather_impact'].get(weather, 1.0)
            
            final_multiplier = base_traffic * multiplier * weather_mult
            
            # Add some noise
            final_multiplier *= random.uniform(0.9, 1.1)
            
            sample = {
                'location': location,
                'hour': hour,
                'day_of_week': day,
                'weather': weather,
                'is_weekend': 1 if day >= 5 else 0,
                'is_rush_hour': 1 if hour in [7, 8, 9, 17, 18, 19] else 0,
                'traffic_multiplier': final_multiplier
            }
            samples.append(sample)
        
        return samples
    
    def generate_delivery_samples(self, num_samples: int = 1000) -> List[Dict]:
        """
        Generate synthetic delivery time data
        
        Returns:
            List of dictionaries with features and target (delivery_time_minutes)
        """
        samples = []
        locations = list(self.locations.keys())
        
        for _ in range(num_samples):
            # Random delivery parameters
            num_stops = random.randint(1, 10)
            total_distance = random.uniform(5, 50)  # km
            hour = random.randint(6, 22)
            day = random.randint(0, 6)
            package_size = random.choice(['small', 'medium', 'large'])
            weather = random.choice(['clear', 'rain', 'heavy_rain', 'fog'])
            
            # Calculate base delivery time (distance / average_speed)
            base_speed = 30  # km/h base speed
            
            # Adjust for traffic
            traffic_mult = 1.0
            if hour in [7, 8, 9, 17, 18, 19] and day < 5:
                traffic_mult = random.uniform(1.5, 2.0)
            elif hour in [22, 23, 0, 1, 2, 3, 4, 5]:
                traffic_mult = random.uniform(0.5, 0.7)
            
            # Adjust for weather
            weather_impact = {'clear': 1.0, 'rain': 1.3, 'heavy_rain': 1.7, 'fog': 1.2}
            weather_mult = weather_impact.get(weather, 1.0)
            
            # Adjust for package size (loading/unloading time)
            size_time = {'small': 2, 'medium': 5, 'large': 10}  # minutes per stop
            
            # Calculate delivery time
            travel_time = (total_distance / base_speed) * 60 * traffic_mult * weather_mult  # minutes
            stop_time = num_stops * size_time[package_size]
            total_time = travel_time + stop_time
            
            # Add some noise
            total_time *= random.uniform(0.9, 1.1)
            
            sample = {
                'distance_km': total_distance,
                'num_stops': num_stops,
                'hour': hour,
                'day_of_week': day,
                'package_size': package_size,
                'weather': weather,
                'is_weekend': 1 if day >= 5 else 0,
                'is_rush_hour': 1 if hour in [7, 8, 9, 17, 18, 19] else 0,
                'delivery_time_minutes': total_time
            }
            samples.append(sample)
        
        return samples
    
    def save_samples(self, samples: List[Dict], filename: str):
        """Save samples to JSON file"""
        with open(filename, 'w') as f:
            json.dump(samples, f, indent=2)
