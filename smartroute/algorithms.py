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

    Returns:
        tuple: (path, cost, metrics, visited_nodes)
    """
    start_time = time.time()
    dist = {source: 0}
    prev = {}
    pq = [(0, source)]
    visited = set()
    nodes_explored = 0

    while pq:
        current_cost, current_node = heapq.heappop(pq)
        if current_node in visited:
            continue
        visited.add(current_node)
        nodes_explored += 1

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
            return path, current_cost, metrics, list(visited)

        for neighbor in G[current_node]:
            if neighbor in visited:
                continue
            edge_cost = _get_min_edge_weight(G, current_node, neighbor, weight)
            new_cost = current_cost + edge_cost
            if new_cost < dist.get(neighbor, float("inf")):
                dist[neighbor] = new_cost
                prev[neighbor] = current_node
                heapq.heappush(pq, (new_cost, neighbor))

    raise ValueError(f"No path exists from node {source} to node {target}")


def astar(G, source, target, weight="travel_time", h_weight=1.0):
    """
    Find the shortest path using A* with a weighted Haversine heuristic.

    Args:
        h_weight (float): Heuristic multiplier. 1.0=Standard A*, 0.0=Dijkstra, >1.0=Greedy.

    Returns:
        tuple: (path, cost, metrics, visited_nodes)
    """
    start_time = time.time()
    target_lat = G.nodes[target]["y"]
    target_lon = G.nodes[target]["x"]

    if weight == "travel_time":
        max_speed_mps = 130 / 3.6
        heuristic_scale = 1.0 / max_speed_mps
    else:
        heuristic_scale = 1.0

    g_score = {source: 0}
    prev = {}
    source_lat = G.nodes[source]["y"]
    source_lon = G.nodes[source]["x"]
    h_source = haversine_distance(source_lat, source_lon, target_lat, target_lon) * heuristic_scale * h_weight
    pq = [(h_source, 0, source)]
    visited = set()
    nodes_explored = 0

    while pq:
        f_score, current_g, current_node = heapq.heappop(pq)
        if current_node in visited:
            continue
        visited.add(current_node)
        nodes_explored += 1

        if current_node == target:
            path = _reconstruct_path(prev, source, target)
            elapsed = time.time() - start_time
            metrics = {
                "algorithm": "A*",
                "execution_time": round(elapsed, 6),
                "nodes_explored": nodes_explored,
                "path_length": len(path),
                "path_cost": round(current_g, 4),
                "h_weight": h_weight
            }
            return path, current_g, metrics, list(visited)

        for neighbor in G[current_node]:
            if neighbor in visited:
                continue
            edge_cost = _get_min_edge_weight(G, current_node, neighbor, weight)
            tentative_g = current_g + edge_cost
            if tentative_g < g_score.get(neighbor, float("inf")):
                g_score[neighbor] = tentative_g
                prev[neighbor] = current_node
                n_lat = G.nodes[neighbor]["y"]
                n_lon = G.nodes[neighbor]["x"]
                h = haversine_distance(n_lat, n_lon, target_lat, target_lon) * heuristic_scale * h_weight
                f = tentative_g + h
                heapq.heappush(pq, (f, tentative_g, neighbor))

    raise ValueError(f"No path exists from node {source} to node {target}")


# ──────────────────────────────────────────────────────────────
# ALGORITHM COMPARISON
# ──────────────────────────────────────────────────────────────

def compare_algorithms(G, source, target, weight="travel_time", h_weight=1.0):
    """
    Run both Dijkstra and A* on the same source→target pair.
    """
    print(f"\n🔍 Running algorithm comparison: {source} → {target}")

    # Run Dijkstra
    d_path, d_cost, d_metrics, d_visited = dijkstra(G, source, target, weight)
    
    # Run A*
    a_path, a_cost, a_metrics, a_visited = astar(G, source, target, weight, h_weight)

    node_reduction = (1 - a_metrics["nodes_explored"] / max(d_metrics["nodes_explored"], 1)) * 100
    time_reduction = (1 - a_metrics["execution_time"] / max(d_metrics["execution_time"], 1e-9)) * 100
    
    return {
        "dijkstra": (d_path, d_cost, d_metrics, d_visited),
        "astar": (a_path, a_cost, a_metrics, a_visited),
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


# Pre-defined lambda for speed
_weight_getter = lambda data_dict, w: float(data_dict.get(w, float("inf"))) if not isinstance(data_dict.get(w), list) else float(data_dict.get(w)[0])

def _get_min_edge_weight(G, u, v, weight):
    """
    Get the minimum edge weight between two nodes in a MultiDiGraph.
    Optimized for lookup speed.
    """
    edges = G[u][v]
    if len(edges) == 1:
        # Fast path for single-edge roads (most common)
        return _weight_getter(next(iter(edges.values())), weight)
    
    return min(_weight_getter(data, weight) for data in edges.values())
