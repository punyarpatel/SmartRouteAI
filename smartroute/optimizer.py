"""
optimizer.py — Multi-Stop Delivery Route Optimization

Solves the problem: given a warehouse and multiple delivery stops,
find the best order to visit all stops and return to the warehouse.

This is a variant of the Travelling Salesman Problem (TSP).
We use two approaches:
1. Greedy Nearest Neighbor — fast, decent solution
2. 2-opt Local Search — iteratively improves the greedy solution

The optimizer uses A* pathfinding to compute pairwise distances
between all stops, then optimizes the visit order.
"""

import time

import numpy as np

from smartroute.algorithms import astar


# ──────────────────────────────────────────────────────────────
# DISTANCE MATRIX COMPUTATION
# ──────────────────────────────────────────────────────────────

def compute_distance_matrix(G, node_ids, weight="travel_time"):
    """
    Compute pairwise shortest-path costs between all locations.

    Runs A* between every pair of nodes to build an N×N cost matrix.
    This matrix is the foundation for route optimization.

    Args:
        G        (nx.MultiDiGraph): Road network graph
        node_ids (list[int]): List of graph node IDs for all locations
                              (index 0 = warehouse, rest = delivery stops)
        weight   (str): Edge attribute for cost

    Returns:
        np.ndarray: N×N matrix where matrix[i][j] = cost from i to j

    Example:
        >>> matrix = compute_distance_matrix(G, [node_w, node_1, node_2])
        >>> print(matrix[0][1])  # Cost from warehouse to stop 1
    """
    n = len(node_ids)
    matrix = np.zeros((n, n))

    print(f"\n📐 Computing {n}×{n} distance matrix ({n * (n-1)} A* calls)...")
    start = time.time()

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            try:
                _, cost, _, _ = astar(G, node_ids[i], node_ids[j], weight)
                matrix[i][j] = cost
            except ValueError:
                # No path exists — use very large cost
                matrix[i][j] = float("inf")
                print(f"   ⚠️  No path from {node_ids[i]} to {node_ids[j]}")

    elapsed = time.time() - start
    print(f"   ✅ Distance matrix computed in {elapsed:.2f}s")

    return matrix


# ──────────────────────────────────────────────────────────────
# GREEDY NEAREST NEIGHBOR
# ──────────────────────────────────────────────────────────────

def greedy_nearest_neighbor(distance_matrix):
    """
    Find a delivery order using the Greedy Nearest Neighbor heuristic.

    Starting from the warehouse (index 0), always visit the nearest
    unvisited stop, then return to the warehouse at the end.

    How it works:
    1. Start at warehouse (index 0)
    2. Look at all unvisited stops
    3. Pick the one with the smallest travel cost
    4. Move there and repeat
    5. After visiting all stops, return to warehouse

    This is fast (O(n²)) but may not find the optimal solution.

    Args:
        distance_matrix (np.ndarray): N×N cost matrix

    Returns:
        tuple: (visit_order, total_cost)
            - visit_order (list[int]): Indices in visit order (starts & ends at 0)
            - total_cost  (float):     Total route cost

    Example:
        >>> order, cost = greedy_nearest_neighbor(matrix)
        >>> print(f"Visit order: {order}, Total cost: {cost:.2f}")
    """
    n = len(distance_matrix)
    visited = {0}       # Start at warehouse (index 0)
    order = [0]         # Visit order starts with warehouse
    total_cost = 0
    current = 0

    print("\n🏃 Running Greedy Nearest Neighbor...")

    while len(visited) < n:
        # Find the nearest unvisited stop
        best_next = None
        best_cost = float("inf")

        for j in range(n):
            if j not in visited and distance_matrix[current][j] < best_cost:
                best_next = j
                best_cost = distance_matrix[current][j]

        if best_next is None:
            break

        visited.add(best_next)
        order.append(best_next)
        total_cost += best_cost
        current = best_next

    # Return to warehouse
    total_cost += distance_matrix[current][0]
    order.append(0)

    # 🛡️ Sequence Integrity Check
    if len(visited) < n:
        unvisited = [j for j in range(n) if j not in visited]
        print(f"   ⚠️ WARNING: Optimizer could not reach {len(unvisited)} stops (Node Indices: {unvisited})")
        print("      Ensure all stops are on connected road segments.")
    else:
        print(f"   ✅ All {n-1} delivery targets successfully sequenced.")

    print(f"   📊 Greedy total cost: {total_cost:.2f}")

    return order, total_cost


# ──────────────────────────────────────────────────────────────
# 2-OPT LOCAL SEARCH IMPROVEMENT
# ──────────────────────────────────────────────────────────────

def two_opt_improve(distance_matrix, initial_order, max_iterations=1000):
    """
    Improve a route using the 2-opt local search algorithm.

    2-opt works by repeatedly trying to swap two edges in the route.
    If swapping reduces the total cost, the swap is kept.

    How it works:
    1. Take the initial route: [0, A, B, C, D, 0]
    2. For each pair of edges, try reversing the segment between them
       Example: [0, A, B, C, D, 0] → [0, A, C, B, D, 0]
    3. If the new route is shorter, keep it
    4. Repeat until no improvement is found (or max iterations)

    This is a well-known improvement heuristic for TSP that typically
    produces solutions within 5-10% of optimal.

    Args:
        distance_matrix (np.ndarray): N×N cost matrix
        initial_order   (list[int]):  Starting visit order
        max_iterations  (int):        Maximum improvement iterations

    Returns:
        tuple: (improved_order, improved_cost)
    """
    print("\n🔧 Running 2-opt improvement...")

    # Work with the inner nodes (exclude start/end warehouse)
    # Route: [0, a, b, c, ..., 0] → we optimize [a, b, c, ...]
    route = list(initial_order[1:-1])  # Remove start/end warehouse
    n = len(route)

    if n < 2:
        return initial_order, initial_order_cost(distance_matrix, initial_order)

    def route_cost(r):
        """Calculate total cost of a route (including warehouse start/end)."""
        if not r:
            return 0
        cost = distance_matrix[0][r[0]]  # Warehouse → first stop
        for i in range(len(r) - 1):
            cost += distance_matrix[r[i]][r[i + 1]]
        cost += distance_matrix[r[-1]][0]  # Last stop → warehouse
        return cost

    best_cost = route_cost(route)
    improved = True
    iteration = 0

    while improved and iteration < max_iterations:
        improved = False
        iteration += 1

        for i in range(n - 1):
            for j in range(i + 1, n):
                # Try reversing the segment between i and j
                new_route = route[:i] + route[i:j + 1][::-1] + route[j + 1:]
                new_cost = route_cost(new_route)

                if new_cost < best_cost - 1e-10:  # Small epsilon for float comparison
                    route = new_route
                    best_cost = new_cost
                    improved = True

    # Reconstruct full order with warehouse at start and end
    improved_order = [0] + route + [0]

    improvement = initial_order_cost(distance_matrix, initial_order) - best_cost
    improvement_pct = (improvement / max(
        initial_order_cost(distance_matrix, initial_order), 1e-9)) * 100

    print(f"   ✅ 2-opt completed in {iteration} iterations")
    print(f"   📊 Improved cost: {best_cost:.2f}")
    print(f"   ⚡ Improvement: {improvement:.2f} ({improvement_pct:.1f}%)")

    return improved_order, best_cost


def initial_order_cost(distance_matrix, order):
    """Calculate total cost of a complete route order."""
    cost = 0
    for i in range(len(order) - 1):
        cost += distance_matrix[order[i]][order[i + 1]]
    return cost


# ──────────────────────────────────────────────────────────────
# FULL ROUTE CONSTRUCTION
# ──────────────────────────────────────────────────────────────

def build_full_route(G, node_ids, visit_order, weight="travel_time"):
    """
    Build the complete path by chaining A* segments between stops.

    Given the optimized visit order and the actual graph node IDs,
    runs A* between consecutive stops to get the road-level path.

    Args:
        G           (nx.MultiDiGraph): Road network graph
        node_ids    (list[int]): Node IDs (index 0 = warehouse)
        visit_order (list[int]): Indices in node_ids, optimized order
        weight      (str): Edge attribute for cost

    Returns:
        tuple: (full_path, segment_paths, segment_costs)
            - full_path     (list[int]): Complete path of node IDs
            - segment_paths (list[list[int]]): Path for each segment
            - segment_costs (list[float]): Cost for each segment
    """
    print(f"\n🛤️  Building full route ({len(visit_order) - 1} segments)...")

    full_path = []
    segment_paths = []
    segment_costs = []

    for i in range(len(visit_order) - 1):
        source_idx = visit_order[i]
        target_idx = visit_order[i + 1]

        source_node = node_ids[source_idx]
        target_node = node_ids[target_idx]

        path, cost, _, _ = astar(G, source_node, target_node, weight)

        segment_paths.append(path)
        segment_costs.append(cost)

        # Append path nodes (avoid duplicating the connection node)
        if i == 0:
            full_path.extend(path)
        else:
            full_path.extend(path[1:])  # Skip first node (shared with previous segment)

    total_cost = sum(segment_costs)
    print(f"   ✅ Full route: {len(full_path):,} nodes, "
          f"total cost: {total_cost:.2f}")

    return full_path, segment_paths, segment_costs


# ──────────────────────────────────────────────────────────────
# COMPLETE OPTIMIZATION PIPELINE
# ──────────────────────────────────────────────────────────────

def optimize_delivery_route(G, node_ids, weight="travel_time"):
    """
    Complete multi-stop delivery optimization pipeline.

    Runs the full optimization process:
    1. Compute distance matrix (pairwise A* costs)
    2. Find initial order (greedy nearest neighbor)
    3. Improve order (2-opt local search)
    4. Build full route on the road network

    Args:
        G        (nx.MultiDiGraph): Road network graph
        node_ids (list[int]): [warehouse_node, stop1_node, stop2_node, ...]
        weight   (str): Edge attribute for cost

    Returns:
        dict with keys:
            - 'greedy_order':   Greedy visit order
            - 'greedy_cost':    Greedy total cost
            - 'optimized_order': 2-opt improved visit order
            - 'optimized_cost':  2-opt improved total cost
            - 'full_path':       Complete node-level path
            - 'segment_paths':   Individual segment paths
            - 'segment_costs':   Individual segment costs
            - 'distance_matrix': Pairwise cost matrix
    """
    # Step 0: Check for enough locations to optimize
    if len(node_ids) < 2:
        print("   ⚠️  Insufficient locations for multi-stop optimization. Skipping.")
        return {
            "greedy_order": [0, 0] if len(node_ids) == 1 else [],
            "greedy_cost": 0,
            "optimized_order": [0, 0] if len(node_ids) == 1 else [],
            "optimized_cost": 0,
            "full_path": [],
            "segment_paths": [],
            "segment_costs": [],
            "distance_matrix": np.zeros((len(node_ids), len(node_ids))),
        }

    # Step 1: Distance matrix
    dist_matrix = compute_distance_matrix(G, node_ids, weight)

    # Step 2: Greedy nearest neighbor
    greedy_order, greedy_cost = greedy_nearest_neighbor(dist_matrix)

    # Step 3: 2-opt improvement
    opt_order, opt_cost = two_opt_improve(dist_matrix, greedy_order)

    # Step 4: Build the actual road-level path
    full_path, seg_paths, seg_costs = build_full_route(
        G, node_ids, opt_order, weight
    )

    # Summary
    improvement = greedy_cost - opt_cost
    improvement_pct = (improvement / max(greedy_cost, 1e-9)) * 100

    print("\n" + "-" * 55)
    print("📊  OPTIMIZATION SUMMARY")
    print("-" * 55)
    print(f"   Greedy cost:    {greedy_cost:>10.2f}")
    print(f"   Optimized cost: {opt_cost:>10.2f}")
    print(f"   Improvement:    {improvement:>10.2f} ({improvement_pct:.1f}%)")
    print(f"   Visit order:    {opt_order}")
    print("-" * 55 + "\n")

    return {
        "greedy_order": greedy_order,
        "greedy_cost": greedy_cost,
        "optimized_order": opt_order,
        "optimized_cost": opt_cost,
        "full_path": full_path,
        "segment_paths": seg_paths,
        "segment_costs": seg_costs,
        "distance_matrix": dist_matrix,
    }
