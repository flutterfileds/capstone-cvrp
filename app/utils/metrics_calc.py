from typing import List, Dict

def calculate_route_distance(route, distance_matrix, id_to_index):
    if not route:
        return 0.0

    total_distance = 0.0
    depot_idx = id_to_index["depot"]
    first_bin_idx = id_to_index[route[0]]
    total_distance += distance_matrix[depot_idx][first_bin_idx]

    for i in range(len(route) - 1):
        from_idx = id_to_index[route[i]]
        to_idx = id_to_index[route[i + 1]]
        total_distance += distance_matrix[from_idx][to_idx]
    
    last_bin_idx = id_to_index[route[-1]]
    total_distance += distance_matrix[last_bin_idx][depot_idx]

    return total_distance

def calculate_route_load(route, demand_dict):
    return sum(demand_dict[bin_id] for bin_id in route)

def calculate_emissions(distance, emission_factor):
    return distance * emission_factor

def calculate_route_metrics(routes, distance_matrix, id_to_index, demand_dict, truck_capacity, emission_factor):
    total_distance = 0.0
    total_emissions = 0.0
    total_utilization = 0.0
    total_unused_capacity = 0.0
    route_count = 0
    route_details = []

    for i, route in enumerate(routes):
        route_distance = calculate_route_distance(route, distance_matrix, id_to_index)
        route_load = calculate_route_load(route, demand_dict)
        unused_capacity = max(truck_capacity - route_load, 0)
        utilization_ratio = route_load / truck_capacity if truck_capacity > 0 else 0.0
        route_emissions = calculate_emissions(route_distance, emission_factor)

        total_distance += route_distance
        total_unused_capacity += unused_capacity
        total_utilization += utilization_ratio
        total_emissions += route_emissions

        route_details.append({
            "truck_no": i + 1,
            "route": route,  # or detailed bin objects
            "distance": route_distance,
            "load": route_load,
            "utilization": utilization_ratio,
            "unused_capacity": unused_capacity,
            "emissions": route_emissions
        })

    route_count = len(routes)
    avg_utilization_ratio = (total_utilization / route_count) if route_count > 0 else 0.0

    return {
        "total_distance": total_distance,
        "total_emissions": total_emissions,
        "average_utilization_ratio": avg_utilization_ratio,
        "number_of_trucks": route_count,
        "route_details": route_details   
    }
