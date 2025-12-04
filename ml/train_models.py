"""
Train ML models for traffic prediction and delivery estimation
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.data_generator import DataGenerator
from models.traffic_predictor import TrafficPredictor
from models.delivery_estimator import DeliveryEstimator
from config import config

def main():
    """Train and save ML models"""
    print("=" * 60)
    print("AI Logistics System - ML Model Training")
    print("=" * 60)
    
    # Paths
    locations_file = os.path.join(config.DATA_DIR, 'locations.json')
    traffic_file = os.path.join(config.DATA_DIR, 'historical_traffic.json')
    
    # Create models directory if it doesn't exist
    os.makedirs(config.MODELS_DIR, exist_ok=True)
    
    # Initialize data generator
    print("\n[1/5] Initializing data generator...")
    generator = DataGenerator(locations_file, traffic_file)
    
    # Generate traffic training data
    print("[2/5] Generating traffic training data (2000 samples)...")
    traffic_samples = generator.generate_traffic_samples(num_samples=2000)
    print(f"  [OK] Generated {len(traffic_samples)} traffic samples")
    
    # Train traffic predictor
    print("[3/5] Training traffic prediction model...")
    traffic_predictor = TrafficPredictor()
    traffic_metrics = traffic_predictor.train(traffic_samples)
    print(f"  [OK] Model trained - R2 Score: {traffic_metrics['train_score']:.4f}")
    
    # Save traffic model
    traffic_model_path = os.path.join(config.MODELS_DIR, config.TRAFFIC_MODEL)
    traffic_predictor.save_model(traffic_model_path)
    print(f"  [OK] Model saved to: {traffic_model_path}")
    
    # Generate delivery training data
    print("[4/5] Generating delivery training data (2000 samples)...")
    delivery_samples = generator.generate_delivery_samples(num_samples=2000)
    print(f"  [OK] Generated {len(delivery_samples)} delivery samples")
    
    # Train delivery estimator
    print("[5/5] Training delivery estimation model...")
    delivery_estimator = DeliveryEstimator()
    delivery_metrics = delivery_estimator.train(delivery_samples)
    print(f"  [OK] Model trained - R2 Score: {delivery_metrics['train_score']:.4f}")
    print(f"  [OK] Mean Absolute Error: {delivery_metrics['mean_absolute_error']:.2f} minutes")
    
    # Save delivery model
    delivery_model_path = os.path.join(config.MODELS_DIR, config.DELIVERY_MODEL)
    delivery_estimator.save_model(delivery_model_path)
    print(f"  [OK] Model saved to: {delivery_model_path}")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] Model training completed successfully!")
    print("=" * 60)
    
    # Test predictions
    print("\n[SAMPLE PREDICTIONS]")
    print("-" * 60)
    
    # Test traffic prediction
    traffic_pred = traffic_predictor.predict(
        location='Ameerpet',
        hour=18,
        day_of_week=2,
        weather='clear'
    )
    print(f"Traffic at Ameerpet (Wed 6PM, clear): {traffic_pred:.2f}x multiplier")
    
    # Test delivery estimation
    delivery_pred = delivery_estimator.predict(
        distance_km=15,
        num_stops=3,
        hour=18,
        day_of_week=2,
        package_size='medium',
        weather='clear'
    )
    print(f"Delivery time (15km, 3 stops, Wed 6PM): {delivery_pred:.1f} minutes")
    print("-" * 60)

if __name__ == '__main__':
    main()
