"""
main.py — SmartRoute AI Entry Point

Runs the complete delivery route optimization pipeline:
1. Load road network from OpenStreetMap
2. Run A* vs Dijkstra comparison (no traffic)
3. Apply peak traffic simulation
4. Re-run comparison under traffic
5. Optimize multi-stop delivery route
6. Generate all visualizations

Usage:
    python main.py
"""

import sys
import time

# ── Import SmartRoute modules ──────────────────────────────
from smartroute.config import (
    DEFAULT_PLACE, DEFAULT_WEIGHT, WAREHOUSE, DELIVERY_STOPS,
)
from smartroute.graph_builder import (
    load_graph, get_nearest_node, print_graph_stats,
)
from smartroute.algorithms import (
    compare_algorithms, print_comparison_table,
)
from smartroute.traffic import (
    apply_traffic, reset_traffic, print_traffic_stats,
)
from smartroute.optimizer import optimize_delivery_route
from smartroute.visualizer import (
    plot_route_interactive,
    plot_multi_stop_route,
    plot_algorithm_comparison,
    plot_traffic_comparison,
    plot_delivery_summary,
)


def main():
    """Run the complete SmartRoute AI demo pipeline."""

    print("=" * 60)
    print("🚀  SMARTROUTE AI — Traffic-Aware Delivery Route Optimiser")
    print("=" * 60)
    print()

    total_start = time.time()

    # ══════════════════════════════════════════════════════════
    # STEP 1: Load Road Network
    # ══════════════════════════════════════════════════════════
    print("━" * 60)
    print("📍 STEP 1: Loading Road Network")
    print("━" * 60)

    G = load_graph(DEFAULT_PLACE)
    stats = print_graph_stats(G)

    # ══════════════════════════════════════════════════════════
    # STEP 2: Map Delivery Locations to Graph Nodes
    # ══════════════════════════════════════════════════════════
    print("━" * 60)
    print("📍 STEP 2: Mapping Delivery Locations")
    print("━" * 60)

    import osmnx as ox

    def resolve_coords(location, default=None):
        """Auto-geocodes address if lat/lon are missing."""
        if "lat" in location and "lon" in location:
            return location["lat"], location["lon"]
        elif "address" in location:
            print(f"   🔍 Geocoding '{location['name']}'...")
            try:
                lat, lon = ox.geocode(location["address"])
                return lat, lon
            except Exception as e:
                print(f"      ❌ Failed to geocode '{location['address']}': {e}")
                if default:
                    print(f"      ⚠️  Using fallback coordinates: {default}")
                    return default
                raise e
        else:
            raise ValueError(f"No address or coordinates provided for {location['name']}")

    # Resolve coordinates and snap warehouse to nearest graph node
    w_lat, w_lon = resolve_coords(WAREHOUSE)
    warehouse_node = get_nearest_node(G, w_lat, w_lon)
    print(f"\n   🏭 Warehouse: {WAREHOUSE['name']}")
    print(f"      Node ID: {warehouse_node}")

    # Snap all delivery stop coordinates
    delivery_nodes = []
    stop_names = [WAREHOUSE["name"]]

    for stop in DELIVERY_STOPS:
        s_lat, s_lon = resolve_coords(stop)
        node = get_nearest_node(G, s_lat, s_lon)
        delivery_nodes.append(node)
        stop_names.append(stop["name"])
        print(f"   📦 {stop['name']}")
        print(f"      Node ID: {node}")

    # All nodes: [warehouse, stop1, stop2, ...]
    all_nodes = [warehouse_node] + delivery_nodes

    # ══════════════════════════════════════════════════════════
    # STEP 3: Single-Route Comparison (No Traffic)
    # ══════════════════════════════════════════════════════════
    print("\n" + "━" * 60)
    print("📍 STEP 3: Algorithm Comparison (No Traffic)")
    print("━" * 60)

    # Compare A* vs Dijkstra: warehouse → first delivery stop
    source = warehouse_node
    target = delivery_nodes[0]  # Empire State Building

    comparison_no_traffic = compare_algorithms(
        G, source, target, weight=DEFAULT_WEIGHT
    )
    print_comparison_table(comparison_no_traffic)

    # Generate interactive map for single-route comparison
    plot_route_interactive(
        G,
        route_astar=comparison_no_traffic["astar"][0],
        route_dijkstra=comparison_no_traffic["dijkstra"][0],
        source_node=source,
        target_node=target,
        source_name=WAREHOUSE["name"],
        target_name=DELIVERY_STOPS[0]["name"],
        metrics=comparison_no_traffic,
        filename="single_route_comparison.html",
    )

    # Generate comparison bar chart
    plot_algorithm_comparison(
        comparison_no_traffic,
        filename="algorithm_comparison_no_traffic.png",
    )

    # ══════════════════════════════════════════════════════════
    # STEP 4: Apply Peak Traffic
    # ══════════════════════════════════════════════════════════
    print("\n" + "━" * 60)
    print("📍 STEP 4: Traffic Simulation (Peak Hours)")
    print("━" * 60)

    G = apply_traffic(G, profile="peak")
    print_traffic_stats(G)

    # ══════════════════════════════════════════════════════════
    # STEP 5: Re-run Comparison Under Traffic
    # ══════════════════════════════════════════════════════════
    print("\n" + "━" * 60)
    print("📍 STEP 5: Algorithm Comparison (With Traffic)")
    print("━" * 60)

    comparison_with_traffic = compare_algorithms(
        G, source, target, weight=DEFAULT_WEIGHT
    )
    print_comparison_table(comparison_with_traffic)

    # Generate traffic comparison chart
    plot_traffic_comparison(
        comparison_no_traffic,
        comparison_with_traffic,
        filename="traffic_impact_comparison.png",
    )

    # Generate interactive map showing traffic-aware route
    plot_route_interactive(
        G,
        route_astar=comparison_with_traffic["astar"][0],
        route_dijkstra=comparison_with_traffic["dijkstra"][0],
        source_node=source,
        target_node=target,
        source_name=WAREHOUSE["name"],
        target_name=DELIVERY_STOPS[0]["name"],
        metrics=comparison_with_traffic,
        filename="route_with_traffic.html",
    )

    # ══════════════════════════════════════════════════════════
    # STEP 6: Multi-Stop Delivery Optimization
    # ══════════════════════════════════════════════════════════
    print("\n" + "━" * 60)
    print("📍 STEP 6: Multi-Stop Delivery Optimization")
    print("━" * 60)

    # Reset traffic for fair baseline, then apply moderate traffic
    G = reset_traffic(G)
    G = apply_traffic(G, profile="moderate")

    opt_result = optimize_delivery_route(G, all_nodes, weight=DEFAULT_WEIGHT)

    # Build the ordered stop nodes for map visualization
    # opt_order gives indices into all_nodes
    opt_order = opt_result["optimized_order"]
    ordered_stop_nodes = [all_nodes[i] for i in opt_order[:-1]]  # Exclude final return
    ordered_stop_names = [stop_names[i] for i in opt_order[:-1]]

    # Generate multi-stop delivery map
    plot_multi_stop_route(
        G,
        segment_paths=opt_result["segment_paths"],
        stop_nodes=ordered_stop_nodes,
        stop_names=ordered_stop_names,
        metrics=opt_result,
        filename="delivery_route.html",
    )

    # Generate delivery summary chart
    plot_delivery_summary(
        opt_result,
        stop_names=stop_names,
        filename="delivery_summary.png",
    )

    # ══════════════════════════════════════════════════════════
    # STEP 7: Final Summary
    # ══════════════════════════════════════════════════════════
    total_time = time.time() - total_start

    print("\n" + "=" * 60)
    print("🏁  SMARTROUTE AI — EXECUTION COMPLETE")
    print("=" * 60)
    print(f"\n   ⏱️  Total execution time: {total_time:.2f}s")
    print(f"\n   📁 Output files generated in: output/")
    print(f"      📄 single_route_comparison.html  — A* vs Dijkstra (interactive)")
    print(f"      📄 route_with_traffic.html        — Routes under traffic")
    print(f"      📄 delivery_route.html             — Multi-stop delivery map")
    print(f"      📊 algorithm_comparison_no_traffic.png")
    print(f"      📊 traffic_impact_comparison.png")
    print(f"      📊 delivery_summary.png")
    print(f"\n   💡 Open the .html files in your browser for interactive maps!")
    print("=" * 60)


if __name__ == "__main__":
    main()
