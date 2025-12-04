"""
Configuration settings for AI Logistics System
"""
import os

class Config:
    """Base configuration"""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = True
    
    # API settings
    API_VERSION = 'v1'
    API_PREFIX = '/api'
    
    # CORS settings
    CORS_ORIGINS = ['http://localhost:5000', 'http://127.0.0.1:5000']
    
    # ML Model paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MODELS_DIR = os.path.join(BASE_DIR, 'ml', 'trained_models')
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    
    # Model filenames
    TRAFFIC_MODEL = 'traffic_predictor.pkl'
    DELIVERY_MODEL = 'delivery_estimator.pkl'
    
    # Optimization settings
    GENETIC_ALGORITHM_GENERATIONS = 100
    GENETIC_ALGORITHM_POPULATION = 50
    ANT_COLONY_ITERATIONS = 100
    
    # Map settings
    DEFAULT_CENTER = [17.385044, 78.486671]  # Hyderabad coordinates
    DEFAULT_ZOOM = 12

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')

# Default config
config = DevelopmentConfig()
