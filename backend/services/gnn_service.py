"""
GNN Service — Dynamic graph built from real patient location data.
Replaces hardcoded 6 Delhi pincodes with actual cities/pincodes from PostgreSQL.
Uses graph diffusion for short-term spread simulation.
(Phase 2 will upgrade this to a real PyTorch Geometric ST-GNN.)
"""
from collections import defaultdict
from datetime import datetime, timedelta
import math

import networkx as nx
from models import SessionLocal, Patient, MedicalRecord


# ─── Haversine distance (km) between two lat/lon points ──────────────────────
# We store approximate city centroids for Indian cities using a lookup table.
# In Phase 2, replace with real lat/lon from geocoded patient addresses.

# Major Indian city centroids (lat, lon)
_CITY_COORDS: dict[str, tuple[float, float]] = {
    "delhi":         (28.6139, 77.2090),
    "new delhi":     (28.6139, 77.2090),
    "mumbai":        (19.0760, 72.8777),
    "bangalore":     (12.9716, 77.5946),
    "bengaluru":     (12.9716, 77.5946),
    "chennai":       (13.0827, 80.2707),
    "kolkata":       (22.5726, 88.3639),
    "hyderabad":     (17.3850, 78.4867),
    "pune":          (18.5204, 73.8567),
    "ahmedabad":     (23.0225, 72.5714),
    "surat":         (21.1702, 72.8311),
    "jaipur":        (26.9124, 75.7873),
    "lucknow":       (26.8467, 80.9462),
    "kanpur":        (26.4499, 80.3319),
    "nagpur":        (21.1458, 79.0882),
    "indore":        (22.7196, 75.8577),
    "bhopal":        (23.2599, 77.4126),
    "visakhapatnam": (17.6868, 83.2185),
    "patna":         (25.5941, 85.1376),
    "vadodara":      (22.3072, 73.1812),
    "ghaziabad":     (28.6692, 77.4538),
    "ludhiana":      (30.9009, 75.8573),
    "agra":          (27.1767, 78.0081),
    "nashik":        (20.0059, 73.7910),
    "faridabad":     (28.4089, 77.3178),
    "meerut":        (28.9845, 77.7064),
    "coimbatore":    (11.0168, 76.9558),
    "ranchi":        (23.3441, 85.3096),
    "amritsar":      (31.6340, 74.8723),
    "varanasi":      (25.3176, 82.9739),
}

_ADJACENCY_THRESHOLD_KM = 300


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def _build_dynamic_graph(location_case_loads: dict[str, int]) -> nx.Graph:
    """
    Build a weighted graph where:
      - Nodes = cities present in real patient data
      - Edges = geographic proximity (< ADJACENCY_THRESHOLD_KM km)
      - Edge weight ∝ proximity (closer = higher weight)
    """
    G = nx.Graph()
    locations = list(location_case_loads.keys())

    if not locations:
        return G

    G.add_nodes_from(locations, case_load=0)
    for loc, load in location_case_loads.items():
        if G.has_node(loc):
            G.nodes[loc]["case_load"] = load

    # Add edges for nearby cities
    for i, loc_a in enumerate(locations):
        coord_a = _CITY_COORDS.get(loc_a.lower())
        if not coord_a:
            continue
        for loc_b in locations[i + 1 :]:
            coord_b = _CITY_COORDS.get(loc_b.lower())
            if not coord_b:
                continue
            dist_km = _haversine(*coord_a, *coord_b)
            if dist_km <= _ADJACENCY_THRESHOLD_KM:
                # Weight: closer ↔ higher weight (max 1.0 at 0 km)
                weight = round(1 - (dist_km / _ADJACENCY_THRESHOLD_KM), 3)
                G.add_edge(loc_a, loc_b, weight=weight, distance_km=round(dist_km, 1))

    return G


class GNNService:
    """
    Disease spread prediction using dynamic graph diffusion on real DB data.
    Phase 1: Graph diffusion (current)
    Phase 2: PyTorch Geometric ST-GNN after 6+ months of live data
    """

    def __init__(self):
        self.transmission_rate = 0.25   # Simplified R0 proxy; can be tuned per disease

    def _get_current_case_loads(self, disease: str = None, days: int = 90) -> dict[str, int]:
        """Query city-level case counts from medical_records for recent N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        with SessionLocal() as db:
            query = (
                db.query(Patient.city, MedicalRecord.diagnosis)
                .join(MedicalRecord, MedicalRecord.patient_id == Patient.id)
                .filter(
                    MedicalRecord.visit_date >= cutoff,
                    Patient.city != None,
                    Patient.city != "",
                    MedicalRecord.diagnosis != None,
                )
            )
            if disease:
                query = query.filter(MedicalRecord.diagnosis.ilike(f"%{disease}%"))
            rows = query.all()

        counts: dict[str, int] = defaultdict(int)
        for city, _ in rows:
            if city:
                counts[city.strip().lower()] += 1
        return dict(counts)

    def predict_spread(self, current_hotspots: list, disease: str = None) -> list:
        """
        Predict disease spread over 7 days using real city-level data.

        Args:
            current_hotspots: Optional override — list of dicts with 'city'/'count'.
                              If empty, loads from DB automatically.
            disease: Optional disease filter for DB query.

        Returns:
            List of predicted hotspot dicts per day.
        """
        # ── 1. Get current case loads ─────────────────────────────────────────
        if current_hotspots:
            # Accept legacy pincode format or new city format
            db_loads = {}
            for h in current_hotspots:
                city = h.get("city") or h.get("pincode") or "unknown"
                db_loads[city.strip().lower()] = float(h.get("count", 0))
        else:
            db_loads = self._get_current_case_loads(disease=disease)

        if not db_loads:
            return []

        # ── 2. Build dynamic graph from real city data ────────────────────────
        graph = _build_dynamic_graph(db_loads)

        if graph.number_of_nodes() == 0:
            return []

        # ── 3. Diffusion simulation (7 days forward) ──────────────────────────
        current_load = {
            node: float(db_loads.get(node, 0))
            for node in graph.nodes()
        }

        predictions = []
        temp_load = current_load.copy()

        for day in range(1, 8):
            next_load = temp_load.copy()

            for node in graph.nodes():
                incoming = 0.0
                for neighbor in graph.neighbors(node):
                    w = graph[node][neighbor]["weight"]
                    incoming += temp_load[neighbor] * w * self.transmission_rate

                # Decay existing + add incoming
                next_load[node] = (temp_load[node] * 0.88) + incoming

            temp_load = next_load

            # Collect hotspots above threshold
            for node, load in temp_load.items():
                if load >= 2:
                    coords = _CITY_COORDS.get(node)
                    predictions.append({
                        "city":            node.title(),
                        "predicted_cases": round(load, 1),
                        "risk_level":      (
                            "Critical" if load > 30
                            else "High" if load > 15
                            else "Moderate" if load > 5
                            else "Low"
                        ),
                        "day_offset":      day,
                        "lat":             coords[0] if coords else None,
                        "lon":             coords[1] if coords else None,
                    })

        return predictions

    def get_spread_graph_summary(self, disease: str = None) -> dict:
        """Return graph statistics for the dashboard — node count, edge count, top hubs."""
        loads = self._get_current_case_loads(disease=disease)
        graph = _build_dynamic_graph(loads)

        if graph.number_of_nodes() == 0:
            return {"nodes": 0, "edges": 0, "top_hubs": []}

        degree_centrality = nx.degree_centrality(graph)
        top_hubs = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "nodes":    graph.number_of_nodes(),
            "edges":    graph.number_of_edges(),
            "top_hubs": [
                {
                    "city": city.title(),
                    "connectivity": round(score, 3),
                    "current_cases": loads.get(city, 0),
                }
                for city, score in top_hubs
            ],
        }


# ─── Singleton ────────────────────────────────────────────────────────────────
gnn_service = GNNService()
