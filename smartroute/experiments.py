import pandas as pd
import time
import os
from smartroute.config import OUTPUT_DIR

class RouteExperiment:
    """Automated benchmarking module for AI Performance Reports."""
    def __init__(self):
        self.results = []

    def log_trial(self, algo_name, traffic_condition, time_s, nodes, cost):
        self.results.append({
            "algorithm": algo_name,
            "traffic": traffic_condition,
            "exec_time_s": time_s,
            "nodes_explored": nodes,
            "total_cost": cost,
            "timestamp": time.ctime()
        })

    def save_to_csv(self, filename="experiment_report.csv"):
        df = pd.DataFrame(self.results)
        path = os.path.join(OUTPUT_DIR, filename)
        df.to_csv(path, index=False)
        return path

    def generate_summary(self):
        """Builds a resume-ready analysis table."""
        df = pd.DataFrame(self.results)
        if df.empty: return "No experiments run."
        
        return df.groupby(["algorithm", "traffic"]).agg({
            "exec_time_s": "mean",
            "nodes_explored": "mean",
            "total_cost": "mean"
        }).to_dict()
