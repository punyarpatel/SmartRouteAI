import random
import math

def simulated_annealing_tsp(distance_matrix, initial_order, temp=100.0, cooling=0.995):
    """Refinement strategy for multi-stop delivery sequences."""
    n = len(distance_matrix)
    if n < 3: return initial_order, sum(distance_matrix[i][j] for i, j in zip(initial_order[:-1], initial_order[1:]))

    # Inner stops (exclude warehouse at index 0 and end)
    current_order = list(initial_order[1:-1])
    
    def get_full_cost(order):
        cost = distance_matrix[0][order[0]]
        for i in range(len(order)-1):
            cost += distance_matrix[order[i]][order[i+1]]
        cost += distance_matrix[order[-1]][0]
        return cost

    current_cost = get_full_cost(current_order)
    best_order, best_cost = list(current_order), current_cost

    while temp > 0.05:
        # Try a swap mutation
        i, j = random.sample(range(len(current_order)), 2)
        new_order = list(current_order)
        new_order[i], new_order[j] = new_order[j], new_order[i]
        
        new_cost = get_full_cost(new_order)
        delta = new_cost - current_cost

        # Metropolis Accept Criterion
        if delta < 0 or random.random() < math.exp(-delta / temp):
            current_order, current_cost = new_order, new_cost
            if current_cost < best_cost:
                best_order = list(current_order)
                best_cost = current_cost
        
        temp *= cooling

    return [0] + best_order + [0], best_cost
