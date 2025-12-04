"""
Graph builder utility for creating and managing road network graphs
"""
import json
import math
from typing import Dict, List, Tuple
import os

class GraphBuilder:
    """Build and manage graph structures for route optimization"""
    
    def __init__(self, locations_file: str, traffic_file: str):
        """Initialize graph builder with location and traffic data"""
        self.locations = self._load_json(locations_file)
        self.traffic_data = self._load_json(traffic_file)
        self.graph = {}
        self._build_graph()
    
    def _load_json(self, filepath: str) -> dict:
        """Load JSON file"""
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def _calculate_distance(self, loc1: str, loc2: str) -> float:
        """Calculate Haversine distance between two locations in km"""
        lat1, lng1 = self.locations[loc1]['lat'], self.locations[loc1]['lng']
        lat2, lng2 = self.locations[loc2]['lat'], self.locations[loc2]['lng']
        
        # Haversine formula
        R = 6371  # Earth's radius in km
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _build_graph(self):
        """Build complete graph with all locations connected"""
        locations = list(self.locations.keys())
        
        for loc1 in locations:
            self.graph[loc1] = {}
            for loc2 in locations:
                if loc1 != loc2:
                    distance = self._calculate_distance(loc1, loc2)
                    self.graph[loc1][loc2] = distance
    
    def get_graph(self) -> Dict[str, Dict[str, float]]:
        """Get the complete graph"""
        return self.graph
    
    def get_traffic_multiplier(self, location: str, hour: int, day: int = 0, weather: str = 'clear') -> float:
        """Get traffic multiplier for a location at specific time"""
        base_traffic = self.traffic_data['area_base_traffic'].get(location, 1.0)
        multiplier = 1.0
        
        # Check time-based patterns
        patterns = self.traffic_data['traffic_patterns']
        
        # Morning rush
        if hour in patterns['weekday_morning_rush']['hours']:
            if location in patterns['weekday_morning_rush']['affected_areas']:
                multiplier *= patterns['weekday_morning_rush']['multiplier']
        
        # Evening rush
        if hour in patterns['weekday_evening_rush']['hours']:
            if location in patterns['weekday_evening_rush']['affected_areas']:
                multiplier *= patterns['weekday_evening_rush']['multiplier']
        
        # Night minimal
        if hour in patterns['night_minimal']['hours']:
            multiplier *= patterns['night_minimal']['multiplier']
        
        # Weekend
        if day in patterns['weekend_light']['days']:
            multiplier *= patterns['weekend_light']['multiplier']
        
        # Weather impact
        weather_multiplier = self.traffic_data['weather_impact'].get(weather, 1.0)
        
        return base_traffic * multiplier * weather_multiplier
    
    def get_dynamic_graph(self, hour: int = 12, day: int = 0, weather: str = 'clear') -> Dict[str, Dict[str, float]]:
        """Get graph with traffic-adjusted weights"""
        dynamic_graph = {}
        
        for loc1 in self.graph:
            dynamic_graph[loc1] = {}
            traffic_mult = self.get_traffic_multiplier(loc1, hour, day, weather)
            
            for loc2, distance in self.graph[loc1].items():
                # Adjust distance based on traffic (time = distance / speed, speed decreases with traffic)
                adjusted_distance = distance * traffic_mult
                dynamic_graph[loc1][loc2] = adjusted_distance
        
        return dynamic_graph
    
    def get_location_coords(self, location: str) -> Tuple[float, float]:
        """Get coordinates for a location"""
        loc_data = self.locations.get(location, {})
        return (loc_data.get('lat', 0), loc_data.get('lng', 0))
    
    def get_all_locations(self) -> List[str]:
        """Get list of all location names"""
        return list(self.locations.keys())
    
    def get_location_info(self, location: str) -> dict:
        """Get full information for a location"""
        return self.locations.get(location, {})
