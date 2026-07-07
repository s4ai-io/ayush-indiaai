"""
spatial_service.py
──────────────────
DBSCAN-based geospatial clustering of disease burden across Indian cities.

Because the patients table stores city names rather than raw lat/lon coordinates,
we use pre-computed city centroids (same lookup table as the GNN service) as the
spatial positions of each data point.

Each (city, disease) pair is treated as a weighted point:
  - Position  = city centroid lat/lon
  - Weight    = case count for that disease in that city

DBSCAN parameters
  ε (eps)        = 400 km  — cities within 400 km form a neighbourhood
  min_samples    = 2        — at least 2 cities needed to form a cluster

Output
  List of clusters, each containing:
    cluster_id, disease, cities, total_cases, centroid_lat, centroid_lon, radius_km
  Points classified as noise (label = -1) are returned as singleton "hotspot" entries.
"""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timedelta
from itertools import combinations

from models import SessionLocal, MedicalRecord, Patient
from services.gnn_service import _CITY_COORDS, _haversine
from utils.episode_dedup import dedupe_repeat_diagnoses


# ─── Pure-Python DBSCAN ───────────────────────────────────────────────────────

def _dbscan(
    points: list[tuple[float, float]],       # [(lat, lon), ...]
    eps_km: float,
    min_samples: int,
) -> list[int]:
    """
    Pure-Python DBSCAN.  Returns a label list parallel to `points`.
    Labels: -1 = noise, 0, 1, 2, … = cluster ids.
    """
    n      = len(points)
    labels = [-1] * n
    visited = [False] * n
    cluster_id = 0

    def neighbours(idx: int) -> list[int]:
        lat1, lon1 = points[idx]
        return [
            j for j in range(n)
            if _haversine(lat1, lon1, *points[j]) <= eps_km
        ]

    for i in range(n):
        if visited[i]:
            continue
        visited[i] = True
        nbrs = neighbours(i)

        if len(nbrs) < min_samples:
            labels[i] = -1  # noise for now, may be absorbed later
            continue

        labels[i] = cluster_id
        seed_set = set(nbrs) - {i}

        while seed_set:
            j = seed_set.pop()
            if not visited[j]:
                visited[j] = True
                j_nbrs = neighbours(j)
                if len(j_nbrs) >= min_samples:
                    seed_set |= set(j_nbrs)
            if labels[j] == -1:
                labels[j] = cluster_id

        cluster_id += 1

    return labels


def _diameter(members: list[int], coords: list[tuple[float, float]]) -> float:
    """Max pairwise distance between any two of the given point indices."""
    if len(members) < 2:
        return 0.0
    return max(
        _haversine(*coords[a], *coords[b])
        for a, b in combinations(members, 2)
    )


def _split_chained_cluster(
    indices: list[int],
    coords: list[tuple[float, float]],
    cap_km: float,
) -> list[list[int]]:
    """
    DBSCAN groups points by density-*reachability*, which chains through
    intermediates: A-B and B-C within eps each puts A, B and C in one
    cluster even if A and C are nowhere near each other (e.g. Kolkata →
    Ranchi → ... → Chandigarh ends up "one cluster" spanning 1400+ km,
    even though eps=400km). That contradicts the product's stated
    definition of a cluster ("cities within `cap_km` of each other").

    Re-splits a DBSCAN cluster via complete-linkage agglomeration bounded
    by `cap_km`, so every final group only ever merges when *all* existing
    members stay within cap_km of the new point — no more chaining.
    """
    groups = [[i] for i in indices]

    while True:
        best = None  # (diameter, i, j)
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                d = _diameter(groups[i] + groups[j], coords)
                if d <= cap_km and (best is None or d < best[0]):
                    best = (d, i, j)
        if best is None:
            break
        _, i, j = best
        groups[i] = groups[i] + groups[j]
        del groups[j]

    return groups


# ─── Spatial Service ──────────────────────────────────────────────────────────

class SpatialService:
    """
    Provides DBSCAN-based geospatial disease clustering.
    """

    EPS_KM      = 400
    MIN_SAMPLES = 2

    def get_disease_clusters(
        self,
        days: int = 90,
        min_cases: int = 2,
    ) -> list[dict]:
        """
        Cluster cities by co-occurring disease burden within EPS_KM radius.

        Returns a list of cluster dicts sorted by total_cases descending.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        with SessionLocal() as db:
            rows = (
                db.query(Patient.id, Patient.city, MedicalRecord.diagnosis, MedicalRecord.visit_date)
                .join(MedicalRecord, MedicalRecord.patient_id == Patient.id)
                .filter(
                    MedicalRecord.visit_date >= cutoff,
                    MedicalRecord.diagnosis  != None,
                    MedicalRecord.diagnosis  != "",
                    Patient.city             != None,
                    Patient.city             != "",
                )
                .all()
            )

        # Collapse each patient's repeat visits for the same diagnosis (within
        # this window) into one case — a returning patient isn't 3 cases.
        rows = dedupe_repeat_diagnoses(rows, patient_idx=0, diagnosis_idx=2, date_idx=3, gap_days=None)

        # ── Aggregate: (city, disease) → count ───────────────────────────────
        counts: dict[tuple[str, str], int] = defaultdict(int)
        for _patient_id, city, diagnosis, _visit_date in rows:
            city      = city.strip().lower()
            diagnosis = diagnosis.strip()
            if city and diagnosis:
                counts[(city, diagnosis)] += 1

        if not counts:
            return []

        # ── Build per-disease point clouds ───────────────────────────────────
        disease_cities: dict[str, dict[str, int]] = defaultdict(dict)
        for (city, disease), cnt in counts.items():
            if cnt >= min_cases and city in _CITY_COORDS:
                disease_cities[disease][city] = cnt

        clusters: list[dict] = []

        for disease, city_counts in disease_cities.items():
            if len(city_counts) < 2:
                continue

            cities  = list(city_counts.keys())
            coords  = [_CITY_COORDS[c] for c in cities]
            weights = [city_counts[c] for c in cities]

            labels = _dbscan(coords, self.EPS_KM, self.MIN_SAMPLES)

            # ── Group labels into clusters, splitting any that chained past
            #    EPS_KM back down to genuinely-nearby groups ─────────────────
            raw_map: dict[int, list[int]] = defaultdict(list)
            for idx, lbl in enumerate(labels):
                if lbl != -1:
                    raw_map[lbl].append(idx)

            cluster_map: dict[int, list[int]] = {}
            noise_idx = -1
            next_id = 0
            for indices in raw_map.values():
                for group in _split_chained_cluster(indices, coords, self.EPS_KM):
                    if len(group) >= self.MIN_SAMPLES:
                        cluster_map[next_id] = group
                        next_id += 1
                    else:
                        cluster_map[noise_idx] = group
                        noise_idx -= 1

            for idx, lbl in enumerate(labels):
                if lbl == -1:
                    cluster_map[noise_idx] = [idx]
                    noise_idx -= 1

            for label, indices in cluster_map.items():
                is_noise = (label < 0)
                if is_noise and len(indices) == 1:
                    # Singleton noise only if it has enough cases to be notable
                    if weights[indices[0]] < 5:
                        continue

                cluster_cities = [cities[i] for i in indices]
                cluster_weights = [weights[i] for i in indices]
                total_cases = sum(cluster_weights)

                # Weighted centroid
                total_w = sum(cluster_weights)
                cent_lat = sum(_CITY_COORDS[c][0] * w for c, w in zip(cluster_cities, cluster_weights)) / total_w
                cent_lon = sum(_CITY_COORDS[c][1] * w for c, w in zip(cluster_cities, cluster_weights)) / total_w

                # Spread = maximum pairwise distance between any two cities in the cluster
                if len(cluster_cities) > 1:
                    spread_km = max(
                        _haversine(*_CITY_COORDS[c1], *_CITY_COORDS[c2])
                        for c1, c2 in combinations(cluster_cities, 2)
                    )
                else:
                    spread_km = 0

                clusters.append({
                    "cluster_id":   int(label),
                    "disease":      disease,
                    "is_noise":     is_noise,
                    # Full list, not top-N: total_cases/spread_km are computed
                    # over every member city, so truncating here would make
                    # "View Cases" silently miss cities that are part of the total.
                    "cities":       sorted(cluster_cities, key=lambda c: city_counts[c], reverse=True),
                    "city_cases":   {c: city_counts[c] for c in cluster_cities},
                    "total_cases":  total_cases,
                    "centroid_lat": round(cent_lat, 4),
                    "centroid_lon": round(cent_lon, 4),
                    "spread_km":    round(spread_km, 1),
                    "period_days":  days,
                })

        clusters.sort(key=lambda x: x["total_cases"], reverse=True)
        return clusters

    def get_cluster_summary(self, days: int = 90) -> dict:
        """High-level summary of clustering results."""
        clusters = self.get_disease_clusters(days=days)
        real_clusters = [c for c in clusters if not c["is_noise"]]
        hotspots      = [c for c in clusters if c["is_noise"]]

        return {
            "total_clusters":  len(real_clusters),
            "total_hotspots":  len(hotspots),
            "diseases_tracked": len({c["disease"] for c in clusters}),
            "clusters":         clusters[:20],   # cap for API response
            "eps_km":           self.EPS_KM,
            "min_samples":      self.MIN_SAMPLES,
            "period_days":      days,
        }


# ─── Singleton ────────────────────────────────────────────────────────────────
spatial_service = SpatialService()
