"""
algorithms.py — Pathfinding Algorithms (Dijkstra & A*)

Custom implementations of Dijkstra's and A* shortest-path algorithms
built from scratch using Python's heapq priority queue. These run on
NetworkX MultiDiGraph structures from OpenStreetMap data.

Why custom implementations?
- Demonstrates genuine understanding of the algorithms
- Allows tracking metrics (nodes explored, execution time)
- Enables fair side-by-side comparison
"""

import heapq
import math
import time

from smartroute.config import EARTH_RADIUS_M


# ──────────────────────────────────────────────────────────────
# HEURISTIC FUNCTION
# ──────────────────────────────────────────────────────────────

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two GPS points.

    Uses the Haversine formula to compute the shortest distance
    over the Earth's surface between two (lat, lon) coordinates.

    This is used as the A* heuristic because:
    - It is ADMISSIBLE: never overestimates the actual road distance
      (straight-line distance ≤ road distance, always)
    - It is CONSISTENT: satisfies the triangle inequality

    Args:
        lat1, lon1 (float): First point (decimal degrees)
        lat2, lon2 (float): Second point (decimal degrees)

    Returns:
        float: Distance in meters

    Example:
        >>> haversine_distance(40.7580, -73.9855, 40.7484, -73.9857)
        1066.8  # ~1 km between Times Square and Empire State Building
    """
    # Convert degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_M * c


# ──────────────────────────────────────────────────────────────
# DIJKSTRA'S ALGORITHM (Baseline)
# ──────────────────────────────────────────────────────────────

def dijkstra(G, source, target, weight="travel_time"):
    """
    Find the shortest path using Dijkstra's algorithm.

    Dijkstra explores nodes in order of increasing distance from
    the source. It guarantees the optimal path but explores many
    unnecessary nodes because it has no sense of direction.

    How it works:
    1. Start at source with cost 0
    2. Use a priority queue (min-heap) ordered by path cost
    3. Pop the cheapest node, explore all its neighbors
    4. If a cheaper path to a neighbor is found, update it
    5. Stop when the target is popped from the queue

    Args:
        G      (nx.MultiDiGraph): Road network graph
        source (int): Starting node ID
        target (int): Destination node ID
        weight (str): Edge attribute to use as cost ("travel_time" or "length")

    Returns:
        tuple: (path, cost, metrics)
            - path    (list[int]): Sequence of node IDs from source to target
            - cost    (float):     Total path cost
            - metrics (dict):      Performance metrics:
                - 'algorithm':      "Dijkstra"
                - 'execution_time': Time in seconds
                - 'nodes_explored': Number of nodes popped from queue
                - 'path_length':    Number of nodes in path
                - 'path_cost':      Total edge weight sum

    Raises:
        ValueError: If no path exists between source and target
    """
    start_time = time.time()

    # ── Data structures ─────────────────────────────────────
    # dist[node] = best known cost from source to node
    dist = {source: 0}

    # prev[node] = predecessor node on the best path
    prev = {}

    # Priority queue: (cost, node_id)
    # We use a counter to break ties deterministically
    pq = [(0, source)]

    # Track which nodes have been finalized (popped from queue)
    visited = set()
    nodes_explored = 0

    # ── Main loop ───────────────────────────────────────────
    while pq:
        current_cost, current_node = heapq.heappop(pq)

        # Skip if we've already found a better path to this node
        if current_node in visited:
            continue

        visited.add(current_node)
        nodes_explored += 1

        # ── Found the target! Reconstruct path ──────────────
        if current_node == target:
            path = _reconstruct_path(prev, source, target)
            elapsed = time.time() - start_time

            metrics = {
                "algorithm": "Dijkstra",
                "execution_time": round(elapsed, 6),
                "nodes_explored": nodes_explored,
                "path_length": len(path),
                "path_cost": round(current_cost, 4),
            }
            return path, current_cost, metrics

        # ── Explore neighbors ───────────────────────────────
        # G[current_node] returns a dict of {neighbor: {key: edge_data}}
        for neighbor in G[current_node]:
            if neighbor in visited:
                continue

            # Get the minimum-weight edge between current and neighbor
            # (MultiDiGraph can have parallel edges)
            edge_cost = _get_min_edge_weight(G, current_node, neighbor, weight)
            new_cost = current_cost + edge_cost

            # If this path is better, update
            if new_cost < dist.get(neighbor, float("inf")):
                dist[neighbor] = new_cost
                prev[neighbor] = current_node
                heapq.heappush(pq, (new_cost, neighbor))

    # No path found
    raise ValueError(
        f"No path exists from node {source} to node {target}"
    )


# ──────────────────────────────────────────────────────────────
# A* ALGORITHM (Optimized with Heuristic)
# ──────────────────────────────────────────────────────────────

def astar(G, source, target, weight="travel_time"):
    """
    Find the shortest path using the A* algorithm with Haversine heuristic.

    A* is an informed search algorithm that uses a heuristic to guide
    exploration toward the target. It explores far fewer nodes than
    Dijkstra while still guaranteeing the optimal path.

    How it works:
    1. f(n) = g(n) + h(n)
       - g(n) = actual cost from source to node n
       - h(n) = estimated cost from n to target (Haversine distance)
       - f(n) = estimated total cost through node n
    2. Priority queue ordered by f(n) instead of just g(n)
    3. The heuristic "pulls" exploration toward the target

    The Haversine heuristic is ADMISSIBLE (never overestimates) because
    the straight-line distance is always ≤ the actual road distance.

    Args:
        G      (nx.MultiDiGraph): Road network graph
        source (int): Starting node ID
        target (int): Destination node ID
        weight (str): Edge attribute to use as cost

    Returns:
        tuple: (path, cost, metrics) — same format as dijkstra()
    """
    start_time = time.time()

    # Get target coordinates for the heuristic
    target_lat = G.nodes[target]["y"]
    target_lon = G.nodes[target]["x"]

    # ── Determine heuristic scaling ─────────────────────────
    # If weight is "travel_time", we need to convert distance (meters)
    # to an estimated time. We use max road speed to ensure admissibility.
    if weight == "travel_time":
        # Assume max possible speed = 130 km/h = 36.11 m/s
        # This ensures h(n) never overestimates travel time
        max_speed_mps = 130 / 3.6  # km/h to m/s
        heuristic_scale = 1.0 / max_speed_mps
    else:
        # For distance-based weight, haversine gives meters directly
        heuristic_scale = 1.0

    # ── Data structures ─────────────────────────────────────
    g_score = {source: 0}   # Best known cost from source
    prev = {}               # Predecessor map

    # Compute initial heuristic
    source_lat = G.nodes[source]["y"]
    source_lon = G.nodes[source]["x"]
    h_source = haversine_distance(source_lat, source_lon,
                                  target_lat, target_lon) * heuristic_scale

    # Priority queue: (f_score, g_score, node_id)
    # Including g_score as tiebreaker favors nodes closer to source
    pq = [(h_source, 0, source)]

    visited = set()
    nodes_explored = 0

    # ── Main loop ───────────────────────────────────────────
    while pq:
        f_score, current_g, current_node = heapq.heappop(pq)

        if current_node in visited:
            continue

        visited.add(current_node)
        nodes_explored += 1

        # ── Found the target! ───────────────────────────────
        if current_node == target:
            path = _reconstruct_path(prev, source, target)
            elapsed = time.time() - start_time

            metrics = {
                "algorithm": "A*",
                "execution_time": round(elapsed, 6),
                "nodes_explored": nodes_explored,
                "path_length": len(path),
                "path_cost": round(current_g, 4),
            }
            return path, current_g, metrics

        # ── Explore neighbors ───────────────────────────────
        for neighbor in G[current_node]:
            if neighbor in visited:
                continue

            edge_cost = _get_min_edge_weight(G, current_node, neighbor, weight)
            tentative_g = current_g + edge_cost

            if tentative_g < g_score.get(neighbor, float("inf")):
                g_score[neighbor] = tentative_g
                prev[neighbor] = current_node

                # Compute heuristic for neighbor
                n_lat = G.nodes[neighbor]["y"]
                n_lon = G.nodes[neighbor]["x"]
                h = haversine_distance(n_lat, n_lon,
                                       target_lat, target_lon) * heuristic_scale

                f = tentative_g + h
                heapq.heappush(pq, (f, tentative_g, neighbor))

    raise ValueError(
        f"No path exists from node {source} to node {target}"
    )


# ──────────────────────────────────────────────────────────────
# ALGORITHM COMPARISON
# ──────────────────────────────────────────────────────────────

def compare_algorithms(G, source, target, weight="travel_time"):
    """
    Run both Dijkstra and A* on the same source→target pair
    and return a side-by-side comparison of their performance.

    Args:
        G      (nx.MultiDiGraph): Road network graph
        source (int): Starting node ID
        target (int): Destination node ID
        weight (str): Edge attribute for cost

    Returns:
        dict with keys:
            - 'dijkstra': (path, cost, metrics)
            - 'astar':    (path, cost, metrics)
    """
    print(f"\n🔍 Running algorithm comparison: {source} → {target}")
    print(f"   Weight attribute: {weight}")

    # Run Dijkstra
    d_path, d_cost, d_metrics = dijkstra(G, source, target, weight)
    print(f"   📊 Dijkstra: {d_metrics['nodes_explored']:,} nodes explored, "
          f"{d_metrics['execution_time']:.4f}s")

    # Run A*
    a_path, a_cost, a_metrics = astar(G, source, target, weight)
    print(f"   📊 A*:       {a_metrics['nodes_explored']:,} nodes explored, "
          f"{a_metrics['execution_time']:.4f}s")

    # Compute improvement
    node_reduction = (1 - a_metrics["nodes_explored"] /
                      max(d_metrics["nodes_explored"], 1)) * 100
    time_reduction = (1 - a_metrics["execution_time"] /
                      max(d_metrics["execution_time"], 1e-9)) * 100

    print(f"   ⚡ A* explored {node_reduction:.1f}% fewer nodes")
    print(f"   ⚡ A* was {time_reduction:.1f}% faster")

    return {
        "dijkstra": (d_path, d_cost, d_metrics),
        "astar": (a_path, a_cost, a_metrics),
        "node_reduction_pct": round(node_reduction, 2),
        "time_reduction_pct": round(time_reduction, 2),
    }


def print_comparison_table(comparison):
    """Print a formatted comparison table of algorithm metrics."""
    d_metrics = comparison["dijkstra"][2]
    a_metrics = comparison["astar"][2]

    print("\n" + "=" * 60)
    print("⚔️   ALGORITHM COMPARISON: DIJKSTRA vs A*")
    print("=" * 60)
    print(f"  {'Metric':<25} {'Dijkstra':>15} {'A*':>15}")
    print("  " + "-" * 55)
    print(f"  {'Execution Time (s)':<25} {d_metrics['execution_time']:>15.6f} "
          f"{a_metrics['execution_time']:>15.6f}")
    print(f"  {'Nodes Explored':<25} {d_metrics['nodes_explored']:>15,} "
          f"{a_metrics['nodes_explored']:>15,}")
    print(f"  {'Path Cost':<25} {d_metrics['path_cost']:>15.2f} "
          f"{a_metrics['path_cost']:>15.2f}")
    print(f"  {'Path Length (nodes)':<25} {d_metrics['path_length']:>15,} "
          f"{a_metrics['path_length']:>15,}")
    print("  " + "-" * 55)
    print(f"  {'A* Node Reduction':<25} {comparison['node_reduction_pct']:>14.1f}%")
    print(f"  {'A* Speed Improvement':<25} {comparison['time_reduction_pct']:>14.1f}%")
    print("=" * 60 + "\n")


# ──────────────────────────────────────────────────────────────
# HELPER FUNCTIONS (Private)
# ──────────────────────────────────────────────────────────────

def _reconstruct_path(prev, source, target):
    """
    Reconstruct the shortest path from predecessor map.

    Traces back from target to source using the prev dictionary
    built during pathfinding, then reverses to get source→target order.

    Args:
        prev   (dict): Mapping node → predecessor node
        source (int):  Starting node
        target (int):  Destination node

    Returns:
        list[int]: Ordered list of node IDs from source to target
    """
    path = []
    current = target

    while current != source:
        path.append(current)
        current = prev[current]

    path.append(source)
    path.reverse()
    return path


def _get_min_edge_weight(G, u, v, weight):
    """
    Get the minimum edge weight between two nodes in a MultiDiGraph.

    Since OSM road networks can have parallel edges (e.g., multiple
    lanes), we pick the edge with the smallest weight value.

    Args:
        G      (nx.MultiDiGraph): Road network
        u, v   (int): Source and target node IDs
        weight (str): Edge attribute name

    Returns:
        float: Minimum weight value among all edges u→v
    """
    def get_float_weight(data_dict, w):
        val = data_dict.get(w, float("inf"))
        try:
            return float(val)
        except (ValueError, TypeError):
            if isinstance(val, list) and val:
                return float(val[0])
            return float("inf")

    edges = G[u][v]  # Dict of {key: edge_data}
    return min(get_float_weight(data, weight) for data in edges.values())
