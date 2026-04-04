# 🚀 SmartRoute AI — Delivery Route Optimiser (AI Lab MVP)

An advanced traffic-aware delivery route optimization system built for the **AI Systems Lab**. It uses **A*** and **Dijkstra** algorithms on real-world OpenStreetMap road graphs to compute optimal multi-stop routes.

---

## 🔬 AI Lab Key Features

*   **Search Frontier Visualisation**: Interactive maps show the "Search Cone" of A* vs. the "Blind Search" of Dijkstra.
*   **Dynamic Heuristic Weighting**: Adjust the influence of the Haversine heuristic (Dijkstra vs. Optimal A* vs. Greedy Search).
*   **Real-world Road Graphs**: Live data fetching from OpenStreetMap via OSMnx.
*   **Traffic-Aware Intelligence**: Simulated peak/moderate traffic profiles that shift routing dynamically.
*   **TSP Optimization**: Deliveries optimized using Greedy Nearest Neighbor and 2-opt refinement.

---

## 🏗️ Technical Architecture

The system is split into a **Python Optimization Engine** and a **React (Next.js) Mission Control**.

```
┌───────────────────────────┐      ┌───────────────────────────┐
│   React Mission Dashboard │ <──> │   Python AI Engine (CLI)  │
│      (Next.js + Tailwind) │      │   (NetworkX + OSMnx)     │
└───────────────────────────┘      └───────────────────────────┘
            │                                    │
    • Interactive Forms                  • Custom Dijkstra/A*
    • Live KPI Visualization             • TSP Solver (2-opt)
    • Search Frontier Overlays           • Traffic Multipliers
```

---

## 🔧 Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Internet connection (to fetch map data)

### 1. Python Backend Setup
```bash
# Create and activate virtual environment
python -m venv venv
./venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. React Dashboard Setup
```bash
cd web-dashboard
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to access the Mission Control.

---

## 🚀 Usage

1.  **Select Location**: Enter a city (e.g., "Manhattan" or "Gandhinagar").
2.  **Add Stops**: Add delivery addresses in the sidebar.
3.  **Tune AI**: Adjust the **Heuristic Weight** slider to observe search space differences.
4.  **Simulate Traffic**: Choose a profile (Peak, Moderate) to see route adaptation.
5.  **Run Mission**: Click "RUN MISSION" to trigger the engine.

---

## 🧠 Algorithms Explained

### A* vs Dijkstra
- **Dijkstra**: Guaranteed optimal, but explores blindly in all directions.
- **A***: Uses $f(n) = g(n) + w \cdot h(n)$ to "aim" at the target, reducing search space by up to 70%.
- **Heuristic**: Haversine distance (Great-circle distance) - Admissible and Consistent.

### Traffic Simulation
Traffic is simulated by modifying edge weights based on road type:
- `Motorway`: 3.0x multiplier during peak.
- `Primary`: 2.5x multiplier.
- `Residential`: 1.2x multiplier.

---

## 📁 Project Structure

```
SmartRouteAI/
├── main.py                  # CLI Engine entry point
├── smartroute/              # Core Logic Package
│   ├── algorithms.py        # Search implementations (Dijkstra/A*)
│   ├── optimizer.py         # TSP solvers (2-opt)
│   ├── visualizer.py        # Folium & Chart generation
│   └── ...
├── web-dashboard/           # Next.js Frontend
│   └── src/app/page.tsx     # Mission Control Dashboard
├── output/                  # Generated results.json & maps
└── cache/                   # OSMnx Graph cache
```

---

## 📄 License
Education Project — SEM 6 AI Systems Lab.
