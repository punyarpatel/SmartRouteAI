# 🚀 SmartRoute AI — Traffic-Aware Delivery Route Optimiser

A production-style Python system that computes optimal delivery routes using **A\*** and **Dijkstra** algorithms on real-world OpenStreetMap road networks, with traffic-aware edge weights and multi-stop delivery optimization.

---

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Algorithms Explained](#algorithms-explained)
- [Traffic Simulation](#traffic-simulation)
- [Multi-Stop Optimization](#multi-stop-optimization)
- [Output Examples](#output-examples)
- [Enhancements](#enhancements)

---

## ✨ Features

- **Real-world road networks** from OpenStreetMap via OSMnx
- **Custom A\* implementation** with Haversine heuristic (not just a wrapper)
- **Custom Dijkstra implementation** for fair baseline comparison
- **Traffic simulation** with peak/moderate/off-peak profiles
- **Multi-stop delivery optimization** using Greedy Nearest Neighbor + 2-opt
- **Interactive Folium maps** (HTML) with color-coded routes and markers
- **Matplotlib charts** for algorithm performance comparison
- **Modular, well-documented code** with clear separation of concerns

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      main.py                            │
│              (Entry Point & Pipeline)                   │
└──────────┬──────────┬──────────┬──────────┬─────────────┘
           │          │          │          │
    ┌──────▼──┐ ┌─────▼────┐ ┌──▼───┐ ┌───▼────────┐
    │ graph_  │ │algorithms│ │traffic│ │ optimizer  │
    │ builder │ │  .py     │ │ .py   │ │   .py      │
    │  .py    │ │          │ │       │ │            │
    │         │ │ Dijkstra │ │ Peak  │ │ Greedy NN  │
    │ OSMnx   │ │ A*       │ │ Off-  │ │ 2-opt      │
    │ NetworkX│ │ Haversine│ │ peak  │ │ Distance   │
    │ Cache   │ │ Compare  │ │ Reset │ │ Matrix     │
    └─────────┘ └──────────┘ └───────┘ └────────────┘
                       │
                ┌──────▼──────┐
                │ visualizer  │
                │    .py      │
                │             │
                │ Folium Maps │
                │ Matplotlib  │
                │ Charts      │
                └─────────────┘
```

---

## 🔧 Installation

### Prerequisites

- Python 3.11 or newer
- Internet connection (for first-time OSM data download)

### Setup

```bash
# 1. Navigate to the project directory
cd "d:\Study\SEM 6\AI Project"

# 2. Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Usage

### Run the full demo

```bash
python main.py
```

This will:
1. Download the Manhattan road network (cached after first run)
2. Compare A\* vs Dijkstra algorithms
3. Simulate peak traffic conditions
4. Optimize a multi-stop delivery route
5. Generate interactive maps and comparison charts

### Output Files

After running, check the `output/` directory:

| File | Description |
|------|-------------|
| `single_route_comparison.html` | Interactive map: A\* vs Dijkstra routes |
| `route_with_traffic.html` | Route comparison under peak traffic |
| `delivery_route.html` | Multi-stop delivery route with numbered stops |
| `algorithm_comparison_no_traffic.png` | Bar chart: algorithm metrics |
| `traffic_impact_comparison.png` | Before/after traffic comparison |
| `delivery_summary.png` | Delivery optimization results |

---

## 📁 Project Structure

```
AI Project/
├── main.py                  # Entry point — runs full pipeline
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── smartroute/
│   ├── __init__.py          # Package initialization
│   ├── config.py            # All settings and constants
│   ├── graph_builder.py     # OSM graph loading & caching
│   ├── algorithms.py        # Dijkstra & A* implementations
│   ├── traffic.py           # Traffic simulation
│   ├── optimizer.py         # Multi-stop route optimization
│   └── visualizer.py        # Map & chart generation
├── output/                  # Generated maps and charts
└── cache/                   # Cached graph data
```

---

## 🧠 Algorithms Explained

### Dijkstra's Algorithm

- **Type**: Uninformed (blind) search
- **Strategy**: Explore nodes in order of increasing cost from source
- **Guarantee**: Always finds the optimal path
- **Weakness**: Explores in all directions — wastes time on nodes far from target

### A\* Algorithm

- **Type**: Informed (heuristic) search
- **Strategy**: `f(n) = g(n) + h(n)` — actual cost + estimated remaining cost
- **Heuristic**: Haversine distance (great-circle distance on Earth's surface)
- **Guarantee**: Optimal path (because Haversine is admissible — never overestimates)
- **Advantage**: Explores far fewer nodes than Dijkstra by "aiming" toward the target

### Why Haversine?

The Haversine formula computes the shortest distance between two points on a sphere.
For road networks, this is always ≤ the actual road distance, making it a perfect
admissible heuristic for A\*.

---

## 🚦 Traffic Simulation

Traffic is simulated by multiplying edge travel times by road-type-dependent factors:

| Profile | Motorway | Primary | Residential |
|---------|----------|---------|-------------|
| Peak    | 2.5-3.5× | 2.0-2.8× | 1.1-1.4× |
| Moderate| 1.3-1.8× | 1.2-1.6× | 1.0-1.1× |
| Off-peak| 1.0×     | 1.0×     | 1.0×      |

A random ±15% jitter is added for realism. Traffic is non-destructive — original
travel times are preserved and can be restored.

---

## 📦 Multi-Stop Optimization

The multi-stop delivery problem is solved in 4 steps:

1. **Distance Matrix**: Compute pairwise A\* costs between all stops
2. **Greedy Nearest Neighbor**: Start at warehouse → always visit nearest unvisited
3. **2-opt Improvement**: Iteratively swap edge pairs to reduce total cost
4. **Route Reconstruction**: Chain A\* paths into one continuous route

This is a practical approach to the Travelling Salesman Problem (TSP), delivering
near-optimal solutions in reasonable time.

---

## 🌟 Potential Enhancements

- **Streamlit Web Dashboard** — interactive UI with real-time controls
- **Real-time traffic API** — integrate Google Maps or TomTom traffic data
- **Vehicle capacity constraints** — package weights and volume limits
- **Multi-vehicle routing (VRP)** — fleet management with multiple trucks
- **Route animation** — animated marker traversal on the map
- **Docker deployment** — containerized one-command setup
- **Performance profiling** — memory and CPU usage analysis
- **Unit test suite** — pytest-based test coverage

---

## 📄 License

This project is for educational purposes — AI Project, Semester 6.
