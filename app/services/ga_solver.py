import random
import time
from typing import List, Dict, Tuple

from app.config import settings
from .nn_solver import NNSolver
from app.utils.metrics_calc import calculate_route_metrics


class GASolver:
    
    def __init__(self, bins, distance_matrix, adaptive=True):
        self.bins = bins
        self.distance_matrix = distance_matrix
        self.truck_capacity = settings.TRUCK_CAPACITY

        # Adaptive parameters
        n_bins = len([b for b in bins if b["id"] != "depot"])
        
        if adaptive and n_bins > 0:
            # pop size
            if n_bins > 100:
                self.population_size = 120
            elif n_bins > 50:
                self.population_size = 80
            else:
                self.population_size = min(100, n_bins * 2)

            # gens
            if n_bins > 100:
                self.num_generations = 150
            elif n_bins > 50:
                self.num_generations = 250
            else:
                self.num_generations = settings.NUM_GENERATIONS

            print(f"🧬 Adaptive mode: Pop={self.population_size}, Gen={self.num_generations} for {n_bins} bins")
        else:
            self.population_size = settings.POPULATION_SIZE
            self.num_generations = settings.NUM_GENERATIONS

        self.tournament_size = settings.TOURNAMENT_SIZE
        self.crossover_rate = settings.CROSSOVER_RATE
        self.mutation_rate = settings.MUTATION_RATE
        self.elitism_count = settings.ELITISM_COUNT
        self.early_stopping_enabled = settings.EARLY_STOPPING_ENABLED
        self.early_stopping_patience = settings.EARLY_STOPPING_PATIENCE
        self.early_stopping_min_delta = settings.EARLY_STOPPING_MIN_DELTA
        self.w1 = settings.WEIGHT_DISTANCE
        self.w2 = settings.WEIGHT_UNUSED_CAPACITY
        self.emission_factor = settings.EMISSION_FACTOR
        
        self.bin_ids = [b["id"] for b in bins if b["id"] != "depot"] # fix later
        self.id_to_index = {b["id"]: i for i, b in enumerate(bins)}
        self.demand_dict = {b["id"]: b["demand"] for b in bins}

    def solve(self) -> Dict:
        """Main GA execution"""
        start_time = time.time()
        
        best_solution_ever = None
        best_fitness_ever = float('inf')
        fitness_history = []

        gen_without_improvement = 0
        last_best_fitness = float('inf')
        actual_generations = 0

        # Initialize population
        population = self._initialize_population()
         
        # Evolution loop
        for generation in range(self.num_generations):

            actual_generations += 1
            # 1. Evaluate fitness
            fitness_values = self._evaluate_population(population)

            # Track Best Solution
            best_idx = fitness_values.index(min(fitness_values))
            best_fitness = fitness_values[best_idx]
            
            if best_fitness < best_fitness_ever:
                best_fitness_ever = best_fitness
                best_solution_ever = population[best_idx].copy()
            
            fitness_history.append(best_fitness)

            # Early Stopping Check
            if self.early_stopping_enabled:
                if last_best_fitness - best_fitness >= self.early_stopping_min_delta:
                    gen_without_improvement = 0
                    last_best_fitness = best_fitness
                else:
                    gen_without_improvement += 1
                
                if gen_without_improvement >= self.early_stopping_patience:
                    break

            # 2. Selection
            parents = self._select_parents(population, fitness_values)

            # 3. Crossover
            offspring = self._crossover_population(parents)
            
            # 4. Mutation
            offspring = self._mutate_population(offspring)

            # 5. Elitism
            offspring_fitness = self._evaluate_population(offspring)
            if self.elitism_count > 0:
                offspring = self._apply_elitism(population, fitness_values, offspring, offspring_fitness)

            # 6. Create new population
            population = offspring

        best_routes = self._decode_routes(best_solution_ever)

        metrics = calculate_route_metrics(
            routes=best_routes,
            distance_matrix=self.distance_matrix,
            id_to_index=self.id_to_index,
            demand_dict=self.demand_dict,
            truck_capacity=self.truck_capacity,
            emission_factor=self.emission_factor
        )

        return {
            'best_solution': best_solution_ever,
            'best_routes': best_routes,
            'number_of_trucks': metrics['number_of_trucks'],
            'total_distance': metrics['total_distance'],
            'total_emissions': metrics['total_emissions'],
            'avg_utilization': metrics['average_utilization_ratio'],
            'route_details': metrics['route_details'],
            'best_fitness': best_fitness_ever,
            'fitness_history': fitness_history,
            'computation_time': time.time() - start_time,
            'generations_run': actual_generations
        }

    def _initialize_population(self):
        """Create initial population"""
        population = []

        try:
            nn_chromosome = self._create_nn_seed()
            population.append(nn_chromosome)
            print(f"✓ NN seed created: {len(nn_chromosome)} bins")
        except Exception as e:
            print(f"⚠️  NN seeding failed: {e}. Using full random initialization.")
        
        if nn_chromosome is not None:
            num_variants = int(self.population_size * 0.5)
            
            for i in range(num_variants):
                variant = nn_chromosome.copy()
                
                # Progressive mutation intensity: 5% to 20%
                mutation_intensity = 0.05 + (0.15 * i / num_variants)
                num_swaps = max(1, int(len(variant) * mutation_intensity))
                
                # Apply multiple swaps
                for _ in range(num_swaps):
                    i_pos, j_pos = random.sample(range(len(variant)), 2)
                    variant[i_pos], variant[j_pos] = variant[j_pos], variant[i_pos]
                
                population.append(variant)
        
        # Fill remaining with random solutions
        while len(population) < self.population_size:
            individual = random.sample(self.bin_ids, len(self.bin_ids))
            population.append(individual)
        
        return population

    def _create_nn_seed(self):
        """
        Create initial chromosome from NN solution
        Converts NN route format to GA chromosome format
        """
        # Initialize your existing NN solver
        nn_solver = NNSolver(
            bins=self.bins,
            distance_matrix=self.distance_matrix
        )
        
        # Get NN solution
        nn_result = nn_solver.solve()
        
        chromosome = []
        
        for route in nn_result['best_routes']:
            for stop in route:
                if stop != 'depot':
                    chromosome.append(stop)
        
        missing = set(self.bin_ids) - set(chromosome)
        if missing:
            print(f"⚠ Missing bins from NN seed: {missing}")
            chromosome.extend(list(missing))
        
        chromosome = list(dict.fromkeys(chromosome))
        
        return chromosome

    def _decode_routes(self, chromosome):
        """ Decode a chromosome into feasible CVRP routes."""
        demand_dict = {b["id"]: b["demand"] for b in self.bins}
        routes = []
        current_route = []
        current_load = 0

        for bin_id in chromosome:
            demand = demand_dict[bin_id]
            if current_load + demand > self.truck_capacity:
                routes.append(["depot"] + current_route + ["depot"])
                current_route = [bin_id]
                current_load = demand
            else:
                current_route.append(bin_id)
                current_load += demand

        if current_route:
            routes.append(["depot"] + current_route + ["depot"])

        return routes
    
    def _calculate_fitness(self, routes):
        total_distance = 0
        total_unused = 0
        num_routes = len(routes)

        for route in routes:
            if not route:
                continue

            route_distance = 0
            route_load = 0
            for i in range(len(route) - 1):
                from_id = self.id_to_index[route[i]]
                to_id = self.id_to_index[route[i + 1]]
                route_distance += self.distance_matrix[from_id][to_id]
            total_distance += route_distance
                
            route_load = sum(
                self.demand_dict[bin_id]
                for bin_id in route
                if bin_id != 'depot'
            )
            unused = max(self.truck_capacity - route_load, 0)
            total_unused += unused

        fitness = (self.w1 * total_distance + 
               self.w2 * total_unused + 
               1000 * num_routes)
        return fitness

    def _evaluate_population(self, population):
        fitness_values = []
        for individual in population:
            routes = self._decode_routes(individual)
            fitness = self._calculate_fitness(routes)
            fitness_values.append(fitness)
        return fitness_values
    
    def _tournament_selection(self, population, fitness_values):
        indices = random.sample(range(len(population)), self.tournament_size)
        best_index = min(indices, key=lambda i: fitness_values[i])
        return population[best_index]
    
    def _select_parents(self, population, fitness_values):
        parents = []
        for _ in range(self.population_size):
            parent = self._tournament_selection(population, fitness_values)
            parents.append(parent)
        return parents
    
    def _order_crossover_single(self, parent1, parent2, start, end):
        """Helper function for order crossover."""
        size = len(parent1)
        child = [None] * size

        child[start:end + 1] = parent1[start:end + 1]

        # Fill the remaining positions with genes from parent2
        pos = (end + 1) % size
        for gene in parent2:
            if gene not in child:
                child[pos] = gene
                pos = (pos + 1) % size

        return child
    
    def _order_crossover(self, parent1, parent2):
        """Perform Order Crossover (OX) between two parents."""
        size = len(parent1)

        cx1 = random.randint(0, size - 1)
        cx2 = random.randint(0, size - 1)
        start, end = min(cx1, cx2), max(cx1, cx2)

        child1 = self._order_crossover_single(parent1, parent2, start, end)
        child2 = self._order_crossover_single(parent2, parent1, start, end)
        return child1, child2
    
    def _crossover_population(self, parents):
        """Create new population via crossover."""
        offspring = []

        for i in range(0, len(parents) - 1, 2):

            if random.random() < self.crossover_rate:
                child1, child2 = self._order_crossover(parents[i], parents[i + 1])
            else:
                child1, child2 = parents[i].copy(), parents[i + 1].copy()

            offspring.extend([child1, child2])

        if len(parents) % 2 == 1:
            offspring.append(parents[-1].copy())
        
        return offspring
    
    def _swap_mutation(self, individual):
        """Perform swap mutation on an individual."""
        mutated = individual.copy()

        if random.random() < self.mutation_rate:
            num_swaps = random.randint(3, 5)
            
            for _ in range(num_swaps):
                idx1, idx2 = random.sample(range(len(mutated)), 2)
                mutated[idx1], mutated[idx2] = mutated[idx2], mutated[idx1]
        
        return mutated
    
    def _mutate_population(self, offspring):
        """Apply mutation to the offspring population."""
        return [self._swap_mutation(ind) for ind in offspring]

    def _apply_elitism(self, old_population, old_fitness, new_population, new_fitness):
        """Preserve the best individuals from the current population."""
        elite_indices = sorted(range(len(old_fitness)), 
                              key=lambda i: old_fitness[i])[:self.elitism_count]
        worst_indices = sorted(range(len(new_fitness)), 
                              key=lambda i: new_fitness[i], 
                              reverse=True)[:self.elitism_count]
        for elite_idx, worst_idx in zip(elite_indices, worst_indices):
            new_population[worst_idx] = old_population[elite_idx].copy()
        
        return new_population