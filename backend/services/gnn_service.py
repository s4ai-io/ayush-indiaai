
import networkx as nx
import numpy as np
from datetime import datetime, timedelta

class GNNService:
    def __init__(self):
        self.graph = self._build_location_graph()
        self.transmission_rate = 0.3  # Simplified R0 factor proxy

    def _build_location_graph(self):
        """
        Builds a graph where Nodes are Pincodes/Areas and Edges are connectivity.
        In a real system, this would come from a database of geospatial adjacency.
        """
        G = nx.Graph()
        
        # Define some Delhi locations (Pincodes)
        # 110001: Connaught Place (Central)
        # 110002: Daryaganj (North)
        # 110003: Aliganj (Central)
        # 110004: Rashtrapati Bhawan (Central)
        # 110005: Karol Bagh (West)
        # 110006: Chandni Chowk (Old Delhi)
        
        locations = ["110001", "110002", "110003", "110004", "110005", "110006"]
        G.add_nodes_from(locations)
        
        # Add edges (Adjacency/Traffic flow)
        # Central is connected to everything
        G.add_edge("110001", "110002", weight=0.8) # High traffic
        G.add_edge("110001", "110003", weight=0.7)
        G.add_edge("110001", "110004", weight=0.6)
        G.add_edge("110001", "110005", weight=0.9) # Very high traffic
        
        # North-Old Delhi connection
        G.add_edge("110002", "110006", weight=0.8)
        
        # West-Central connection
        G.add_edge("110005", "110003", weight=0.5)
        
        return G

    def predict_spread(self, current_hotspots: list):
        """
        Simulate disease spread using Graph Diffusion.
        
        Args:
            current_hotspots: List of dicts [{'pincode': '110001', 'count': 10}, ...]
            
        Returns:
            List of predicted hotspots for next 7 days.
        """
        # Initialize state vector
        # Map pincode -> current load
        current_load = {node: 0.0 for node in self.graph.nodes()}
        
        for hotspot in current_hotspots:
            pincode = hotspot.get('pincode')
            if pincode in current_load:
                current_load[pincode] = float(hotspot.get('count', 0))
        
        predictions = []
        
        # Simulate 7 days forward
        # Simple diffusion: Next = Current + (Neighbors * Weight * Rate)
        
        temp_load = current_load.copy()
        
        for day in range(1, 8):
            next_load = temp_load.copy()
            
            for node in self.graph.nodes():
                incoming_infection = 0
                for neighbor in self.graph.neighbors(node):
                    weight = self.graph[node][neighbor]['weight']
                    neighbor_load = temp_load[neighbor]
                    
                    # Diffusion logic
                    incoming_infection += neighbor_load * weight * self.transmission_rate
                
                # Update node load (decay old cases slightly, add new infections)
                # decay = 0.9, new = incoming
                next_load[node] = (temp_load[node] * 0.9) + incoming_infection
            
            temp_load = next_load
            
            # Identify new hotspots in prediction
            daily_prediction = []
            for node, load in temp_load.items():
                if load > 5: # Threshold for "Spread"
                    # Calculate risk level
                    risk = "High" if load > 20 else "Moderate"
                    daily_prediction.append({
                        "pincode": node,
                        "predicted_cases": int(load),
                        "risk_level": risk,
                        "day_offset": day
                    })
            
            if daily_prediction:
                predictions.extend(daily_prediction)
                
        return predictions

# Singleton
gnn_service = GNNService()
