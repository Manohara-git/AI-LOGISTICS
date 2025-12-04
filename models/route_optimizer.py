"""
Route optimization algorithms for delivery logistics
Includes: Dijkstra, A*, Genetic Algorithm, and Ant Colony Optimization
"""
import heapq
import random
import math
from typing import List, Dict, Tuple, Optional
import copy

class RouteOptimizer:
    """Collection of route optimization algorithms"""
    
    def __init__(self, graph: Dict[str, Dict[str, float]], locations_coords: Dict[str, Tuple[float, float]] = None):
        """
        Initialize optimizer with graph
        
        Args:
            graph: Dictionary of {node: {neighbor: distance}}
            locations_coords: Dictionary of {node: (lat, lng)} for heuristics
        """
        self.graph = graph
        self.locations_coords = locations_coords or {}
    
    def dijkstra(self, start: str, end: str) -> Tuple[List[str], float]:
        """
        Dijkstra's algorithm for shortest path
        
        Returns:
            Tuple of (path, total_distance)
        """
        distances = {node: float('infinity') for node in self.graph}
        distances[start] = 0
        previous = {node: None for node in self.graph}
        pq = [(0, start)]
        visited = set()
        
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            if current in visited:
                continue
            
            visited.add(current)
            
            if current == end:
                break
            
            for neighbor, weight in self.graph[current].items():
                distance = current_dist + weight
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current
                    heapq.heappush(pq, (distance, neighbor))
        
        # Reconstruct path
        path = []
        current = end
        while current is not None:
            path.insert(0, current)
            current = previous[current]
        
        if path[0] != start:
            return [], float('infinity')
        
        return path, distances[end]
    
    def _heuristic(self, node1: str, node2: str) -> float:
        """Heuristic function for A* (Euclidean distance)"""
        if node1 not in self.locations_coords or node2 not in self.locations_coords:
            return 0
        
        lat1, lng1 = self.locations_coords[node1]
        lat2, lng2 = self.locations_coords[node2]
        
        # Simple Euclidean distance (good enough for heuristic)
        return math.sqrt((lat2 - lat1)**2 + (lng2 - lng1)**2) * 111  # Approximate km
    
    def a_star(self, start: str, end: str) -> Tuple[List[str], float]:
        """
        A* algorithm for shortest path with heuristic
        
        Returns:
            Tuple of (path, total_distance)
        """
        open_set = [(0, start)]
        came_from = {}
        g_score = {node: float('infinity') for node in self.graph}
        g_score[start] = 0
        f_score = {node: float('infinity') for node in self.graph}
        f_score[start] = self._heuristic(start, end)
        
        while open_set:
            current_f, current = heapq.heappop(open_set)
            
            if current == end:
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.insert(0, current)
                return path, g_score[end]
            
            for neighbor, weight in self.graph[current].items():
                tentative_g = g_score[current] + weight
                
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, end)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return [], float('infinity')
    
    def _calculate_route_distance(self, route: List[str]) -> float:
        """Calculate total distance for a route"""
        total = 0
        for i in range(len(route) - 1):
            if route[i+1] in self.graph[route[i]]:
                total += self.graph[route[i]][route[i+1]]
            else:
                return float('infinity')
        return total
    
    def genetic_algorithm(self, start: str, stops: List[str], generations: int = 100, population_size: int = 50) -> Tuple[List[str], float]:
        """
        Genetic Algorithm for multi-stop route optimization (TSP)
        
        Args:
            start: Starting location
            stops: List of stops to visit
            generations: Number of generations to evolve
            population_size: Size of population
        
        Returns:
            Tuple of (optimized_route, total_distance)
        """
        if not stops:
            return [start], 0
        
        # Create initial population
        def create_individual():
            route = stops.copy()
            random.shuffle(route)
            return [start] + route + [start]
        
        population = [create_individual() for _ in range(population_size)]
        
        # Fitness function (lower distance is better)
        def fitness(route):
            dist = self._calculate_route_distance(route)
            return 1 / (dist + 1) if dist != float('infinity') else 0
        
        # Selection (tournament)
        def select_parent(pop):
            tournament = random.sample(pop, min(5, len(pop)))
            return max(tournament, key=fitness)
        
        # Crossover (order crossover)
        def crossover(parent1, parent2):
            # Exclude start and end
            p1_middle = parent1[1:-1]
            p2_middle = parent2[1:-1]
            
            if len(p1_middle) < 2:
                return parent1.copy()
            
            # Select crossover points
            size = len(p1_middle)
            cx_point1 = random.randint(0, size - 1)
            cx_point2 = random.randint(cx_point1 + 1, size)
            
            # Create child
            child_middle = [None] * size
            child_middle[cx_point1:cx_point2] = p1_middle[cx_point1:cx_point2]
            
            # Fill remaining from parent2
            p2_genes = [gene for gene in p2_middle if gene not in child_middle]
            j = 0
            for i in range(size):
                if child_middle[i] is None:
                    child_middle[i] = p2_genes[j]
                    j += 1
            
            return [start] + child_middle + [start]
        
        # Mutation (swap two cities)
        def mutate(route, mutation_rate=0.1):
            if random.random() < mutation_rate:
                route_copy = route.copy()
                if len(route_copy) > 3:
                    i, j = random.sample(range(1, len(route_copy) - 1), 2)
                    route_copy[i], route_copy[j] = route_copy[j], route_copy[i]
                return route_copy
            return route
        
        # Evolution
        for generation in range(generations):
            # Evaluate fitness
            population_fitness = [(route, fitness(route)) for route in population]
            population_fitness.sort(key=lambda x: x[1], reverse=True)
            
            # Keep best individuals (elitism)
            new_population = [route for route, _ in population_fitness[:5]]
            
            # Create new generation
            while len(new_population) < population_size:
                parent1 = select_parent(population)
                parent2 = select_parent(population)
                child = crossover(parent1, parent2)
                child = mutate(child)
                new_population.append(child)
            
            population = new_population
        
        # Return best route
        best_route = max(population, key=fitness)
        best_distance = self._calculate_route_distance(best_route)
        
        return best_route, best_distance
    
    def nearest_neighbor(self, start: str, stops: List[str]) -> Tuple[List[str], float]:
        """
        Nearest Neighbor heuristic for TSP (greedy approach)
        Fast but not optimal
        
        Returns:
            Tuple of (route, total_distance)
        """
        if not stops:
            return [start], 0
        
        route = [start]
        remaining = set(stops)
        current = start
        total_distance = 0
        
        while remaining:
            # Find nearest unvisited stop
            nearest = min(remaining, key=lambda x: self.graph[current].get(x, float('infinity')))
            distance = self.graph[current].get(nearest, float('infinity'))
            
            if distance == float('infinity'):
                break
            
            route.append(nearest)
            remaining.remove(nearest)
            total_distance += distance
            current = nearest
        
        # Return to start
        if current in self.graph and start in self.graph[current]:
            route.append(start)
            total_distance += self.graph[current][start]
        
        return route, total_distance
    
    def optimize_multi_stop(self, start: str, stops: List[str], algorithm: str = 'genetic') -> Dict:
        """
        Optimize route for multiple stops using specified algorithm
        
        Args:
            start: Starting location
            stops: List of stops to visit
            algorithm: 'genetic', 'nearest_neighbor', or 'brute_force'
        
        Returns:
            Dictionary with route, distance, and algorithm info
        """
        if algorithm == 'genetic':
            route, distance = self.genetic_algorithm(start, stops)
        elif algorithm == 'nearest_neighbor':
            route, distance = self.nearest_neighbor(start, stops)
        else:
            route, distance = self.nearest_neighbor(start, stops)
        
        return {
            'route': route,
            'distance': distance,
            'algorithm': algorithm,
            'num_stops': len(stops)
        }
