import time
from typing import List, Dict, Tuple

from app.config import settings
from app.utils.metrics_calc import calculate_route_metrics

class NNSolver:
    def __init__(self, bins, distance_matrix):
        self.bins = bins
        self.distance_matrix = distance_matrix
        self.truck_capacity = settings.TRUCK_CAPACITY
        self.emission_factor = settings.EMISSION_FACTOR

        self.depot_id = bins[0]['id']
        self.depot_index = 0

        self.bin_ids = [bin_data['id'] for bin_data in bins[1:]]
        self.id_to_index = {b["id"]: i for i, b in enumerate(bins)}
        self.demand_dict = {b["id"]: b["demand"] for b in bins}
    
    def solve(self) -> Dict:
        start_time = time.time()
        
        routes = []
        unvisited = set(self.bin_ids.copy())

        while unvisited:
            route = self._create_single_trip(unvisited)

            if not route or len(route) <= 2:
                break
            
            routes.append(route)
        
        metrics = calculate_route_metrics(
            routes=routes,
            distance_matrix=self.distance_matrix,
            id_to_index=self.id_to_index,
            demand_dict=self.demand_dict,
            truck_capacity=self.truck_capacity,
            emission_factor=self.emission_factor
        )

        return {
            'best_routes': routes,
            'number_of_trucks': metrics['number_of_trucks'],
            'total_distance': metrics['total_distance'],
            'total_emissions': metrics['total_emissions'],
            'avg_utilization': metrics['average_utilization_ratio'],
            'route_details': metrics['route_details'],
            'best_fitness': 0,
            'fitness_history': 0,
            'computation_time': time.time() - start_time,
            'generations_run': 0
        }

    def _create_single_trip(self, unvisited):
        current_id = self.depot_id
        current_load = 0
        route = [self.depot_id]

        while unvisited:
            nearest_id = self._find_nearest_feasible_bin(current_id, current_load, unvisited)

            if nearest_id is None:
                break
            
            route.append(nearest_id)
            current_load += self.demand_dict[nearest_id]
            current_id = nearest_id

            unvisited.remove(nearest_id)
        
        route.append(self.depot_id)

        return route
    
    def _find_nearest_feasible_bin(self, current_id, current_load, unvisited):
        nearest_id = None
        nearest_distance = float('inf')

        current_idx = self.id_to_index[current_id]

        for bin_id in unvisited:
            bin_demand = self.demand_dict[bin_id]

            if current_load + bin_demand <= self.truck_capacity:
                bin_idx = self.id_to_index[bin_id]
                distance = self.distance_matrix[current_idx][bin_idx]

                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_id = bin_id

        return nearest_id

    