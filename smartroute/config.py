"""
config.py — Central Configuration for SmartRoute AI

Contains all constants, default locations, traffic settings,
color palettes, and file paths used across the project.
"""

import os

# ──────────────────────────────────────────────────────────────
# 1. LOCATION SETTINGS
# ──────────────────────────────────────────────────────────────

# Default city for road network download
# We will download Gandhinagar, Gujarat which includes PDEU
DEFAULT_PLACE = "Gandhinagar, Gujarat, India"

# Type of road network to download from OpenStreetMap
# Options: "drive" (car), "walk" (pedestrian), "bike", "all"
NETWORK_TYPE = "drive"

# ──────────────────────────────────────────────────────────────
# 2. DEMO DELIVERY LOCATIONS (Manhattan landmarks)
# ──────────────────────────────────────────────────────────────

# Warehouse / starting depot (PDEU)
WAREHOUSE = {
    "name": "Warehouse (PDEU)",
    "address": "Pandit Deendayal Energy University, Gandhinagar, Gujarat",
}

# Delivery stops — famous landmarks around PDEU / Gandhinagar
DELIVERY_STOPS = [
    {"name": "Stop 1 — GIFT City",             "address": "GIFT City, Gandhinagar, Gujarat"},
    {"name": "Stop 2 — InfoCity Gandhinagar",  "address": "Infocity, Gandhinagar, Gujarat"},
    {"name": "Stop 3 — Swagat Mall",     "address": "Swagat Mall, Gandhinagar, Gujarat"},
    {"name": "Stop 4 — IIT Gandhinagar",   "address": "IIT Gandhinagar, Gandhinagar, Gujarat"},
    {"name": "Stop 5 — GNLU",        "address": "Gujarat National Law University, Gandhinagar, Gujarat"},
]

# Which delivery stop should be used for the A* vs Dijkstra 1-on-1 comparison maps?
# Options: 0 (Stop 1), 1 (Stop 2), 2 (Stop 3), 3 (Stop 4), 4 (Stop 5)
SINGLE_ROUTE_STOP_INDEX = 4

# ──────────────────────────────────────────────────────────────
# 3. TRAFFIC SIMULATION SETTINGS
# ──────────────────────────────────────────────────────────────

# Traffic multipliers by road type and traffic profile
# Each profile maps highway_type → (min_multiplier, max_multiplier)
TRAFFIC_PROFILES = {
    "peak": {
        # Rush hour: major roads heavily congested
        "motorway":      (2.5, 3.5),
        "motorway_link": (2.0, 3.0),
        "trunk":         (2.0, 3.0),
        "trunk_link":    (1.8, 2.5),
        "primary":       (2.0, 2.8),
        "primary_link":  (1.8, 2.5),
        "secondary":     (1.5, 2.2),
        "secondary_link":(1.4, 2.0),
        "tertiary":      (1.3, 1.8),
        "tertiary_link": (1.2, 1.6),
        "residential":   (1.1, 1.4),
        "living_street": (1.0, 1.2),
        "unclassified":  (1.1, 1.5),
        "default":       (1.3, 1.8),
    },
    "moderate": {
        # Mid-day: moderate congestion on major roads
        "motorway":      (1.3, 1.8),
        "motorway_link": (1.2, 1.6),
        "trunk":         (1.3, 1.7),
        "trunk_link":    (1.2, 1.5),
        "primary":       (1.2, 1.6),
        "primary_link":  (1.2, 1.5),
        "secondary":     (1.1, 1.4),
        "secondary_link":(1.1, 1.3),
        "tertiary":      (1.0, 1.2),
        "tertiary_link": (1.0, 1.2),
        "residential":   (1.0, 1.1),
        "living_street": (1.0, 1.0),
        "unclassified":  (1.0, 1.2),
        "default":       (1.1, 1.4),
    },
    "off_peak": {
        # Late night: minimal traffic everywhere
        "default": (1.0, 1.0),
    },
}

# ──────────────────────────────────────────────────────────────
# 4. ALGORITHM SETTINGS
# ──────────────────────────────────────────────────────────────

# Default edge weight attribute for pathfinding
# "travel_time" = seconds, "length" = meters
DEFAULT_WEIGHT = "travel_time"

# Earth's radius in meters (for Haversine distance calculation)
EARTH_RADIUS_M = 6_371_000

# ──────────────────────────────────────────────────────────────
# 5. VISUALIZATION SETTINGS
# ──────────────────────────────────────────────────────────────

# Color palette for routes and markers
COLORS = {
    "warehouse":       "#E74C3C",   # Red
    "delivery_stop":   "#3498DB",   # Blue
    "route_astar":     "#2ECC71",   # Green
    "route_dijkstra":  "#E67E22",   # Orange
    "route_segments": [             # Cycling colors for multi-stop
        "#1ABC9C", "#9B59B6", "#E74C3C",
        "#F39C12", "#3498DB", "#2ECC71",
    ],
    "graph_edges":     "#BDC3C7",   # Light gray
    "graph_nodes":     "#7F8C8D",   # Gray
    "traffic_low":     "#2ECC71",   # Green
    "traffic_medium":  "#F39C12",   # Orange
    "traffic_high":    "#E74C3C",   # Red
}

# Map tile provider for Folium
MAP_TILES = "CartoDB positron"  # Clean, light tiles ideal for route overlay

# ──────────────────────────────────────────────────────────────
# 6. FILE PATHS
# ──────────────────────────────────────────────────────────────

# Base project directory
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Output directory for generated maps and plots
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")

# Cache directory for downloaded graph data
CACHE_DIR = os.path.join(PROJECT_DIR, "cache")

# Ensure output and cache directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
