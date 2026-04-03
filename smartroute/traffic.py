"""
traffic.py — Dynamic Traffic Simulation

Simulates real-world traffic conditions by modifying edge weights
in the road network graph. Supports multiple traffic profiles
(peak, moderate, off-peak) with road-type-aware multipliers.

How it works:
- Each edge has a base 'travel_time_original' (set during graph building)
- Traffic simulation multiplies this base time by a factor based on:
  1. The road type (highway tag from OSM)
  2. The traffic profile (peak, moderate, off-peak)
  3. A random jitter (±15%) for realism
- The modified 'travel_time' is used by pathfinding algorithms
"""

import random

from smartroute.config import TRAFFIC_PROFILES


# ──────────────────────────────────────────────────────────────
# TRAFFIC APPLICATION
# ──────────────────────────────────────────────────────────────

def apply_traffic(G, profile="peak", seed=42):
    """
    Apply a traffic profile to modify edge travel times.

    Modifies the 'travel_time' attribute of every edge in the graph
    according to the specified traffic profile. Higher-class roads
    (motorways, primary) get larger multipliers during peak hours.

    Args:
        G       (nx.MultiDiGraph): Road network graph (modified in-place)
        profile (str): Traffic profile — "peak", "moderate", or "off_peak"
        seed    (int): Random seed for reproducible jitter

    Returns:
        G (nx.MultiDiGraph): The same graph with updated travel times

    Example:
        >>> G = apply_traffic(G, profile="peak")
        >>> # Edge travel times are now 1.5×–3.5× longer on major roads
    """
    if profile not in TRAFFIC_PROFILES:
        raise ValueError(
            f"Unknown traffic profile: '{profile}'. "
            f"Choose from: {list(TRAFFIC_PROFILES.keys())}"
        )

    random.seed(seed)
    profile_config = TRAFFIC_PROFILES[profile]
    edges_modified = 0
    total_multiplier = 0

    print(f"\n🚦 Applying '{profile}' traffic profile...")

    for u, v, key, data in G.edges(keys=True, data=True):
        # Get the original (no-traffic) travel time
        raw_time = data.get("travel_time_original", data.get("travel_time", 0))
        try:
            original_time = float(raw_time)
        except (ValueError, TypeError):
            # If it's a list or invalid, take the first element or 0
            original_time = float(raw_time[0]) if isinstance(raw_time, list) else 0.0

        # Determine the road type from OSM 'highway' tag
        highway_type = _get_highway_type(data)

        # Look up the multiplier range for this road type and profile
        multiplier = _get_traffic_multiplier(highway_type, profile_config)

        # Apply the multiplier to travel time
        data["travel_time"] = original_time * multiplier
        data["traffic_multiplier"] = multiplier

        edges_modified += 1
        total_multiplier += multiplier

    avg_multiplier = total_multiplier / max(edges_modified, 1)
    print(f"   ✅ Modified {edges_modified:,} edges")
    print(f"   📊 Average traffic multiplier: {avg_multiplier:.2f}×")

    return G


def reset_traffic(G):
    """
    Reset all edge travel times to their original (no-traffic) values.

    Args:
        G (nx.MultiDiGraph): Road network graph (modified in-place)

    Returns:
        G (nx.MultiDiGraph): The same graph with reset travel times
    """
    print("\n🔄 Resetting traffic to baseline (off-peak)...")
    edges_reset = 0

    for u, v, key, data in G.edges(keys=True, data=True):
        if "travel_time_original" in data:
            data["travel_time"] = data["travel_time_original"]
            data["traffic_multiplier"] = 1.0
            edges_reset += 1

    print(f"   ✅ Reset {edges_reset:,} edges to original travel times")
    return G


# ──────────────────────────────────────────────────────────────
# TRAFFIC ANALYSIS
# ──────────────────────────────────────────────────────────────

def get_traffic_stats(G):
    """
    Compute summary statistics about current traffic conditions.

    Returns:
        dict with keys:
            - avg_multiplier:  Average traffic multiplier across all edges
            - max_multiplier:  Maximum traffic multiplier
            - min_multiplier:  Minimum traffic multiplier
            - congested_edges: Number of edges with multiplier > 1.5
            - total_edges:     Total number of edges
    """
    multipliers = []
    for _, _, data in G.edges(data=True):
        mult = data.get("traffic_multiplier", 1.0)
        multipliers.append(mult)

    if not multipliers:
        return {"avg_multiplier": 1.0, "max_multiplier": 1.0,
                "min_multiplier": 1.0, "congested_edges": 0,
                "total_edges": 0}

    return {
        "avg_multiplier": round(sum(multipliers) / len(multipliers), 3),
        "max_multiplier": round(max(multipliers), 3),
        "min_multiplier": round(min(multipliers), 3),
        "congested_edges": sum(1 for m in multipliers if m > 1.5),
        "total_edges": len(multipliers),
    }


def print_traffic_stats(G):
    """Print formatted traffic statistics."""
    stats = get_traffic_stats(G)
    print("\n" + "=" * 50)
    print("🚦  TRAFFIC CONDITIONS")
    print("=" * 50)
    print(f"   📊 Average multiplier:    {stats['avg_multiplier']:.2f}×")
    print(f"   🔴 Max multiplier:        {stats['max_multiplier']:.2f}×")
    print(f"   🟢 Min multiplier:        {stats['min_multiplier']:.2f}×")
    print(f"   ⚠️  Congested edges (>1.5×): "
          f"{stats['congested_edges']:,} / {stats['total_edges']:,} "
          f"({100 * stats['congested_edges'] / max(stats['total_edges'], 1):.1f}%)")
    print("=" * 50 + "\n")
    return stats


# ──────────────────────────────────────────────────────────────
# HELPER FUNCTIONS (Private)
# ──────────────────────────────────────────────────────────────

def _get_highway_type(edge_data):
    """
    Extract the road type from an edge's OSM 'highway' tag.

    The highway tag can be a string or a list (for complex roads).
    We normalize to a single string.

    Args:
        edge_data (dict): Edge attribute dictionary

    Returns:
        str: Normalized highway type (e.g., "primary", "residential")
    """
    highway = edge_data.get("highway", "unclassified")

    # Handle list values (some edges have multiple tags)
    if isinstance(highway, list):
        highway = highway[0]

    return str(highway).lower()


def _get_traffic_multiplier(highway_type, profile_config):
    """
    Compute a traffic multiplier for a road type under a given profile.

    Looks up the (min, max) multiplier range for the highway type,
    then picks a random value within that range for realism.

    Args:
        highway_type   (str):  OSM highway tag
        profile_config (dict): Traffic profile configuration

    Returns:
        float: Traffic multiplier (1.0 = no traffic, 3.0 = severe)
    """
    # Look up range for this road type, fall back to default
    if highway_type in profile_config:
        min_mult, max_mult = profile_config[highway_type]
    else:
        min_mult, max_mult = profile_config.get("default", (1.0, 1.0))

    # Pick a random multiplier within the range
    return random.uniform(min_mult, max_mult)
