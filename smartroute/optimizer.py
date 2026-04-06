"""
optimizer.py — Multi-Stop Delivery Route

Solves the multi-stop routing sequentially using Dijkstra and A*.
We do not optimize the stop order. We follow the given order exactly
and compare the performance between Dijkstra and A*.
"""

import time
import numpy as np

from smartroute.algorithms import astar, dijkstra


def compute_sequential_route(G, node_ids, weight="travel_time", algorithm="astar", h_weight=1.0):
    """
    Build the complete path by chaining segments between stops using the specified algorithm.
    """
    full_path = []
    segment_paths = []
    segment_costs = []
    total_nodes_explored = 0
    total_execution_time = 0

    if len(node_ids) < 2:
        return full_path, segment_paths, segment_costs, total_nodes_explored, total_execution_time

    for i in range(len(node_ids) - 1):
        source_node = node_ids[i]
        target_node = node_ids[i + 1]

        if algorithm == "astar":
            path, cost, metrics, _ = astar(G, source_node, target_node, weight, h_weight=h_weight)
        else:
            path, cost, metrics, _ = dijkstra(G, source_node, target_node, weight)

        segment_paths.append(path)
        segment_costs.append(cost)
        total_nodes_explored += metrics['nodes_explored']
        total_execution_time += metrics['execution_time']

        if i == 0:
            full_path.extend(path)
        else:
            full_path.extend(path[1:])

    return full_path, segment_paths, segment_costs, total_nodes_explored, total_execution_time


def analyze_delivery_route(G, node_ids, weight="travel_time", h_weight=1.0):
    """
    Computes the sequential route using both Dijkstra and A* and compares them.
    """
    print(f"\n🛤️  Building full route using Dijkstra ({len(node_ids) - 1} segments)...")
    d_full, d_seg_paths, d_seg_costs, d_explored, d_time = compute_sequential_route(
        G, node_ids, weight, algorithm="dijkstra"
    )

    print(f"🛤️  Building full route using A* ({len(node_ids) - 1} segments)...")
    a_full, a_seg_paths, a_seg_costs, a_explored, a_time = compute_sequential_route(
        G, node_ids, weight, algorithm="astar", h_weight=h_weight
    )

    d_cost = sum(d_seg_costs) if d_seg_costs else 0
    a_cost = sum(a_seg_costs) if a_seg_costs else 0

    print("\n" + "-" * 55)
    print("📊  SEQUENTIAL ROUTE SUMMARY")
    print("-" * 55)
    print(f"   Dijkstra cost:  {d_cost:>10.2f} (Explored: {d_explored:,})")
    print(f"   A* cost:        {a_cost:>10.2f} (Explored: {a_explored:,})")
    print("-" * 55 + "\n")

    return {
        "dijkstra": {
            "full_path": d_full,
            "segment_paths": d_seg_paths,
            "segment_costs": d_seg_costs,
            "cost": d_cost,
            "nodes_explored": d_explored,
            "execution_time": d_time
        },
        "astar": {
            "full_path": a_full,
            "segment_paths": a_seg_paths,
            "segment_costs": a_seg_costs,
            "cost": a_cost,
            "nodes_explored": a_explored,
            "execution_time": a_time
        }
    }

