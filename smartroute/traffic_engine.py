import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import os

class TrafficPredictor:
    """ML-based Traffic Delay Prediction (Portfolio Edition)."""
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=50, random_state=42)
        self.is_trained = False

    def train_synthetic(self):
        """Creates a training set based on road types and peak-hour logic."""
        data = []
        road_types = {'motorway': 0, 'primary': 1, 'secondary': 2, 'residential': 3}
        
        for _ in range(1000):
            hr = np.random.randint(0, 24)
            rt = np.random.randint(0, 4)
            length = np.random.uniform(50, 500)
            
            # Logic: 8am-10am and 5pm-7pm are high traffic on major roads
            multiplier = 1.0
            if hr in [8, 9, 17, 18] and rt <= 1:
                multiplier = np.random.uniform(2.0, 4.0)
            elif rt == 3:
                multiplier = np.random.uniform(1.1, 1.4)
                
            delay = (length / 10.0) * multiplier
            data.append([hr, rt, length, delay])

        df = pd.DataFrame(data, columns=['hour', 'road_type', 'length', 'delay'])
        self.model.fit(df[['hour', 'road_type', 'length']], df['delay'])
        self.is_trained = True

    def predict_batch(self, edge_features_list):
        """High-speed vectorized prediction for the entire graph at once."""
        if not self.is_trained:
            self.train_synthetic()
        
        if not edge_features_list:
            return []

        # Convert the entire list of (hour, road_type_str, length) to a DF
        rt_map = {'motorway': 0, 'primary': 1, 'secondary': 2, 'residential': 3}
        processed_features = []
        for hr, rt_str, length in edge_features_list:
            rt_val = rt_map.get(rt_str.lower() if isinstance(rt_str, str) else 'residential', 2)
            processed_features.append([hr, rt_val, length])

        features_df = pd.DataFrame(processed_features, columns=['hour', 'road_type', 'length'])
        
        # Run one single prediction for all edges!
        return self.model.predict(features_df).tolist()
