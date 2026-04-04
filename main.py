"""
main.py — SmartRoute AI Entry Point (Dynamic CLI Version)

Accepts mission parameters and runs the optimization pipeline.
Outputs interactive maps, charts, and a results.json for the React frontend.

Usage:
    python main.py --mission '{"place": "Manhattan", "stops": [...]}'
"""

import sys
import time
import json
import argparse
import os

# 🩺 Strategic Startup Heartbeat
print(">> SMARTROUTE AI - ENGINE HEARTBEAT: Startup sequence initiated...", file=sys.stderr)

try:
    import numpy as np
    import pandas as pd
    print("   ✅ Stage 1: Core Data Math Loaded.", file=sys.stderr)
    
    import osmnx as ox
    print("   ✅ Stage 2: OSM Mapping Engine Loaded.", file=sys.stderr)
    
    import folium
    print("   ✅ Stage 3: Visualizer Systems Ready.", file=sys.stderr)

    from smartroute.config import (
        DEFAULT_PLACE, DEFAULT_WEIGHT, WAREHOUSE, DELIVERY_STOPS, OUTPUT_DIR
    )
    from smartroute.graph_builder import load_graph, get_nearest_node
    from smartroute.algorithms import compare_algorithms
    from smartroute.optimizer import optimize_delivery_route
    from smartroute.visualizer import (
        plot_route_interactive, plot_multi_stop_route
    )
    print("   🚀 All AI Systems Go.", file=sys.stderr)
    
except Exception as e:
    import traceback
    print("\n" + "!"*60, file=sys.stderr)
    print(f"SMARTROUTE AI - CRITICAL DEPENDENCY FAILURE", file=sys.stderr)
    print(f"FAILED AT COMPONENT: {type(e).__name__}", file=sys.stderr)
    print("!"*60 + "\n", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

def resolve_coords(location):
    """Geocodes location if coords are missing."""
    if "lat" in location and "lon" in location:
        return float(location["lat"]), float(location["lon"])
    
    print(f"   [GEO] Geocoding '{location.get('name', 'Unknown')}'...", file=sys.stderr)
    try:
        lat, lon = ox.geocode(location["address"])
        return lat, lon
    except Exception as e:
        print(f"      [ERROR] CRITICAL: Failed to resolve address '{location.get('address')}': {e}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description="SmartRoute AI Runner")
    parser.add_argument("--mission", type=str, help="Path to mission.json file")
    args = parser.parse_args()

    mission = {
        "place": DEFAULT_PLACE,
        "warehouse": WAREHOUSE,
        "stops": DELIVERY_STOPS,
        "h_weight": 1.0,
        "traffic_profile": "peak"
    }

    if args.mission and os.path.exists(args.mission):
        try:
            with open(args.mission, 'r', encoding='utf-8') as f:
                mission.update(json.load(f))
        except Exception as e:
            print(f"   ❌ ERROR loading mission file: {e}", file=sys.stderr)
            sys.exit(1)

    print("=" * 60)
    print(">> SMARTROUTE AI - MISSION START")
    print(f"   LOCATION: {mission['place']}")
    print("=" * 60)

    import random
    from smartroute.traffic_engine import TrafficPredictor
    from smartroute.metaheuristics import simulated_annealing_tsp
    from smartroute.experiments import RouteExperiment
    
    total_start = time.time()
    predictor = TrafficPredictor()
    predictor.train_synthetic()
    experiment = RouteExperiment()

    # 1. Load Graph ── [Stage 4 Heartbeat]
    if not mission.get("place") or str(mission["place"]).strip() == "":
        print(f"   ⚠️ WARNING: No city provided. Defaulting to: {DEFAULT_PLACE}", file=sys.stderr)
        mission["place"] = DEFAULT_PLACE

    print(f"   🛰️ Stage 4: Loading Road Network for '{mission['place']}'...", file=sys.stderr)
    G = load_graph(mission["place"])
    print(f"   🏙️ Graph Density Resolved.", file=sys.stderr)

    # 2. Map Locations ── [MISSION DEBUGGER ENABLED]
    print(f"\n📡 RECEIVING MISSION: {len(mission.get('stops', []))} delivery targets.", file=sys.stderr)
    
    w_coords = resolve_coords(mission["warehouse"])
    if not w_coords: 
        print(f"      ❌ CRITICAL: WAREHOUSE ADDRESS FAILED GEOCODE: {mission['warehouse']['address']}", file=sys.stderr)
        sys.exit(1)
    
    warehouse_node = get_nearest_node(G, w_coords[0], w_coords[1])
    
    stop_nodes = []
    stop_names = [mission["warehouse"]["name"]]
    
    for i, stop in enumerate(mission.get("stops", [])):
        print(f"   🔍 Geocoding Stop {i+1}: '{stop.get('name', 'Unnamed')}'", file=sys.stderr)
        coords = resolve_coords(stop)
        if coords:
            node = get_nearest_node(G, coords[0], coords[1])
            stop_nodes.append(node)
            stop_names.append(stop["name"])
            print(f"      ✅ OK: Resolved '{stop['name']}' to Node {node}", file=sys.stderr)
        else:
            print(f"      ❌ ERROR: Could not resolve address for '{stop.get('name')}'", file=sys.stderr)
            print(f"         Address: {stop.get('address')}", file=sys.stderr)

    if not stop_nodes:
        print(f"      ❌ MISSION ABORTED: Zero valid delivery stops found in manifest.", file=sys.stderr)
        sys.exit(1)

    all_nodes = [warehouse_node] + stop_nodes
    print(f"🚀 FINAL MISSION LOADED: {len(all_nodes)} nodes in active manifest.", file=sys.stderr)

    # 3. AI Algorithm Comparison (No Traffic)
    source, target = warehouse_node, (stop_nodes[0] if stop_nodes else warehouse_node)
    comp = compare_algorithms(G, source, target, weight=DEFAULT_WEIGHT, h_weight=mission["h_weight"])
    
    # Logging Experiment Results
    experiment.log_trial("Dijkstra", "None", comp["dijkstra"][2]["execution_time"], comp["dijkstra"][2]["nodes_explored"], comp["dijkstra"][1])
    experiment.log_trial("A*", "None", comp["astar"][2]["execution_time"], comp["astar"][2]["nodes_explored"], comp["astar"][1])

    plot_route_interactive(
        G, route_astar=comp["astar"][0], route_dijkstra=comp["dijkstra"][0], 
        visited_astar=comp["astar"][3], visited_dijkstra=comp["dijkstra"][3], 
        source_node=source, target_node=target, 
        extra_stops=stop_nodes, extra_stop_names=stop_names[1:],
        filename="comparison.html"
    )

    # 4. ML-Based Traffic Simulation ── [TIMER START]
    sim_start = time.time()
    hour = int(mission.get("hour", 12))
    sim_incident = mission.get("sim_incident", False)

    # 🚀 Batch Extraction for Speed (Vectorization)
    edges_to_predict = []
    keys = []
    for u, v, k, data in G.edges(data=True, keys=True):
        road_type = data.get("highway", "residential")
        if isinstance(road_type, list): road_type = road_type[0]
        length = float(data.get('length', 0))
        edges_to_predict.append((hour, road_type, length))
        keys.append((u, v, k))

    # Single call for the whole city! 🏎️
    delays = predictor.predict_batch(edges_to_predict)

    for i, (u, v, k) in enumerate(keys):
        data = G.edges[u, v, k]
        base_time = float(data.get('travel_time_original', data.get('travel_time', 0)))
        data['travel_time'] = base_time + delays[i]
        
        # Incident simulation (Fast)
        if sim_incident and random.random() < 0.05:
            data['travel_time'] *= 10.0 

    print(f"   ⚡ ML Simulation completed for {len(keys):,} edges in {time.time() - sim_start:.3f}s")

    # 5. Multi-Stop Sequence Optimization (TSP)
    opt_result = optimize_delivery_route(G, all_nodes, weight=DEFAULT_WEIGHT)
    dist_matrix = opt_result["distance_matrix"]
    
    # 🕵️ Metaheuristic Portfolio (Portfolio Logic: Best of 2-opt + SA)
    opt_order_2opt, opt_cost_2opt = opt_result["optimized_order"], opt_result["optimized_cost"]
    sa_order, sa_cost = simulated_annealing_tsp(dist_matrix, opt_order_2opt)
    
    # Selection of the overall best found sequence
    final_order, final_cost = (sa_order, sa_cost) if sa_cost < opt_cost_2opt else (opt_order_2opt, opt_cost_2opt)
    
    # 🕵️ Sequence Audit
    print(f"📊 SEQUENCE AUDIT: Final optimized visits: {len(final_order)} nodes total.")
    improvement_over_greedy = opt_result["greedy_cost"] - final_cost
    print(f"   ✨ Metaheuristic Discovery: Overall cost reduction of {improvement_over_greedy:.2f}s")

    plot_multi_stop_route(
        G, segment_paths=opt_result["segment_paths"], 
        stop_nodes=[all_nodes[i] for i in final_order], 
        stop_names=[stop_names[i] for i in final_order], 
        metrics={
            "greedy_cost": opt_result["greedy_cost"],
            "optimized_cost": final_cost,
            "sa_improvement": round(opt_result["greedy_cost"] - final_cost, 2)
        }, 
        filename="delivery_route.html"
    )

    # 6. Save Results & Data Export
    experiment.save_to_csv()
    results = {
        "timestamp": time.ctime(),
        "total_time": round(time.time() - total_start, 2),
        "hour": hour,
        "traffic_ml": "Active",
        "sa_improvement": round(opt_result["greedy_cost"] - final_cost, 2),
        "comparison_no_traffic": {
            "dijkstra": {"cost": round(comp["dijkstra"][1], 1), "nodes": len(comp["dijkstra"][3])},
            "astar": {"cost": round(comp["astar"][1], 1), "nodes": len(comp["astar"][3])},
            "reduction": comp["node_reduction_pct"]
        },
        "optimization": {"orders": [stop_names[i] for i in final_order]}
    }
    
    with open(os.path.join(OUTPUT_DIR, "results.json"), "w") as f:
        json.dump(results, f, indent=4)

    print("\n>> MISSION COMPLETE")
    print(f"   Execution time: {results['total_time']}s")
    print(f"   💡 TIP: View the full mission sequence in the 'Logistics Optimization' tab.")
    print(f"   Output folder: {OUTPUT_DIR}")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        import sys
        print("\n" + "!"*60, file=sys.stderr)
        print("SMARTROUTE AI - CRITICAL ENGINE FAILURE", file=sys.stderr)
        print("!"*60 + "\n", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
