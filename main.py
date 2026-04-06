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
    from smartroute.optimizer import analyze_delivery_route
    from smartroute.visualizer import (
        plot_route_interactive, plot_multi_stop_route,
        plot_algorithm_comparison, plot_traffic_comparison, plot_delivery_summary
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

# 🏁 Geocode Cache to prevent redundant OSN lookups
GEO_CACHE_FILE = os.path.join(os.path.dirname(__file__), "cache", "geocode_cache.json")
_geocode_cache = {}

def _load_geocode_cache():
    global _geocode_cache
    if os.path.exists(GEO_CACHE_FILE):
        try:
            with open(GEO_CACHE_FILE, 'r', encoding='utf-8') as f:
                _geocode_cache = json.load(f)
        except Exception:
            _geocode_cache = {}

def _save_geocode_cache():
    os.makedirs(os.path.dirname(GEO_CACHE_FILE), exist_ok=True)
    try:
        with open(GEO_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(_geocode_cache, f, indent=4)
    except Exception:
        pass

_load_geocode_cache()

def resolve_coords(location):
    """Geocodes location if coords are missing."""
    if "lat" in location and "lon" in location:
        return float(location["lat"]), float(location["lon"])
    
    address = location["address"]
    if address in _geocode_cache:
        # ⚡ Cache Hit!
        return tuple(_geocode_cache[address])
    
    print(f"   [GEO] Geocoding '{location.get('name', 'Unknown')}'...", file=sys.stderr)
    try:
        lat, lon = ox.geocode(address)
        _geocode_cache[address] = [lat, lon]
        _save_geocode_cache()
        return lat, lon
    except Exception as e:
        print(f"      [ERROR] CRITICAL: Failed to resolve address '{address}': {e}", file=sys.stderr)
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
    try:
        G = load_graph(mission["place"], coords=mission.get("place_coords"))
    except Exception as e:
        print(f"\n      ❌ CRITICAL: Could not load road network for '{mission['place']}'.", file=sys.stderr)
        print(f"         Reason: {str(e)}", file=sys.stderr)
        print(f"         TIP: Try a more specific city/state name.", file=sys.stderr)
        sys.exit(1)
        
    if len(G.nodes) == 0:
        print(f"\n      ❌ CRITICAL: Graph for '{mission['place']}' is empty.", file=sys.stderr)
        sys.exit(1)
        
    print(f"   🏙️ Graph Density Resolved ({len(G.nodes):,} nodes).", file=sys.stderr)

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

    # 🚀 COMPLETE THE CIRCUIT: Add warehouse back to the end for a round trip
    all_nodes = [warehouse_node] + stop_nodes + [warehouse_node]
    stop_names.append(mission["warehouse"]["name"])
    print(f"🚀 FINAL MISSION LOADED: {len(all_nodes)} nodes in active manifest.", file=sys.stderr)

    # 3. AI Algorithm Comparison (No Traffic)
    source, target = warehouse_node, (stop_nodes[0] if stop_nodes else warehouse_node)
    comp = compare_algorithms(G, source, target, weight=DEFAULT_WEIGHT, h_weight=mission["h_weight"])
    
    # Logging Experiment Results
    experiment.log_trial("Dijkstra", "None", comp["dijkstra"][2]["execution_time"], comp["dijkstra"][2]["nodes_explored"], comp["dijkstra"][1])
    experiment.log_trial("A*", "None", comp["astar"][2]["execution_time"], comp["astar"][2]["nodes_explored"], comp["astar"][1])

    # Replaced redundant plot_route_interactive call with faster logging
    print(f"   📈 Phase 1 Analytics: Baseline A* vs Dijkstra computed in {comp['astar'][2]['execution_time']:.4f}s")

    # 4. ML-Based Traffic Simulation ── [TIMER START]
    sim_start = time.time()
    hour = int(mission.get("hour", 12))
    sim_incident = mission.get("sim_incident", False)

    # 🚀 PORTFOLIO OPTIMIZATION: Extracting features directly from MultiDiGraph
    features = []
    edge_refs = []
    
    for u, v, k, d in G.edges(keys=True, data=True):
        hw = d.get("highway", "residential")
        features.append([hour, hw[0] if isinstance(hw, list) else hw, d.get("length", 100)])
        edge_refs.append((u, v, k))
    
    delays = predictor.predict_batch(features)
    
    # 🏎️ Update Edge Weights directly
    for i, (u, v, k) in enumerate(edge_refs):
        d = G.edges[u, v, k]
        original = float(d.get('travel_time_original', d.get('travel_time', 10)))
        if 'travel_time_original' not in d:
             d['travel_time_original'] = original
        d['travel_time'] = original + delays[i]
        if sim_incident and random.random() < 0.03:
            d['travel_time'] *= 10.0

    # 4b. AI Performance Delta (With Traffic) ── [Dynamic Analysis]
    comp_traffic = compare_algorithms(G, source, target, weight=DEFAULT_WEIGHT, h_weight=mission["h_weight"])
    
    # 🕵️ Generate Intelligence Assets (Fresh Charts)
    plot_algorithm_comparison(comp, filename="algorithm_comparison_no_traffic.png")
    plot_traffic_comparison(comp, comp_traffic, filename="traffic_impact_comparison.png")
    
    plot_route_interactive(
        G, route_astar=comp_traffic["astar"][0], route_dijkstra=comp_traffic["dijkstra"][0], 
        source_node=source, target_node=target, 
        filename="route_with_traffic.html"
    )

    print(f"   ⚡ ML Simulation completed for {len(edge_refs):,} edges in {time.time() - sim_start:.3f}s")

    # 5. Multi-Stop Sequential Analysis (A* vs Dijkstra)
    analysis = analyze_delivery_route(G, all_nodes, weight=DEFAULT_WEIGHT, h_weight=mission["h_weight"])
    
    print(f"📊 SEQUENCE AUDIT: Analyzed path across {len(all_nodes)} nodes.")
    improvement_over_dijkstra = analysis["dijkstra"]["execution_time"] - analysis["astar"]["execution_time"]
    print(f"   ✨ Discovery: A* was {improvement_over_dijkstra:.5f}s faster than Dijkstra.")

    final_order = list(range(len(all_nodes)))
    plot_multi_stop_route(
        G, segment_paths=analysis["astar"]["segment_paths"], 
        stop_nodes=[all_nodes[i] for i in final_order], 
        stop_names=[stop_names[i] for i in final_order], 
        metrics={
            "greedy_cost": analysis["dijkstra"]["execution_time"],
            "optimized_cost": analysis["astar"]["execution_time"],
            "sa_improvement": improvement_over_dijkstra
        }, 
        filename="delivery_route.html"
    )
    
    # 📊 Final Logistics Chart
    plot_delivery_summary(analysis, stop_names=[stop_names[i] for i in final_order], filename="delivery_summary.png")

    # 6. Save Results & Data Export
    experiment.save_to_csv()
    results = {
        "timestamp": time.ctime(),
        "total_time": round(time.time() - total_start, 2),
        "hour": hour,
        "traffic_ml": "Active",
        "sa_improvement": round(improvement_over_dijkstra, 5),
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
