"""
geo_reference.py
─────────────────
Shared geography reference used by:
  - generate_historical_data_v2.py / seed_weekly_surge_data_v2.py (synthetic patient
    generation — which cities exist, their relative patient volume, and a plausible
    pincode for each patient's state)
  - gnn_service.py / spatial_service.py (city-centroid lookup for graph-diffusion
    spread simulation and DBSCAN geospatial clustering)

Replaces the old private ~30-entry `_CITY_COORDS` dict that used to live inside
gnn_service.py (and was silently reused by spatial_service.py) with a single shared,
much wider table, so patients outside a small hardcoded metro list are no longer
dropped from the geospatial panels.

Sources / methodology (approximations, not live data — documented so nobody mistakes
this for authoritative geocoding):
  - City list + relative population weights: broad city-size tiering (metro > tier-1
    > tier-2 > tier-3/4), roughly proportional to known relative urban-agglomeration
    sizes. Used only to get realistic *relative* proportions across ~130 cities
    spanning every state/UT, not to claim precise current population figures.
  - Lat/lon: approximate city centroids, accurate to roughly 0.1° (~10km) — more
    than sufficient for the 300-400km adjacency thresholds used by the spread/
    clustering services.
  - Pincode ranges: modeled on India Post's real postal-circle numbering (the first
    1-3 digits of a PIN identify a fixed circle/region per state) as inclusive
    6-digit ranges per state. Real PIN allocation has finer-grained exceptions this
    doesn't capture; this guarantees generated pincodes fall in the *correct state's*
    real range rather than being fully random 6-digit strings unrelated to the
    patient's city (the previous behavior).
"""
from __future__ import annotations

import random

# ─── (state, lat, lon, relative population weight) per city, Title-Case keys ──
# Weight is a coarse relative-size tier, not a literal population count.
CITY_INFO: dict[str, tuple[str, float, float, int]] = {
    # ── Delhi NCR ──
    "Delhi":            ("Delhi",            28.6139, 77.2090, 100),
    "Gurugram":         ("Haryana",          28.4595, 77.0266, 45),
    "Faridabad":        ("Haryana",          28.4089, 77.3178, 30),
    "Ghaziabad":        ("Uttar Pradesh",    28.6692, 77.4538, 30),
    "Noida":            ("Uttar Pradesh",    28.5355, 77.3910, 25),

    # ── Maharashtra ──
    "Mumbai":           ("Maharashtra",      19.0760, 72.8777, 100),
    "Pune":             ("Maharashtra",      18.5204, 73.8567, 55),
    "Nagpur":           ("Maharashtra",      21.1458, 79.0882, 30),
    "Thane":            ("Maharashtra",      19.2183, 72.9781, 30),
    "Navi Mumbai":      ("Maharashtra",      19.0330, 73.0297, 20),
    "Nashik":           ("Maharashtra",      20.0059, 73.7910, 22),
    "Aurangabad":       ("Maharashtra",      19.8762, 75.3433, 18),
    "Kalyan":           ("Maharashtra",      19.2403, 73.1305, 15),
    "Solapur":          ("Maharashtra",      17.6599, 75.9064, 12),
    "Kolhapur":         ("Maharashtra",      16.7050, 74.2433, 10),
    "Vasai-Virar":      ("Maharashtra",      19.4912, 72.8054, 10),
    "Amravati":         ("Maharashtra",      20.9374, 77.7796, 8),
    "Sangli":           ("Maharashtra",      16.8524, 74.5815, 6),
    "Jalgaon":          ("Maharashtra",      21.0077, 75.5626, 6),
    "Akola":            ("Maharashtra",      20.7002, 77.0082, 5),

    # ── Karnataka ──
    "Bangalore":        ("Karnataka",        12.9716, 77.5946, 70),
    "Mysore":           ("Karnataka",        12.2958, 76.6394, 15),
    "Hubli":            ("Karnataka",        15.3647, 75.1240, 12),
    "Mangalore":        ("Karnataka",        12.9141, 74.8560, 12),
    "Belgaum":          ("Karnataka",        15.8497, 74.4977, 9),
    "Gulbarga":         ("Karnataka",        17.3297, 76.8343, 7),
    "Davanagere":       ("Karnataka",        14.4644, 75.9932, 6),

    # ── Tamil Nadu ──
    "Chennai":          ("Tamil Nadu",       13.0827, 80.2707, 65),
    "Coimbatore":       ("Tamil Nadu",       11.0168, 76.9558, 25),
    "Madurai":          ("Tamil Nadu",       9.9252,  78.1198, 18),
    "Tiruchirappalli":  ("Tamil Nadu",       10.7905, 78.7047, 12),
    "Salem":            ("Tamil Nadu",       11.6643, 78.1460, 10),
    "Tirunelveli":      ("Tamil Nadu",       8.7139,  77.7567, 8),
    "Erode":            ("Tamil Nadu",       11.3410, 77.7172, 6),
    "Vellore":          ("Tamil Nadu",       12.9165, 79.1325, 6),

    # ── Kerala ──
    "Kochi":            ("Kerala",           9.9312,  76.2673, 25),
    "Thiruvananthapuram": ("Kerala",         8.5241,  76.9366, 22),
    "Kozhikode":        ("Kerala",           11.2588, 75.7804, 15),
    "Thrissur":         ("Kerala",           10.5276, 76.2144, 10),
    "Kollam":           ("Kerala",           8.8932,  76.6141, 8),
    "Kannur":           ("Kerala",           11.8745, 75.3704, 6),

    # ── Andhra Pradesh ──
    "Visakhapatnam":    ("Andhra Pradesh",   17.6868, 83.2185, 28),
    "Vijayawada":       ("Andhra Pradesh",   16.5062, 80.6480, 22),
    "Guntur":           ("Andhra Pradesh",   16.3067, 80.4365, 12),
    "Nellore":          ("Andhra Pradesh",   14.4426, 79.9865, 8),
    "Tirupati":         ("Andhra Pradesh",   13.6288, 79.4192, 8),
    "Kurnool":          ("Andhra Pradesh",   15.8281, 78.0373, 6),

    # ── Telangana ──
    "Hyderabad":        ("Telangana",        17.3850, 78.4867, 65),
    "Warangal":         ("Telangana",        17.9689, 79.5941, 12),
    "Nizamabad":        ("Telangana",        18.6725, 78.0941, 6),

    # ── Gujarat ──
    "Ahmedabad":        ("Gujarat",          23.0225, 72.5714, 55),
    "Surat":            ("Gujarat",          21.1702, 72.8311, 40),
    "Vadodara":         ("Gujarat",          22.3072, 73.1812, 25),
    "Rajkot":           ("Gujarat",          22.3039, 70.8022, 18),
    "Gandhinagar":      ("Gujarat",          23.2156, 72.6369, 8),
    "Bhavnagar":        ("Gujarat",          21.7645, 72.1519, 8),
    "Jamnagar":         ("Gujarat",          22.4707, 70.0577, 7),
    "Junagadh":         ("Gujarat",          21.5222, 70.4579, 5),

    # ── Rajasthan ──
    "Jaipur":           ("Rajasthan",        26.9124, 75.7873, 40),
    "Jodhpur":          ("Rajasthan",        26.2389, 73.0243, 18),
    "Kota":             ("Rajasthan",        25.2138, 75.8648, 12),
    "Udaipur":          ("Rajasthan",        24.5854, 73.7125, 9),
    "Bikaner":          ("Rajasthan",        28.0229, 73.3119, 8),
    "Ajmer":            ("Rajasthan",        26.4499, 74.6399, 8),
    "Bhilwara":         ("Rajasthan",        25.3407, 74.6313, 5),

    # ── Madhya Pradesh ──
    "Indore":           ("Madhya Pradesh",   22.7196, 75.8577, 32),
    "Bhopal":           ("Madhya Pradesh",   23.2599, 77.4126, 28),
    "Jabalpur":         ("Madhya Pradesh",   23.1815, 79.9864, 15),
    "Gwalior":          ("Madhya Pradesh",   26.2183, 78.1828, 14),
    "Ujjain":           ("Madhya Pradesh",   23.1765, 75.7885, 8),
    "Sagar":            ("Madhya Pradesh",   23.8388, 78.7378, 5),
    "Satna":            ("Madhya Pradesh",   24.6005, 80.8322, 5),

    # ── Chhattisgarh ──
    "Raipur":           ("Chhattisgarh",     21.2514, 81.6296, 20),
    "Bhilai":           ("Chhattisgarh",     21.2090, 81.4285, 10),
    "Bilaspur":         ("Chhattisgarh",     22.0797, 82.1409, 7),
    "Korba":            ("Chhattisgarh",     22.3595, 82.6829, 5),

    # ── Uttar Pradesh ──
    "Lucknow":          ("Uttar Pradesh",    26.8467, 80.9462, 35),
    "Kanpur":           ("Uttar Pradesh",    26.4499, 80.3319, 30),
    "Agra":             ("Uttar Pradesh",    27.1767, 78.0081, 22),
    "Varanasi":         ("Uttar Pradesh",    25.3176, 82.9739, 22),
    "Meerut":           ("Uttar Pradesh",    28.9845, 77.7064, 18),
    "Prayagraj":        ("Uttar Pradesh",    25.4358, 81.8463, 16),
    "Bareilly":         ("Uttar Pradesh",    28.3670, 79.4304, 10),
    "Aligarh":          ("Uttar Pradesh",    27.8974, 78.0880, 8),
    "Moradabad":        ("Uttar Pradesh",    28.8386, 78.7733, 8),
    "Gorakhpur":        ("Uttar Pradesh",    26.7606, 83.3732, 8),
    "Saharanpur":       ("Uttar Pradesh",    29.9680, 77.5460, 6),
    "Jhansi":           ("Uttar Pradesh",    25.4484, 78.5685, 5),
    "Mathura":          ("Uttar Pradesh",    27.4924, 77.6737, 4),
    "Firozabad":        ("Uttar Pradesh",    27.1591, 78.3958, 4),

    # ── Bihar ──
    "Patna":            ("Bihar",            25.5941, 85.1376, 30),
    "Gaya":             ("Bihar",            24.7955, 84.9994, 10),
    "Bhagalpur":        ("Bihar",            25.2425, 86.9842, 8),
    "Muzaffarpur":      ("Bihar",            26.1197, 85.3910, 8),
    "Darbhanga":        ("Bihar",            26.1542, 85.8918, 6),
    "Purnia":           ("Bihar",            25.7771, 87.4753, 5),

    # ── Jharkhand ──
    "Ranchi":           ("Jharkhand",        23.3441, 85.3096, 16),
    "Jamshedpur":       ("Jharkhand",        22.8046, 86.2029, 15),
    "Dhanbad":          ("Jharkhand",        23.7957, 86.4304, 12),
    "Bokaro":           ("Jharkhand",        23.6693, 86.1511, 6),

    # ── West Bengal ──
    "Kolkata":          ("West Bengal",      22.5726, 88.3639, 60),
    "Howrah":           ("West Bengal",      22.5958, 88.2636, 20),
    "Durgapur":         ("West Bengal",      23.5204, 87.3119, 10),
    "Asansol":          ("West Bengal",      23.6739, 86.9524, 9),
    "Siliguri":         ("West Bengal",      26.7271, 88.3953, 9),
    "Kharagpur":        ("West Bengal",      22.3460, 87.2320, 5),

    # ── Odisha ──
    "Bhubaneswar":      ("Odisha",           20.2961, 85.8245, 20),
    "Cuttack":          ("Odisha",           20.4625, 85.8828, 12),
    "Rourkela":         ("Odisha",           22.2604, 84.8536, 7),
    "Berhampur":        ("Odisha",           19.3149, 84.7941, 6),

    # ── Punjab ──
    "Ludhiana":         ("Punjab",           30.9009, 75.8573, 25),
    "Amritsar":         ("Punjab",           31.6340, 74.8723, 20),
    "Jalandhar":        ("Punjab",           31.3260, 75.5762, 14),
    "Patiala":          ("Punjab",           30.3398, 76.3869, 9),
    "Bathinda":         ("Punjab",           30.2110, 74.9455, 6),

    # ── Haryana (non-NCR) ──
    "Panipat":          ("Haryana",          29.3909, 76.9635, 8),
    "Hisar":            ("Haryana",          29.1492, 75.7217, 6),
    "Rohtak":           ("Haryana",          28.8955, 76.6066, 6),
    "Karnal":           ("Haryana",          29.6857, 76.9905, 5),

    # ── Assam / Northeast ──
    "Guwahati":         ("Assam",            26.1445, 91.7362, 18),
    "Silchar":          ("Assam",            24.8333, 92.7789, 6),
    "Dibrugarh":        ("Assam",            27.4728, 94.9120, 5),
    "Imphal":           ("Manipur",          24.8170, 93.9368, 5),
    "Shillong":         ("Meghalaya",        25.5788, 91.8933, 5),
    "Agartala":         ("Tripura",          23.8315, 91.2868, 5),
    "Aizawl":           ("Mizoram",          23.7271, 92.7176, 3),
    "Kohima":           ("Nagaland",         25.6751, 94.1086, 3),
    "Itanagar":         ("Arunachal Pradesh",27.0844, 93.6053, 3),
    "Gangtok":          ("Sikkim",           27.3389, 88.6065, 3),

    # ── Uttarakhand ──
    "Dehradun":         ("Uttarakhand",      30.3165, 78.0322, 14),
    "Haridwar":         ("Uttarakhand",      29.9457, 78.1642, 7),

    # ── Himachal Pradesh ──
    "Shimla":           ("Himachal Pradesh", 31.1048, 77.1734, 7),
    "Dharamshala":      ("Himachal Pradesh", 32.2190, 76.3234, 4),

    # ── J&K / Ladakh ──
    "Srinagar":         ("Jammu and Kashmir",34.0837, 74.7973, 12),
    "Jammu":            ("Jammu and Kashmir",32.7266, 74.8570, 12),
    "Leh":              ("Ladakh",           34.1526, 77.5771, 3),

    # ── Chandigarh (UT) ──
    "Chandigarh":       ("Chandigarh",       30.7333, 76.7794, 15),

    # ── Goa ──
    "Panaji":           ("Goa",              15.4909, 73.8278, 6),
    "Margao":           ("Goa",              15.2832, 73.9862, 5),

    # ── Puducherry (UT) ──
    "Puducherry":       ("Puducherry",       11.9416, 79.8083, 6),
}

# ─── Lowercase lat/lon-only view — drop-in replacement for the old private
# `_CITY_COORDS` dict in gnn_service.py, plus a few common alias spellings that
# resolve to the same centroid. ────────────────────────────────────────────────
_ALIASES: dict[str, str] = {
    "new delhi":  "Delhi",
    "bengaluru":  "Bangalore",
    "kanpur nagar": "Kanpur",
    "prayagraj":  "Prayagraj",
    "allahabad":  "Prayagraj",
    "gurgaon":    "Gurugram",
    "vizag":      "Visakhapatnam",
    "trivandrum": "Thiruvananthapuram",
    "calicut":    "Kozhikode",
    "cochin":     "Kochi",
    "trichy":     "Tiruchirappalli",
    "pondicherry": "Puducherry",
    "vasai":      "Vasai-Virar",
    "kalyan-dombivli": "Kalyan",
    "belagavi":   "Belgaum",
    "kalaburagi": "Gulbarga",
    "chhatrapati sambhajinagar": "Aurangabad",
}

CITY_COORDS: dict[str, tuple[float, float]] = {
    name.lower(): (lat, lon) for name, (_, lat, lon, _weight) in CITY_INFO.items()
}
for _alias, _canonical in _ALIASES.items():
    _state, _lat, _lon, _w = CITY_INFO[_canonical]
    CITY_COORDS[_alias] = (_lat, _lon)

# ─── (city, state, weight) list for weighted patient-city sampling ───────────
CITIES: list[tuple[str, str, int]] = [
    (name, state, weight) for name, (state, _lat, _lon, weight) in CITY_INFO.items()
]

# ─── Real India Post postal-circle numbering, approximated per state as an
# inclusive 6-digit range. See module docstring for caveats. ─────────────────
STATE_PINCODE_RANGES: dict[str, tuple[int, int]] = {
    "Delhi":               (110001, 110097),
    "Haryana":             (121001, 136156),
    "Punjab":              (140001, 160104),
    "Chandigarh":          (160001, 160104),
    "Himachal Pradesh":    (171001, 177601),
    "Jammu and Kashmir":   (180001, 194301),
    "Ladakh":              (194101, 194404),
    "Uttar Pradesh":       (201001, 285223),
    "Uttarakhand":         (244001, 263679),
    "Rajasthan":           (301001, 345034),
    "Gujarat":             (360001, 396590),
    "Goa":                 (403001, 403806),
    "Maharashtra":         (400001, 445402),
    "Madhya Pradesh":      (450001, 488450),
    "Chhattisgarh":        (490001, 497778),
    "Telangana":           (500001, 509412),
    "Andhra Pradesh":      (515001, 535594),
    "Karnataka":           (560001, 591346),
    "Tamil Nadu":          (600001, 643253),
    "Puducherry":          (605001, 605602),
    "Kerala":              (670001, 695615),
    "West Bengal":         (700001, 743711),
    "Sikkim":              (737101, 737139),
    "Odisha":              (751001, 770076),
    "Jharkhand":           (813001, 835325),
    "Bihar":               (800001, 855117),
    "Assam":               (781001, 788931),
    "Meghalaya":           (793001, 794115),
    "Manipur":             (795001, 795159),
    "Mizoram":             (796001, 796901),
    "Nagaland":            (797001, 798627),
    "Tripura":             (799001, 799290),
    "Arunachal Pradesh":   (790001, 792131),
}


def sample_pincode(state: str, rng: random.Random | None = None) -> str:
    """Sample a 6-digit pincode that falls within the given state's real postal range."""
    r = rng or random
    lo, hi = STATE_PINCODE_RANGES.get(state, (110001, 855117))
    return str(r.randint(lo, hi))
