"""
graph_builder.py — Road Network Graph Construction

Downloads real-world road networks from OpenStreetMap using OSMnx,
converts them into NetworkX graphs, adds travel-time edge weights,
and provides utility functions for node lookups and graph statistics.
"""

import os
import time

import networkx as nx
import osmnx as ox

from smartroute.config import CACHE_DIR, DEFAULT_PLACE, NETWORK_TYPE


# ──────────────────────────────────────────────────────────────
# GRAPH LOADING & CACHING
# ──────────────────────────────────────────────────────────────

def load_graph(place_name=DEFAULT_PLACE, network_type=NETWORK_TYPE,
               use_cache=True):
    """
    Load a road network graph from OpenStreetMap.

    Downloads the graph for the given place using OSMnx, adds speed
    and travel-time attributes to every edge, and optionally caches
    the result to disk for faster subsequent loads.

    Args:
        place_name  (str):  Name of the place (city, neighborhood, etc.)
        network_type (str): Road network type — "drive", "walk", "bike", "all"
        use_cache   (bool): If True, load from disk cache when available

    Returns:
        G (nx.MultiDiGraph): The road network graph with attributes:
            - Nodes: 'x' (longitude), 'y' (latitude), 'street_count'
            - Edges: 'length' (meters), 'speed_kph', 'travel_time' (seconds)

    Example:
        >>> G = load_graph("Manhattan, New York, USA")
        >>> print(f"Loaded {len(G.nodes)} intersections, {len(G.edges)} road segments")
    """
    # Build a safe filename from the place name for caching
    safe_name = str(place_name).lower().replace(" ", "_").replace(",", "").replace("[", "").replace("]", "").replace("'", "")
    safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
    cache_path = os.path.join(CACHE_DIR, f"{safe_name}_{network_type}.graphml")

    # ── Try loading from cache first ───────────────────────────
    if use_cache and os.path.exists(cache_path):
        print(f"📂 Loading cached graph from: {cache_path}")
        start = time.time()
        G = ox.io.load_graphml(cache_path)
        elapsed = time.time() - start
        print(f"   ✅ Loaded in {elapsed:.2f}s — "
              f"{len(G.nodes):,} nodes, {len(G.edges):,} edges")
        return G

    # ── Download from OpenStreetMap ────────────────────────────
    print(f"🌐 Downloading road network for: {place_name}")
    print(f"   Network type: {network_type}")
    start = time.time()

    G = ox.graph.graph_from_place(place_name, network_type=network_type)

    download_time = time.time() - start
    print(f"   ⬇️  Downloaded in {download_time:.2f}s")

    # ── Add speed and travel time to edges ─────────────────────
    # OSMnx infers speeds from road type and adds travel_time (seconds)
    print("   🔧 Computing edge speeds and travel times...")
    G = ox.routing.add_edge_speeds(G)
    G = ox.routing.add_edge_travel_times(G)

    # ── Store original travel_time for traffic simulation reset ──
    for u, v, key, data in G.edges(keys=True, data=True):
        data["travel_time_original"] = data.get("travel_time", 0)

    # ── Cache to disk ──────────────────────────────────────────
    if use_cache:
        print(f"   💾 Saving to cache: {cache_path}")
        ox.io.save_graphml(G, cache_path)

    elapsed = time.time() - start
    print(f"   ✅ Graph ready in {elapsed:.2f}s — "
          f"{len(G.nodes):,} nodes, {len(G.edges):,} edges")
    return G


# ──────────────────────────────────────────────────────────────
# NODE LOOKUP UTILITIES
# ──────────────────────────────────────────────────────────────

def get_nearest_node(G, lat, lon):
    """
    Find the graph node closest to the given GPS coordinates.

    Uses OSMnx's fast ball-tree spatial index to snap a (lat, lon)
    coordinate to the nearest intersection in the road network.

    Args:
        G   (nx.MultiDiGraph): The road network graph
        lat (float): Latitude in decimal degrees
        lon (float): Longitude in decimal degrees

    Returns:
        node_id (int): The OSM node ID of the nearest intersection

    Example:
        >>> node = get_nearest_node(G, 40.7580, -73.9855)
        >>> print(f"Nearest node: {node}")
    """
    return ox.distance.nearest_nodes(G, lon, lat)  # Note: OSMnx takes (X, Y) = (lon, lat)


def get_node_coords(G, node_id):
    """
    Get the (latitude, longitude) of a graph node.

    Args:
        G       (nx.MultiDiGraph): The road network graph
        node_id (int): The OSM node ID

    Returns:
        (lat, lon) tuple of floats
    """
    node_data = G.nodes[node_id]
    return node_data["y"], node_data["x"]  # y = lat, x = lon


# ──────────────────────────────────────────────────────────────
# GRAPH STATISTICS
# ──────────────────────────────────────────────────────────────

def get_graph_stats(G):
    """
    Compute summary statistics for the road network graph.

    Returns:
        dict with keys:
            - nodes:            Total intersection count
            - edges:            Total road segment count
            - total_length_km:  Sum of all edge lengths in kilometers
            - avg_edge_length:  Average edge length in meters
            - strongly_connected: Whether the graph is strongly connected
    """
    total_length = sum(
        data.get("length", 0) for _, _, data in G.edges(data=True)
    )
    edge_count = G.number_of_edges()

    stats = {
        "nodes": G.number_of_nodes(),
        "edges": edge_count,
        "total_length_km": round(total_length / 1000, 2),
        "avg_edge_length_m": round(total_length / max(edge_count, 1), 2),
        "strongly_connected": nx.is_strongly_connected(G),
    }
    return stats


def print_graph_stats(G):
    """Print a formatted summary of graph statistics."""
    stats = get_graph_stats(G)
    print("\n" + "=" * 55)
    print("📊  ROAD NETWORK STATISTICS")
    print("=" * 55)
    print(f"   🔵 Intersections (nodes):    {stats['nodes']:>8,}")
    print(f"   🔗 Road segments (edges):    {stats['edges']:>8,}")
    print(f"   📏 Total road length:        {stats['total_length_km']:>8.1f} km")
    print(f"   📐 Avg segment length:       {stats['avg_edge_length_m']:>8.1f} m")
    print(f"   🔄 Strongly connected:       {'Yes ✅' if stats['strongly_connected'] else 'No ❌'}")
    print("=" * 55 + "\n")
    return stats
