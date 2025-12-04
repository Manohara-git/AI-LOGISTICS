"""
Flask API Backend for AI Logistics System
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from utils.graph_builder import GraphBuilder
from models.route_optimizer import RouteOptimizer
from models.traffic_predictor import TrafficPredictor
from models.delivery_estimator import DeliveryEstimator
import json

# Initialize Flask app
app = Flask(__name__, static_folder='.')
CORS(app, origins=config.CORS_ORIGINS)

# Initialize components
locations_file = os.path.join(config.DATA_DIR, 'locations.json')
traffic_file = os.path.join(config.DATA_DIR, 'historical_traffic.json')

graph_builder = GraphBuilder(locations_file, traffic_file)
traffic_predictor = TrafficPredictor()
delivery_estimator = DeliveryEstimator()

# Load trained models
traffic_model_path = os.path.join(config.MODELS_DIR, config.TRAFFIC_MODEL)
delivery_model_path = os.path.join(config.MODELS_DIR, config.DELIVERY_MODEL)

if os.path.exists(traffic_model_path):
    traffic_predictor.load_model(traffic_model_path)
    print("[OK] Traffic prediction model loaded")
else:
    print("[WARNING] Traffic model not found. Run 'python ml/train_models.py' first")

if os.path.exists(delivery_model_path):
    delivery_estimator.load_model(delivery_model_path)
    print("[OK] Delivery estimation model loaded")
else:
    print("[WARNING] Delivery model not found. Run 'python ml/train_models.py' first")

# In-memory storage for deliveries (in production, use a database)
deliveries = []
delivery_counter = 1

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('.', path)

@app.route('/api/locations', methods=['GET'])
def get_locations():
    """Get all available locations"""
    locations = []
    for name, info in graph_builder.locations.items():
        locations.append({
            'name': name,
            'lat': info['lat'],
            'lng': info['lng'],
            'type': info['type'],
            'area_type': info['area_type']
        })
    return jsonify({'locations': locations})

@app.route('/api/optimize-route', methods=['POST'])
def optimize_route():
    """
    Optimize route for single or multiple stops
    
    Request body:
    {
        "start": "Warehouse",
        "end": "Gachibowli",  // Optional, for single destination
        "stops": ["Miyapur", "Kukatpally"],  // Optional, for multi-stop
        "algorithm": "genetic",  // dijkstra, a_star, genetic, nearest_neighbor
        "hour": 14,  // Optional, current hour
        "day": 2,  // Optional, day of week
        "weather": "clear"  // Optional
    }
    """
    data = request.json
    start = data.get('start', 'Warehouse')
    end = data.get('end')
    stops = data.get('stops', [])
    algorithm = data.get('algorithm', 'genetic')
    hour = data.get('hour', datetime.now().hour)
    day = data.get('day', datetime.now().weekday())
    weather = data.get('weather', 'clear')
    
    # Get dynamic graph with traffic
    dynamic_graph = graph_builder.get_dynamic_graph(hour, day, weather)
    
    # Get location coordinates for heuristics
    coords = {loc: graph_builder.get_location_coords(loc) 
              for loc in graph_builder.get_all_locations()}
    
    optimizer = RouteOptimizer(dynamic_graph, coords)
    
    try:
        if stops and len(stops) > 0:
            # Multi-stop optimization
            result = optimizer.optimize_multi_stop(start, stops, algorithm)
            route = result['route']
            distance = result['distance']
            
            # Estimate delivery time
            delivery_time = delivery_estimator.predict(
                distance_km=distance,
                num_stops=len(stops),
                hour=hour,
                day_of_week=day,
                package_size='medium',
                weather=weather
            )
        else:
            # Single destination
            if not end:
                return jsonify({'error': 'Either end or stops must be provided'}), 400
            
            if algorithm == 'a_star':
                route, distance = optimizer.a_star(start, end)
            else:
                route, distance = optimizer.dijkstra(start, end)
            
            # Estimate delivery time
            delivery_time = delivery_estimator.predict(
                distance_km=distance,
                num_stops=1,
                hour=hour,
                day_of_week=day,
                package_size='medium',
                weather=weather
            )
        
        # Get coordinates for route visualization
        route_coords = [graph_builder.get_location_coords(loc) for loc in route]
        
        return jsonify({
            'success': True,
            'route': route,
            'route_coords': route_coords,
            'distance': round(distance, 2),
            'estimated_time_minutes': round(delivery_time, 1),
            'algorithm': algorithm,
            'traffic_conditions': {
                'hour': hour,
                'day': day,
                'weather': weather
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict-traffic', methods=['POST'])
def predict_traffic():
    """
    Predict traffic for a location
    
    Request body:
    {
        "location": "Ameerpet",
        "hour": 18,
        "day": 2,
        "weather": "clear"
    }
    """
    data = request.json
    location = data.get('location')
    hour = data.get('hour', datetime.now().hour)
    day = data.get('day', datetime.now().weekday())
    weather = data.get('weather', 'clear')
    
    if not location:
        return jsonify({'error': 'Location is required'}), 400
    
    try:
        multiplier = traffic_predictor.predict(location, hour, day, weather)
        
        # Categorize traffic level
        if multiplier < 0.8:
            level = 'light'
        elif multiplier < 1.2:
            level = 'moderate'
        elif multiplier < 1.6:
            level = 'heavy'
        else:
            level = 'very_heavy'
        
        return jsonify({
            'success': True,
            'location': location,
            'traffic_multiplier': round(multiplier, 2),
            'traffic_level': level,
            'conditions': {
                'hour': hour,
                'day': day,
                'weather': weather
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/estimate-delivery', methods=['POST'])
def estimate_delivery():
    """
    Estimate delivery time
    
    Request body:
    {
        "distance_km": 15,
        "num_stops": 3,
        "hour": 14,
        "day": 2,
        "package_size": "medium",
        "weather": "clear"
    }
    """
    data = request.json
    distance = data.get('distance_km')
    num_stops = data.get('num_stops', 1)
    hour = data.get('hour', datetime.now().hour)
    day = data.get('day', datetime.now().weekday())
    package_size = data.get('package_size', 'medium')
    weather = data.get('weather', 'clear')
    
    if distance is None:
        return jsonify({'error': 'distance_km is required'}), 400
    
    try:
        time_minutes = delivery_estimator.predict(
            distance_km=distance,
            num_stops=num_stops,
            hour=hour,
            day_of_week=day,
            package_size=package_size,
            weather=weather
        )
        
        return jsonify({
            'success': True,
            'estimated_time_minutes': round(time_minutes, 1),
            'estimated_time_hours': round(time_minutes / 60, 2),
            'parameters': {
                'distance_km': distance,
                'num_stops': num_stops,
                'package_size': package_size,
                'weather': weather
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/deliveries', methods=['GET', 'POST'])
def manage_deliveries():
    """Get all deliveries or create a new one"""
    global delivery_counter
    
    if request.method == 'GET':
        return jsonify({'deliveries': deliveries})
    
    elif request.method == 'POST':
        data = request.json
        
        # Create new delivery
        delivery = {
            'id': delivery_counter,
            'start': data.get('start', 'Warehouse'),
            'stops': data.get('stops', []),
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'package_size': data.get('package_size', 'medium'),
            'weather': data.get('weather', 'clear')
        }
        
        delivery_counter += 1
        deliveries.append(delivery)
        
        return jsonify({'success': True, 'delivery': delivery}), 201

@app.route('/api/deliveries/<int:delivery_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_delivery(delivery_id):
    """Get, update, or delete a specific delivery"""
    delivery = next((d for d in deliveries if d['id'] == delivery_id), None)
    
    if not delivery:
        return jsonify({'error': 'Delivery not found'}), 404
    
    if request.method == 'GET':
        return jsonify({'delivery': delivery})
    
    elif request.method == 'PUT':
        data = request.json
        delivery.update(data)
        return jsonify({'success': True, 'delivery': delivery})
    
    elif request.method == 'DELETE':
        deliveries.remove(delivery)
        return jsonify({'success': True})

@app.route('/api/deliveries/<int:delivery_id>/submit', methods=['POST'])
def submit_delivery(delivery_id):
    """
    Submit/confirm a delivered package
    
    Request body:
    {
        "recipient_name": "John Doe",
        "delivery_notes": "Package left at front door",
        "signature": "base64_encoded_signature",  // Optional
        "photo": "base64_encoded_photo",  // Optional
        "delivered_at": "2025-12-04T19:00:00"  // Optional, defaults to now
    }
    """
    delivery = next((d for d in deliveries if d['id'] == delivery_id), None)
    
    if not delivery:
        return jsonify({'error': 'Delivery not found'}), 404
    
    data = request.json
    
    # Update delivery with submission details
    delivery['status'] = 'completed'
    delivery['recipient_name'] = data.get('recipient_name', 'Unknown')
    delivery['delivery_notes'] = data.get('delivery_notes', '')
    delivery['signature'] = data.get('signature')
    delivery['photo'] = data.get('photo')
    delivery['delivered_at'] = data.get('delivered_at', datetime.now().isoformat())
    delivery['updated_at'] = datetime.now().isoformat()
    
    return jsonify({
        'success': True,
        'message': 'Delivery submitted successfully',
        'delivery': delivery
    })

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get analytics and statistics"""
    total_deliveries = len(deliveries)
    completed = len([d for d in deliveries if d.get('status') == 'completed'])
    pending = len([d for d in deliveries if d.get('status') == 'pending'])
    in_progress = len([d for d in deliveries if d.get('status') == 'in_progress'])
    
    return jsonify({
        'total_deliveries': total_deliveries,
        'completed': completed,
        'pending': pending,
        'in_progress': in_progress,
        'completion_rate': round(completed / total_deliveries * 100, 1) if total_deliveries > 0 else 0
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("[AI LOGISTICS SYSTEM] Starting Server")
    print("="*60)
    print(f"Server running at: http://localhost:5000")
    print(f"API endpoints available at: http://localhost:5000/api/*")
    print("="*60 + "\n")
    
    app.run(debug=config.DEBUG, host='0.0.0.0', port=5000)
