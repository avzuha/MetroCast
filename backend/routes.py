import os
import math
import pandas as pd
import networkx as nx
from functools import lru_cache
from typing import Optional

# ─────────────────────────────────────────────
# GTFS FILE PATHS
# ─────────────────────────────────────────────
GTFS_PATH = os.path.join(os.path.dirname(__file__), "gtfs")

# ─────────────────────────────────────────────
# DMRC OFFICIAL FARE SLABS (as of 2024)
# ─────────────────────────────────────────────
FARE_SLABS = [
    (2,   10),
    (5,   20),
    (12,  30),
    (21,  40),
    (32,  50),
    (float("inf"), 60),
]

# ─────────────────────────────────────────────
# LINE COLOR MAP (DMRC official line names)
# ─────────────────────────────────────────────
LINE_COLOR_MAP = {
    "red":       "#E53935",
    "yellow":    "#FDD835",
    "blue":      "#1E88E5",
    "green":     "#43A047",
    "violet":    "#8E24AA",
    "orange":    "#FB8C00",
    "magenta":   "#D81B60",
    "pink":      "#F06292",
    "grey":      "#757575",
    "aqua":      "#00ACC1",
    "rapid":     "#FF7043",
}

# ─────────────────────────────────────────────
# METRO STATIONS (official DMRC stations only)
# ─────────────────────────────────────────────
METRO_STATIONS = {
    "Adarsh Nagar": "Yellow",
    "Ajronda": "Violet",
    "Akshardham": "Blue",
    "Anand Vihar ISBT": "Blue",
    "Arjan Garh": "Yellow",
    "Arthala": "Red",
    "Ashok Park Main": "Green",
    "Ashok Nagar": "Pink",
    "AIIMS": "Yellow",
    "Azadpur": "Yellow",
    "Badarpur Border": "Violet",
    "Bahadurgarh City": "Green",
    "Baljit Nagar": "Pink",
    "Ballabhgarh": "Violet",
    "Bata Chowk": "Violet",
    "Botanical Garden": "Magenta",
    "Brigadier Hoshiyar Singh": "Green",
    "Central Secretariat": "Yellow",
    "Chatterpur": "Yellow",
    "Chawri Bazar": "Yellow",
    "Civil Lines": "Yellow",
    "Dabri Mor - Janakpuri South": "Magenta",
    "Dashrathpuri": "Magenta",
    "Delhi Aerocity": "Orange",
    "Delhi Cantt": "Blue",
    "Dilshad Garden": "Red",
    "Durgabai Deshmukh South Campus": "Pink",
    "Dwarka": "Blue",
    "Dwarka Mor": "Blue",
    "Dwarka Sector 10": "Blue",
    "Dwarka Sector 11": "Blue",
    "Dwarka Sector 12": "Blue",
    "Dwarka Sector 13": "Blue",
    "Dwarka Sector 14": "Blue",
    "Dwarka Sector 21": "Blue",
    "East Azad Nagar": "Pink",
    "Escorts Mujesar": "Violet",
    "ESI Hospital": "Green",
    "Faridabad New Town": "Violet",
    "Ghevra": "Green",
    "GNIDA Office": "Aqua",
    "Gokulpuri": "Pink",
    "Govind Puri": "Violet",
    "Greater Kailash": "Magenta",
    "GTB Nagar": "Yellow",
    "Hauz Khas": "Yellow",
    "Hindon River": "Red",
    "Huda City Centre": "Yellow",
    "INA": "Yellow",
    "Inderlok": "Green",
    "Indira Gandhi International Airport": "Orange",
    "IP Extension": "Pink",
    "ITO": "Violet",
    "Jahangirpuri": "Yellow",
    "Jama Masjid": "Violet",
    "Janakpuri East": "Magenta",
    "Janakpuri West": "Magenta",
    "Jasola Apollo": "Violet",
    "Jasola Vihar Shaheen Bagh": "Magenta",
    "Jhandewalan": "Yellow",
    "Jhilmil": "Pink",
    "Jonapur": "Magenta",
    "Kali Bari Marg": "Pink",
    "Kalkaji Mandir": "Violet",
    "Kalindi Kunj": "Magenta",
    "Kashmere Gate": "Violet",
    "Keshav Puram": "Green",
    "Khan Market": "Violet",
    "Khyala": "Green Branch",
    "Kirti Nagar": "Green",
    "Krishna Nagar": "Pink",
    "Lajpat Nagar": "Violet",
    "Lal Quila": "Violet",
    "Lado Sarai": "Yellow",
    "Laxmi Nagar": "Blue",
    "Lok Kalyan Marg": "Pink",
    "Lok Nayak Hospital": "Pink",
    "Majlis Park": "Pink",
    "Malviya Nagar": "Yellow",
    "Mandawali - West Vinod Nagar": "Pink",
    "Mansarovar Park": "Red",
    "Mandi House": "Violet",
    "Maya Puri": "Green",
    "Metro Bhawan": "Yellow",
    "MG Road": "Yellow",
    "Model Town": "Yellow",
    "Mohan Estate": "Violet",
    "Moti Nagar": "Blue",
    "Mundka": "Green",
    "Mundka Industrial Area": "Green",
    "Najafgarh": "Grey",
    "Nangloi": "Green",
    "Nangloi Railway Station": "Green",
    "Netaji Subhash Place": "Red",
    "New Delhi": "Orange",
    "Noida City Centre": "Blue",
    "Noida Electronic City": "Blue",
    "Noida Sector 15": "Blue",
    "Noida Sector 16": "Blue",
    "Noida Sector 18": "Blue",
    "Noida Sector 34": "Blue",
    "Noida Sector 52": "Blue",
    "Noida Sector 62": "Blue",
    "Okhla": "Violet",
    "Okhla Bird Sanctuary": "Magenta",
    "Okhla NSIC": "Magenta",
    "Palam": "Magenta",
    "Patel Chowk": "Yellow",
    "Patel Nagar": "Green",
    "Patparganj": "Blue",
    "Pitampura": "Red",
    "Preet Vihar": "Blue",
    "Punjabi Bagh East": "Green",
    "Punjabi Bagh West": "Pink",
    "Pushp Vihar": "Yellow",
    "Qutub Minar": "Yellow",
    "Rajiv Chowk": "Yellow",
    "Rajouri Garden": "Blue",
    "Raja Nahar Singh (Ballabhgarh)": "Violet",
    "Ram Krishna Ashram Marg": "Yellow",
    "Rithala": "Red",
    "RRTS Sarai Kale Khan": "Rapid",
    "Sadar Bazar Cantonment": "Magenta",
    "Saket": "Yellow",
    "Samaypur Badli": "Yellow",
    "Sarojini Nagar": "Pink",
    "Sarita Vihar": "Violet",
    "Sector 28 Faridabad": "Violet",
    "Sector 31 Faridabad": "Violet",
    "Shastri Nagar": "Yellow",
    "Shastri Park": "Red",
    "Shiv Vihar": "Pink",
    "Sikandarpur": "Yellow",
    "South Campus": "Yellow",
    "Subhash Nagar": "Blue",
    "Sunder Nagar": "Violet",
    "Surajmal Stadium": "Pink",
    "Tagore Garden": "Blue",
    "Terminal 1 IGI Airport": "Magenta",
    "Tikri Border": "Green",
    "Tikri Kalan": "Green",
    "Trilokpuri Sanjay Lake": "Pink",
    "Tis Hazari": "Yellow",
    "Udyog Bhawan": "Yellow",
    "Uttam Nagar East": "Blue",
    "Uttam Nagar West": "Blue",
    "Vaishali": "Blue",
    "Vasant Kunj Sector D": "Magenta",
    "Vasant Vihar": "Magenta",
    "Vidhan Sabha": "Yellow",
    "Vinobapuri": "Violet",
    "Vishwavidyalaya": "Yellow",
    "Welcome": "Red",
    "Yamuna Bank": "Blue"
}


# ─────────────────────────────────────────────
# LOAD GTFS DATA (once at startup)
# ─────────────────────────────────────────────

def _load_gtfs():
    """
    Loads all relevant GTFS tables into DataFrames.
    Returns a dict of DataFrames.
    """
    try:
        stops        = pd.read_csv(f"{GTFS_PATH}/stops.txt",      dtype=str)
        routes       = pd.read_csv(f"{GTFS_PATH}/routes.txt",     dtype=str)
        trips        = pd.read_csv(f"{GTFS_PATH}/trips.txt",      dtype=str)
        stop_times   = pd.read_csv(f"{GTFS_PATH}/stop_times.txt", dtype=str)

        # Normalize column names (strip whitespace)
        for df in [stops, routes, trips, stop_times]:
            df.columns = df.columns.str.strip()

        # Convert stop_sequence to int for ordering
        stop_times["stop_sequence"] = pd.to_numeric(
            stop_times["stop_sequence"], errors="coerce"
        )

        return {
            "stops":      stops,
            "routes":     routes,
            "trips":      trips,
            "stop_times": stop_times,
        }
    except FileNotFoundError as e:
        raise RuntimeError(
            f"GTFS file missing: {e}. "
            f"Make sure all files are in {GTFS_PATH}/"
        )


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns distance in km between two lat/lon points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi       = math.radians(lat2 - lat1)
    dlambda    = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _build_graph(gtfs: dict) -> tuple[nx.Graph, dict, dict]:
    """
    Builds a weighted undirected graph where:
      - Nodes  = stop_id
      - Edges  = consecutive stops on the same trip
      - Weight = haversine distance in km between stops

    Also returns:
      stop_info : { stop_id -> { name, lat, lon, line_name } }
      name_to_id: { normalized_stop_name -> stop_id }
    """
    stops      = gtfs["stops"]
    trips      = gtfs["trips"]
    stop_times = gtfs["stop_times"]
    routes_df  = gtfs["routes"]

    # ── Build stop_info lookup ──────────────────────────────────────
    stop_info = {}
    for _, row in stops.iterrows():
        sid = str(row["stop_id"]).strip()
        try:
            lat = float(row.get("stop_lat", 0))
            lon = float(row.get("stop_lon", 0))
        except (ValueError, TypeError):
            lat, lon = 0.0, 0.0

        stop_info[sid] = {
            "name": str(row.get("stop_name", sid)).strip(),
            "lat":  lat,
            "lon":  lon,
            "line": "",  # filled below
        }

    # ── Map trip_id -> route_long_name (line name) ─────────────────
    route_name_map = {}
    for _, r in routes_df.iterrows():
        rid  = str(r["route_id"]).strip()
        name = str(r.get("route_long_name", r.get("route_short_name", rid))).strip()
        route_name_map[rid] = name

    trip_to_route = {}
    for _, t in trips.iterrows():
        tid = str(t["trip_id"]).strip()
        rid = str(t["route_id"]).strip()
        trip_to_route[tid] = route_name_map.get(rid, rid)

    # ── Build the graph ────────────────────────────────────────────
    G = nx.Graph()

    # Group stop_times by trip, sorted by sequence
    grouped = (
        stop_times
        .sort_values("stop_sequence")
        .groupby("trip_id")
    )

    for trip_id, group in grouped:
        stop_ids  = group["stop_id"].astype(str).str.strip().tolist()
        line_name = trip_to_route.get(str(trip_id).strip(), "unknown")

        for i in range(len(stop_ids) - 1):
            s1 = stop_ids[i]
            s2 = stop_ids[i + 1]

            if s1 not in stop_info or s2 not in stop_info:
                continue

            # Tag stops with their line
            stop_info[s1]["line"] = line_name
            stop_info[s2]["line"] = line_name

            dist = _haversine_km(
                stop_info[s1]["lat"], stop_info[s1]["lon"],
                stop_info[s2]["lat"], stop_info[s2]["lon"],
            )
            dist = max(dist, 0.1)  # avoid zero-weight edges

            # Keep the shortest edge between any two stops
            if G.has_edge(s1, s2):
                if G[s1][s2]["weight"] > dist:
                    G[s1][s2]["weight"]     = dist
                    G[s1][s2]["line"]       = line_name
            else:
                G.add_edge(s1, s2, weight=dist, line=line_name)

    # ── Build name -> id lookup (lowercase, stripped) ──────────────
    name_to_id = {}
    for sid, info in stop_info.items():
        key = info["name"].lower().strip()
        # If duplicate names exist, prefer the first encountered
        if key not in name_to_id:
            name_to_id[key] = sid

    return G, stop_info, name_to_id


# ─────────────────────────────────────────────
# MODULE-LEVEL SINGLETONS  (loaded once)
# ─────────────────────────────────────────────
print("[MetroCast] Loading GTFS data...")
_GTFS     = _load_gtfs()
_G, _STOP_INFO, _NAME_TO_ID = _build_graph(_GTFS)
print(f"[MetroCast] Graph ready: {_G.number_of_nodes()} stations, "
      f"{_G.number_of_edges()} edges")

# ── Update stop_info with metro lines ─────────────────────────────
for sid, info in _STOP_INFO.items():
    name = info["name"]
    if name in METRO_STATIONS:
        _STOP_INFO[sid]["line"] = METRO_STATIONS[name]


# ─────────────────────────────────────────────
# PUBLIC HELPERS
# ─────────────────────────────────────────────

def list_all_stations() -> list[dict]:
    """Returns all metro stations sorted alphabetically by name."""
    stations = []
    for sid, info in _STOP_INFO.items():
        name = info["name"]
        if name in METRO_STATIONS:
            line = METRO_STATIONS[name]
            color = LINE_COLOR_MAP.get(line.lower().replace(" branch", ""), "#888")
            stations.append({
                "id":   sid,
                "name": name,
                "line": line,
                "color": color,
                "lat":  info["lat"],
                "lon":  info["lon"],
            })
    return sorted(stations, key=lambda x: x["name"].lower())


def resolve_station(query: str) -> Optional[str]:
    """
    Takes a station name string (from user input) and returns
    the matching stop_id, or None if not found.
    Tries: exact match -> partial match.
    """
    q = query.lower().strip()

    # 1. Exact match
    if q in _NAME_TO_ID:
        return _NAME_TO_ID[q]

    # 2. Partial match (first result)
    for name, sid in _NAME_TO_ID.items():
        if q in name or name in q:
            return sid

    return None


def get_fare(distance_km: float) -> int:
    """Returns fare in INR based on DMRC official slabs."""
    for limit, fare in FARE_SLABS:
        if distance_km <= limit:
            return fare
    return 60


def get_route(from_station: str, to_station: str) -> dict:
    """
    Main route-planning function.

    Parameters
    ----------
    from_station : str  Station name (e.g. "Rajiv Chowk")
    to_station   : str  Station name (e.g. "Huda City Centre")

    Returns
    -------
    dict with keys:
        path         - ordered list of station names
        stops        - total number of stops
        interchanges - list of interchange station names
        distance_km  - total route distance
        duration_min - estimated travel time
        lines        - metro lines used
        fare_inr     - fare in rupees
    """

    # ── Resolve names to stop_ids ──────────────────────────────────
    from_id = resolve_station(from_station)
    to_id   = resolve_station(to_station)

    if from_id is None:
        raise ValueError(
            f"Station not found: '{from_station}'. "
            f"Check spelling or use list_all_stations()."
        )
    if to_id is None:
        raise ValueError(
            f"Station not found: '{to_station}'. "
            f"Check spelling or use list_all_stations()."
        )
    if from_id == to_id:
        raise ValueError("Source and destination are the same station.")

    # ── Shortest path (Dijkstra by distance weight) ────────────────
    try:
        path_ids = nx.shortest_path(
            _G, source=from_id, target=to_id, weight="weight"
        )
    except nx.NetworkXNoPath:
        raise ValueError(
            f"No route found between '{from_station}' and '{to_station}'. "
            f"The network may be disconnected in the GTFS data."
        )

    # ── Build human-readable path + metadata ──────────────────────
    path_names   = []
    total_dist   = 0.0
    lines_used   = []
    interchanges = []
    prev_line    = None

    for i, sid in enumerate(path_ids):
        info = _STOP_INFO.get(sid, {})
        name = info.get("name", sid)
        line = info.get("line", "")

        path_names.append(name)

        if i > 0:
            prev_id = path_ids[i - 1]
            if _G.has_edge(prev_id, sid):
                total_dist += _G[prev_id][sid]["weight"]

        # Detect interchanges (line change)
        if line and line != prev_line and prev_line is not None:
            interchanges.append(name)

        if line and line not in lines_used:
            lines_used.append(line)

        prev_line = line

    stops        = len(path_names)
    duration_min = _estimate_duration(total_dist, len(interchanges))
    fare         = get_fare(total_dist)

    # Attach line colors
    line_details = []
    for l in lines_used:
        color_key = _infer_color_key(l)
        line_details.append({
            "name":  l,
            "color": LINE_COLOR_MAP.get(color_key, "#888888"),
        })

    return {
        "from":          _STOP_INFO[from_id]["name"],
        "to":            _STOP_INFO[to_id]["name"],
        "path":          path_names,
        "stops":         stops,
        "interchanges":  interchanges,
        "distance_km":   round(total_dist, 2),
        "duration_min":  duration_min,
        "lines":         line_details,
        "fare_inr":      fare,
    }


# ─────────────────────────────────────────────
# PRIVATE HELPERS
# ─────────────────────────────────────────────

def _estimate_duration(distance_km: float, num_interchanges: int) -> int:
    """
    Estimates travel time in minutes.
    DMRC average speed ~33 km/h + 4 min per interchange for platform change.
    """
    travel_min      = (distance_km / 33.0) * 60
    interchange_min = num_interchanges * 4
    return math.ceil(travel_min + interchange_min)


def _infer_color_key(line_name: str) -> str:
    """Infers color key from DMRC line name string."""
    ln = line_name.lower()
    for color in LINE_COLOR_MAP:
        if color in ln:
            return color
    return "grey"
