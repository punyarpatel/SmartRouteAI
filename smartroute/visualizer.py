"""
visualizer.py — Route Visualization (Folium + Matplotlib)

Generates two types of visualizations:
1. Interactive HTML maps using Folium (openable in any browser)
2. Static comparison charts using Matplotlib

All output files are saved to the 'output/' directory.
"""

import os

import folium
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from smartroute.config import COLORS, MAP_TILES, OUTPUT_DIR


# ══════════════════════════════════════════════════════════════
# SECTION 1: INTERACTIVE MAPS (Folium)
# ══════════════════════════════════════════════════════════════

def plot_route_interactive(G, route_astar, route_dijkstra=None,
                           source_node=None, target_node=None,
                           source_name=None, target_name=None,
                           metrics=None, filename="route_map.html"):
    """
    Create an interactive HTML map showing the computed route(s).

    Displays the A* route (and optionally Dijkstra route) overlaid
    on an OpenStreetMap base map. Click markers for info.

    Args:
        G               (nx.MultiDiGraph): Road network graph
        route_astar     (list[int]): A* path (list of node IDs)
        route_dijkstra  (list[int]): Optional Dijkstra path for comparison
        source_node     (int): Start node ID (for marker)
        target_node     (int): End node ID (for marker)
        filename        (str): Output filename

    Returns:
        str: Path to saved HTML file
    """
    print(f"\n🗺️  Generating interactive route map...")

    # ── Create base map centered on the route ───────────────
    route_coords = _nodes_to_coords(G, route_astar)
    center_lat = np.mean([c[0] for c in route_coords])
    center_lon = np.mean([c[1] for c in route_coords])

    m = folium.Map(location=[center_lat, center_lon],
                   zoom_start=14, tiles=MAP_TILES)

    # ── Plot Dijkstra route (if provided, drawn first = behind) ──
    if route_dijkstra:
        dijkstra_coords = _nodes_to_coords(G, route_dijkstra)
        folium.PolyLine(
            locations=dijkstra_coords,
            color=COLORS["route_dijkstra"],
            weight=10,
            opacity=0.8,
            dash_array="10 10",
            tooltip="Dijkstra Path",
        ).add_to(m)

    # ── Plot A* route ───────────────────────────────────────
    folium.PolyLine(
        locations=route_coords,
        color=COLORS["route_astar"],
        weight=4,
        opacity=1.0,
        tooltip="A* Path",
    ).add_to(m)

    # ── Add start/end markers ───────────────────────────────
    if source_node:
        s_lat, s_lon = G.nodes[source_node]["y"], G.nodes[source_node]["x"]
        s_text = source_name if source_name else "Start Point"
        folium.Marker(
            location=[s_lat, s_lon],
            popup=f"<b>{s_text}</b><br>Start Node",
            tooltip=s_text,
            icon=folium.Icon(color="green", icon="play", prefix="fa"),
        ).add_to(m)

    if target_node:
        t_lat, t_lon = G.nodes[target_node]["y"], G.nodes[target_node]["x"]
        t_text = target_name if target_name else "Destination"
        folium.Marker(
            location=[t_lat, t_lon],
            popup=f"<b>{t_text}</b><br>Destination Node",
            tooltip=t_text,
            icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa"),
        ).add_to(m)

    legend_html = _build_legend({
        "A* Route": COLORS["route_astar"],
        **({"Dijkstra Route": COLORS["route_dijkstra"]} if route_dijkstra else {}),
    })
    m.get_root().html.add_child(folium.Element(legend_html))
    
    if metrics:
        panel_html = _build_metrics_panel(metrics, type="single")
        m.get_root().html.add_child(folium.Element(panel_html))

    # ── Auto-zoom to fit route ──────────────────────────────
    m.fit_bounds([[min(c[0] for c in route_coords), min(c[1] for c in route_coords)],
                  [max(c[0] for c in route_coords), max(c[1] for c in route_coords)]])

    # ── Save ────────────────────────────────────────────────
    filepath = os.path.join(OUTPUT_DIR, filename)
    m.save(filepath)
    print(f"   ✅ Saved: {filepath}")
    return filepath


def plot_multi_stop_route(G, segment_paths, stop_nodes, stop_names=None,
                          metrics=None, filename="delivery_map.html"):
    """
    Create an interactive map showing the multi-stop delivery route.

    Each segment between consecutive stops is drawn in a different
    color. Numbered markers show the delivery order.

    Args:
        G              (nx.MultiDiGraph): Road network graph
        segment_paths  (list[list[int]]): Path for each segment
        stop_nodes     (list[int]): Node IDs in visit order
        stop_names     (list[str]): Optional names for each stop
        filename       (str): Output filename

    Returns:
        str: Path to saved HTML file
    """
    print(f"\n🗺️  Generating multi-stop delivery map...")

    # ── Collect all coordinates for centering ───────────────
    all_coords = []
    for seg in segment_paths:
        all_coords.extend(_nodes_to_coords(G, seg))

    center_lat = np.mean([c[0] for c in all_coords])
    center_lon = np.mean([c[1] for c in all_coords])

    m = folium.Map(location=[center_lat, center_lon],
                   zoom_start=13, tiles=MAP_TILES)

    segment_colors = COLORS["route_segments"]

    # ── Draw each route segment ─────────────────────────────
    for i, seg_path in enumerate(segment_paths):
        coords = _nodes_to_coords(G, seg_path)
        color = segment_colors[i % len(segment_colors)]

        folium.PolyLine(
            locations=coords,
            color=color,
            weight=5,
            opacity=0.8,
            tooltip=f"Segment {i + 1}",
        ).add_to(m)

    # Add numbered stop markers
    seen_coords = set()
    for i, node in enumerate(stop_nodes):
        lat, lon = G.nodes[node]["y"], G.nodes[node]["x"]
        
        # Jitter coordinates slightly if multiple stops map to the exact same intersection
        # (e.g. Warehouse and a nearby stop snapping to the same street corner)
        while (lat, lon) in seen_coords:
            lat += 0.0003  # Offset roughly 30 meters
            lon += 0.0003
        seen_coords.add((lat, lon))

        name = stop_names[i] if stop_names and i < len(stop_names) else f"Stop {i}"

        if i == 0:
            # Warehouse marker
            folium.Marker(
                location=[lat, lon],
                popup=f"<b>{name}</b><br>📍 Warehouse / Depot",
                tooltip=name,
                icon=folium.Icon(color="red", icon="warehouse",
                                 prefix="fa"),
            ).add_to(m)
        else:
            # Delivery stop marker with number
            folium.Marker(
                location=[lat, lon],
                popup=f"<b>{name}</b><br>📦 Delivery #{i}",
                tooltip=f"#{i}: {name}",
                icon=folium.Icon(color="blue", icon="box",
                                 prefix="fa"),
            ).add_to(m)

            # Add a numbered circle for clear ordering
            folium.CircleMarker(
                location=[lat, lon],
                radius=12,
                color="white",
                fill=True,
                fill_color="#3498DB",
                fill_opacity=0.9,
                popup=f"Stop #{i}",
            ).add_to(m)

    # ── Auto-zoom ───────────────────────────────────────────
    m.fit_bounds([[min(c[0] for c in all_coords), min(c[1] for c in all_coords)],
                  [max(c[0] for c in all_coords), max(c[1] for c in all_coords)]])

    if metrics:
        panel_html = _build_metrics_panel(metrics, type="multi")
        m.get_root().html.add_child(folium.Element(panel_html))

    filepath = os.path.join(OUTPUT_DIR, filename)
    m.save(filepath)
    print(f"   ✅ Saved: {filepath}")
    return filepath


# ══════════════════════════════════════════════════════════════
# SECTION 2: STATIC CHARTS (Matplotlib)
# ══════════════════════════════════════════════════════════════

def plot_algorithm_comparison(comparison, filename="comparison.png"):
    """
    Create a bar chart comparing Dijkstra vs A* performance metrics.

    Shows three side-by-side comparisons:
    1. Execution Time (seconds)
    2. Nodes Explored (count)
    3. Path Cost (travel time or distance)

    Args:
        comparison (dict): Output from algorithms.compare_algorithms()
        filename   (str): Output filename

    Returns:
        str: Path to saved image
    """
    print(f"\n📊 Generating algorithm comparison chart...")

    d_metrics = comparison["dijkstra"][2]
    a_metrics = comparison["astar"][2]

    # ── Prepare data ────────────────────────────────────────
    categories = ["Execution Time\n(seconds)", "Nodes Explored",
                  "Path Cost"]
    dijkstra_vals = [d_metrics["execution_time"],
                     d_metrics["nodes_explored"],
                     d_metrics["path_cost"]]
    astar_vals = [a_metrics["execution_time"],
                  a_metrics["nodes_explored"],
                  a_metrics["path_cost"]]

    # ── Create figure ───────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    fig.suptitle("Algorithm Comparison: Dijkstra vs A*",
                 fontsize=18, fontweight="bold", y=1.02)

    bar_width = 0.35
    colors_d = "#E67E22"  # Orange for Dijkstra
    colors_a = "#2ECC71"  # Green for A*

    for idx, (ax, cat) in enumerate(zip(axes, categories)):
        vals = [dijkstra_vals[idx], astar_vals[idx]]
        bars = ax.bar(["Dijkstra", "A*"], vals,
                      color=[colors_d, colors_a],
                      width=0.5, edgecolor="white", linewidth=1.5)

        # Add value labels on bars
        for bar, val in zip(bars, vals):
            if val >= 1000:
                label = f"{val:,.0f}"
            elif val >= 1:
                label = f"{val:.2f}"
            else:
                label = f"{val:.6f}"

            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    label, ha="center", va="bottom", fontsize=11,
                    fontweight="bold")

        ax.set_title(cat, fontsize=13, pad=10)
        ax.set_ylabel("")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Add grid
        ax.yaxis.grid(True, alpha=0.3)
        ax.set_axisbelow(True)

    # ── Add reduction labels ────────────────────────────────
    fig.text(0.5, -0.02,
             f"A* explored {comparison['node_reduction_pct']:.1f}% fewer nodes | "
             f"A* was {comparison['time_reduction_pct']:.1f}% faster",
             ha="center", fontsize=13, style="italic",
             color="#7F8C8D")

    plt.tight_layout()

    filepath = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(filepath, dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"   ✅ Saved: {filepath}")
    return filepath


def plot_traffic_comparison(comparison_no_traffic, comparison_with_traffic,
                            filename="traffic_comparison.png"):
    """
    Create a chart comparing route metrics with and without traffic.

    Args:
        comparison_no_traffic   (dict): Comparison results without traffic
        comparison_with_traffic (dict): Comparison results with traffic
        filename (str): Output filename

    Returns:
        str: Path to saved image
    """
    print(f"\n📊 Generating traffic impact chart...")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Impact of Traffic on Route Performance",
                 fontsize=18, fontweight="bold", y=1.02)

    # ── Chart 1: Path Cost Comparison ───────────────────────
    ax = axes[0]
    conditions = ["No Traffic", "Peak Traffic"]

    d_costs = [comparison_no_traffic["dijkstra"][2]["path_cost"],
               comparison_with_traffic["dijkstra"][2]["path_cost"]]
    a_costs = [comparison_no_traffic["astar"][2]["path_cost"],
               comparison_with_traffic["astar"][2]["path_cost"]]

    x = np.arange(len(conditions))
    width = 0.3

    bars1 = ax.bar(x - width/2, d_costs, width, color="#E67E22",
                   label="Dijkstra", edgecolor="white")
    bars2 = ax.bar(x + width/2, a_costs, width, color="#2ECC71",
                   label="A*", edgecolor="white")

    ax.set_title("Path Cost", fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels(conditions)
    ax.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, alpha=0.3)
    ax.set_axisbelow(True)

    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"{bar.get_height():.1f}", ha="center", va="bottom",
                    fontsize=10, fontweight="bold")

    # ── Chart 2: Nodes Explored ─────────────────────────────
    ax = axes[1]
    d_nodes = [comparison_no_traffic["dijkstra"][2]["nodes_explored"],
               comparison_with_traffic["dijkstra"][2]["nodes_explored"]]
    a_nodes = [comparison_no_traffic["astar"][2]["nodes_explored"],
               comparison_with_traffic["astar"][2]["nodes_explored"]]

    bars1 = ax.bar(x - width/2, d_nodes, width, color="#E67E22",
                   label="Dijkstra", edgecolor="white")
    bars2 = ax.bar(x + width/2, a_nodes, width, color="#2ECC71",
                   label="A*", edgecolor="white")

    ax.set_title("Nodes Explored", fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels(conditions)
    ax.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, alpha=0.3)
    ax.set_axisbelow(True)

    for bars in [bars1, bars2]:
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"{int(bar.get_height()):,}", ha="center", va="bottom",
                    fontsize=10, fontweight="bold")

    plt.tight_layout()
    filepath = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(filepath, dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"   ✅ Saved: {filepath}")
    return filepath


def plot_delivery_summary(optimization_result, stop_names=None,
                          filename="delivery_summary.png"):
    """
    Create a summary chart for the multi-stop delivery optimization.

    Shows:
    1. Segment costs (bar chart)
    2. Greedy vs Optimized total cost

    Args:
        optimization_result (dict): Output from optimizer.optimize_delivery_route()
        stop_names          (list): Names for each stop
        filename            (str): Output filename

    Returns:
        str: Path to saved image
    """
    print(f"\n📊 Generating delivery summary chart...")

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle("Multi-Stop Delivery Optimization Results",
                 fontsize=18, fontweight="bold", y=1.02)

    segment_costs = optimization_result["segment_costs"]
    opt_order = optimization_result["optimized_order"]

    # ── Chart 1: Segment Costs ──────────────────────────────
    ax = axes[0]
    segment_labels = []
    for i in range(len(opt_order) - 1):
        src = opt_order[i]
        dst = opt_order[i + 1]

        if stop_names:
            src_name = stop_names[src] if src < len(stop_names) else f"Stop {src}"
            dst_name = stop_names[dst] if dst < len(stop_names) else f"Stop {dst}"
            # Shorten names
            src_short = src_name.split("—")[-1].strip()[:15] if "—" in src_name else src_name[:15]
            dst_short = dst_name.split("—")[-1].strip()[:15] if "—" in dst_name else dst_name[:15]
            segment_labels.append(f"{src_short}\n→ {dst_short}")
        else:
            segment_labels.append(f"Stop {src}\n→ Stop {dst}")

    colors = [COLORS["route_segments"][i % len(COLORS["route_segments"])]
              for i in range(len(segment_costs))]

    bars = ax.barh(range(len(segment_costs)), segment_costs,
                   color=colors, edgecolor="white", linewidth=1)

    ax.set_yticks(range(len(segment_labels)))
    ax.set_yticklabels(segment_labels, fontsize=9)
    ax.set_xlabel("Travel Cost")
    ax.set_title("Cost per Segment", fontsize=13)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.xaxis.grid(True, alpha=0.3)
    ax.set_axisbelow(True)

    for bar in bars:
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2,
                f" {bar.get_width():.1f}", va="center", fontsize=10)

    # ── Chart 2: Greedy vs Optimized ────────────────────────
    ax = axes[1]
    greedy = optimization_result["greedy_cost"]
    optimized = optimization_result["optimized_cost"]

    bars = ax.bar(["Greedy\nNearest Neighbor", "2-opt\nOptimized"],
                  [greedy, optimized],
                  color=["#E74C3C", "#2ECC71"],
                  width=0.5, edgecolor="white", linewidth=2)

    for bar, val in zip(bars, [greedy, optimized]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                f"{val:.1f}", ha="center", va="bottom",
                fontsize=13, fontweight="bold")

    improvement = greedy - optimized
    if improvement > 0:
        ax.text(0.5, 0.5,
                f"↓ {improvement:.1f} saved\n({improvement/max(greedy,1e-9)*100:.1f}%)",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=14, color="#27AE60", fontstyle="italic",
                fontweight="bold")

    ax.set_title("Route Optimization", fontsize=13)
    ax.set_ylabel("Total Travel Cost")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, alpha=0.3)
    ax.set_axisbelow(True)

    plt.tight_layout()
    filepath = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(filepath, dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"   ✅ Saved: {filepath}")
    return filepath


# ══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════

def _nodes_to_coords(G, node_list):
    """
    Convert a list of node IDs to (lat, lon) coordinate tuples.

    Args:
        G         (nx.MultiDiGraph): Road network graph
        node_list (list[int]): List of node IDs

    Returns:
        list[tuple]: List of (latitude, longitude) tuples
    """
    return [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in node_list]


def _build_legend(items):
    """
    Build an HTML legend overlay for a Folium map.

    Args:
        items (dict): Mapping of label → color

    Returns:
        str: HTML string for the legend
    """
    legend_items = ""
    for label, color in items.items():
        legend_items += (
            f'<li><span style="background:{color};width:20px;height:4px;'
            f'display:inline-block;margin-right:8px;vertical-align:middle;'
            f'border-radius:2px;"></span>{label}</li>'
        )

    return f'''
    <div style="
        position: fixed;
        bottom: 30px;
        left: 30px;
        z-index: 1000;
        background: white;
        padding: 12px 16px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 13px;
    ">
        <b style="font-size:14px;">Legend</b>
        <ul style="list-style:none;padding:4px 0 0 0;margin:0;">
            {legend_items}
        </ul>
    </div>
    '''

def _build_metrics_panel(metrics, type="single"):
    if not metrics:
        return ""
    
    html_content = ""
    if type == "single":
        d_metrics = metrics["dijkstra"][2]
        a_metrics = metrics["astar"][2]
        
        # Determine the winner
        time_diff = abs(a_metrics['execution_time'] - d_metrics['execution_time'])
        if a_metrics['execution_time'] < d_metrics['execution_time']:
            winner_text = f"🏆 A* was faster by {time_diff:.5f} s!"
            winner_color = "#2ECC71"
        else:
            winner_text = f"🏆 Dijkstra was faster by {time_diff:.5f} s!"
            winner_color = "#E67E22"
            
        html_content = f"""
        <b style="font-size:15px; color:#2C3E50; border-bottom:1px solid #eee; display:block; padding-bottom:8px; margin-bottom:8px;">Algorithm Performance</b>
        
        <div style="margin-bottom:8px;">
            <span style="color:#2C3E50; font-weight:bold;">A* Search</span>
            <div style="display:flex; justify-content:space-between; margin-left:10px; margin-top:2px;">
                <span style="color:#7F8C8D;">Explored:</span> <span style="color:#2ECC71; font-weight:bold;">{a_metrics['nodes_explored']:,} nodes</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-left:10px; margin-top:2px;">
                <span style="color:#7F8C8D;">Execution:</span> <span style="color:#2C3E50;">{a_metrics['execution_time']:.5f} s</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-left:10px; margin-top:2px;">
                <span style="color:#7F8C8D;">Path Cost:</span> <span style="color:#2C3E50;">{a_metrics['path_cost']:.2f}</span>
            </div>
        </div>
        
        <div style="margin-bottom:8px;">
            <span style="color:#2C3E50; font-weight:bold;">Dijkstra Algorithm</span>
            <div style="display:flex; justify-content:space-between; margin-left:10px; margin-top:2px;">
                <span style="color:#7F8C8D;">Explored:</span> <span style="color:#E67E22; font-weight:bold;">{d_metrics['nodes_explored']:,} nodes</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-left:10px; margin-top:2px;">
                <span style="color:#7F8C8D;">Execution:</span> <span style="color:#2C3E50;">{d_metrics['execution_time']:.5f} s</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-left:10px; margin-top:2px;">
                <span style="color:#7F8C8D;">Path Cost:</span> <span style="color:#2C3E50;">{d_metrics['path_cost']:.2f}</span>
            </div>
        </div>

        <div style="margin-top:10px; border-top:1px solid #eee; padding-top:8px; text-align:center;">
            <span style="font-weight:bold; color:{winner_color}; font-size:14px;">{winner_text}</span>
            <span style="display:block; font-size:11px; color:#95a5a6; margin-top:2px;">(A* explored {metrics['node_reduction_pct']:.1f}% fewer nodes)</span>
        </div>
        """
    elif type == "multi":
        greedy = metrics["greedy_cost"]
        opt = metrics["optimized_cost"]
        improvement = greedy - opt
        pct = (improvement / max(greedy, 1e-9)) * 100
        
        if opt < greedy:
            winner_text = "🏆 2-opt search found a better route!"
            winner_color = "#2ECC71"
        else:
            winner_text = "🏆 Greedy route was already optimal!"
            winner_color = "#3498DB"
            
        html_content = f"""
        <b style="font-size:15px; color:#2C3E50; border-bottom:1px solid #eee; display:block; padding-bottom:8px; margin-bottom:8px;">Multi-Stop Optimization</b>
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
            <span style="color:#7F8C8D;">Greedy Nearest:</span> 
            <span style="font-weight:bold; color:#E74C3C;">{greedy:.1f} sec ({greedy/60:.1f} min)</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
            <span style="color:#7F8C8D;">2-opt Search:</span> 
            <span style="font-weight:bold; color:#2ECC71;">{opt:.1f} sec ({opt/60:.1f} min)</span>
        </div>
        
        <div style="margin-top:10px; border-top:1px solid #eee; padding-top:8px; text-align:center;">
            <span style="font-weight:bold; color:{winner_color}; font-size:13px;">{winner_text}</span>
        </div>
        <div style="display:flex; justify-content:center; margin-top:4px;">
            <span style="color:#7F8C8D; font-size:12px;">Saved: {improvement:.1f} sec ({improvement/60:.2f} min) ({pct:.1f}%)</span>
        </div>
        """

    return f'''
    <div style="
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        background: white;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 13px;
        width: 250px;
    ">
        {html_content}
    </div>
    '''
