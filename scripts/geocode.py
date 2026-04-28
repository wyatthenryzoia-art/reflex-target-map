#!/usr/bin/env python3
"""Geocode (hq_city, hq_country) pairs from companies.csv to lat/lon.

Strategy:
1. Hardcoded dict for high-frequency cities (instant, no network).
2. OpenStreetMap Nominatim for the rest (1 req/sec, free, no key).
3. Country centroid fallback when city is blank.
4. Skip rows with neither city nor country.

Output: data/geocoded.csv with columns hq_city,hq_country,lat,lon,source
"""

import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IN_CSV = ROOT / "data" / "companies.csv"
OUT_CSV = ROOT / "data" / "geocoded.csv"
CACHE_FILE = ROOT / "cache" / "geocode_cache.json"

USER_AGENT = "reflex-target-map/0.1 (wyatthenryzoia@gmail.com)"

# ---------------------------------------------------------------------------
# Hardcoded city coordinates (lat, lon). Keys are (city_lower, country_lower).
# country_lower normalized to common short forms used in the CSV.
# ---------------------------------------------------------------------------
HARDCODED = {
    # USA
    ("san francisco", "usa"): (37.7749, -122.4194),
    ("new york", "usa"): (40.7128, -74.0060),
    ("boston", "usa"): (42.3601, -71.0589),
    ("pittsburgh", "usa"): (40.4406, -79.9959),
    ("pasadena", "usa"): (34.1478, -118.1445),
    ("palo alto", "usa"): (37.4419, -122.1430),
    ("mountain view", "usa"): (37.3861, -122.0839),
    ("sunnyvale", "usa"): (37.3688, -122.0363),
    ("san jose", "usa"): (37.3382, -121.8863),
    ("fremont", "usa"): (37.5485, -121.9886),
    ("irvine", "usa"): (33.6846, -117.8265),
    ("redwood city", "usa"): (37.4852, -122.2364),
    ("menlo park", "usa"): (37.4530, -122.1817),
    ("los angeles", "usa"): (34.0522, -118.2437),
    ("seattle", "usa"): (47.6062, -122.3321),
    ("austin", "usa"): (30.2672, -97.7431),
    ("chicago", "usa"): (41.8781, -87.6298),
    ("cambridge", "usa"): (42.3736, -71.1097),
    ("berkeley", "usa"): (37.8716, -122.2727),
    ("oakland", "usa"): (37.8044, -122.2712),
    ("san diego", "usa"): (32.7157, -117.1611),
    ("denver", "usa"): (39.7392, -104.9903),
    ("atlanta", "usa"): (33.7490, -84.3880),
    ("washington", "usa"): (38.9072, -77.0369),
    ("philadelphia", "usa"): (39.9526, -75.1652),
    ("houston", "usa"): (29.7604, -95.3698),
    ("dallas", "usa"): (32.7767, -96.7970),
    ("detroit", "usa"): (42.3314, -83.0458),
    ("miami", "usa"): (25.7617, -80.1918),
    ("portland", "usa"): (45.5152, -122.6784),
    ("brooklyn", "usa"): (40.6782, -73.9442),
    ("nashville", "usa"): (36.1627, -86.7816),
    ("salt lake city", "usa"): (40.7608, -111.8910),
    ("philadelphia", "usa"): (39.9526, -75.1652),
    ("san mateo", "usa"): (37.5630, -122.3255),
    ("san juan", "usa"): (18.4655, -66.1057),
    ("kirkland", "usa"): (47.6815, -122.2087),
    ("wilmington", "usa"): (39.7391, -75.5398),
    ("downers grove", "usa"): (41.8089, -88.0112),
    ("gardena", "usa"): (33.8884, -118.3089),
    ("martinez", "usa"): (38.0194, -122.1341),
    ("dresden", "germany"): (51.0504, 13.7373),
    ("karlsruhe", "germany"): (49.0069, 8.4037),
    ("winterthur", "switzerland"): (47.5022, 8.7386),
    ("lille", "france"): (50.6292, 3.0573),
    ("belgrade", "serbia"): (44.7866, 20.4489),
    ("bratislava", "slovakia"): (48.1486, 17.1077),
    ("kuala lumpur", "malaysia"): (3.1390, 101.6869),
    ("abu dhabi", "uae"): (24.4539, 54.3773),
    ("abu dhabi", "united arab emirates"): (24.4539, 54.3773),
    ("noida", "india"): (28.5355, 77.3910),
    ("reading", "united kingdom"): (51.4543, -0.9781),
    ("sejong-si", "south korea"): (36.4801, 127.2890),
    ("wuxi", "china"): (31.4912, 120.3119),
    # Asia
    ("tokyo", "japan"): (35.6762, 139.6503),
    ("osaka", "japan"): (34.6937, 135.5023),
    ("kyoto", "japan"): (35.0116, 135.7681),
    ("beijing", "china"): (39.9042, 116.4074),
    ("shanghai", "china"): (31.2304, 121.4737),
    ("shenzhen", "china"): (22.5431, 114.0579),
    ("hangzhou", "china"): (30.2741, 120.1551),
    ("guangzhou", "china"): (23.1291, 113.2644),
    ("suzhou", "china"): (31.2989, 120.5853),
    ("seoul", "south korea"): (37.5665, 126.9780),
    ("seoul", "korea"): (37.5665, 126.9780),
    ("hong kong", "hong kong"): (22.3193, 114.1694),
    ("hong kong", "china"): (22.3193, 114.1694),
    ("taipei", "taiwan"): (25.0330, 121.5654),
    ("bangkok", "thailand"): (13.7563, 100.5018),
    ("hanoi", "vietnam"): (21.0285, 105.8542),
    ("ho chi minh city", "vietnam"): (10.8231, 106.6297),
    ("singapore", "singapore"): (1.3521, 103.8198),
    ("bangalore", "india"): (12.9716, 77.5946),
    ("bengaluru", "india"): (12.9716, 77.5946),
    ("mumbai", "india"): (19.0760, 72.8777),
    ("delhi", "india"): (28.7041, 77.1025),
    ("new delhi", "india"): (28.6139, 77.2090),
    ("tel aviv", "israel"): (32.0853, 34.7818),
    # Europe
    ("london", "united kingdom"): (51.5074, -0.1278),
    ("london", "uk"): (51.5074, -0.1278),
    ("oxford", "united kingdom"): (51.7520, -1.2577),
    ("cambridge", "united kingdom"): (52.2053, 0.1218),
    ("manchester", "united kingdom"): (53.4808, -2.2426),
    ("edinburgh", "united kingdom"): (55.9533, -3.1883),
    ("berlin", "germany"): (52.5200, 13.4050),
    ("munich", "germany"): (48.1351, 11.5820),
    ("stuttgart", "germany"): (48.7758, 9.1829),
    ("hamburg", "germany"): (53.5511, 9.9937),
    ("frankfurt", "germany"): (50.1109, 8.6821),
    ("cologne", "germany"): (50.9375, 6.9603),
    ("zurich", "switzerland"): (47.3769, 8.5417),
    ("geneva", "switzerland"): (46.2044, 6.1432),
    ("lausanne", "switzerland"): (46.5197, 6.6323),
    ("paris", "france"): (48.8566, 2.3522),
    ("lyon", "france"): (45.7640, 4.8357),
    ("bordeaux", "france"): (44.8378, -0.5792),
    ("marseille", "france"): (43.2965, 5.3698),
    ("toulouse", "france"): (43.6047, 1.4442),
    ("warsaw", "poland"): (52.2297, 21.0122),
    ("krakow", "poland"): (50.0647, 19.9450),
    ("madrid", "spain"): (40.4168, -3.7038),
    ("barcelona", "spain"): (41.3851, 2.1734),
    ("amsterdam", "netherlands"): (52.3676, 4.9041),
    ("rotterdam", "netherlands"): (51.9244, 4.4777),
    ("delft", "netherlands"): (52.0116, 4.3571),
    ("eindhoven", "netherlands"): (51.4416, 5.4697),
    ("stockholm", "sweden"): (59.3293, 18.0686),
    ("gothenburg", "sweden"): (57.7089, 11.9746),
    ("helsinki", "finland"): (60.1699, 24.9384),
    ("copenhagen", "denmark"): (55.6761, 12.5683),
    ("oslo", "norway"): (59.9139, 10.7522),
    ("genoa", "italy"): (44.4056, 8.9463),
    ("genova", "italy"): (44.4056, 8.9463),
    ("milan", "italy"): (45.4642, 9.1900),
    ("rome", "italy"): (41.9028, 12.4964),
    ("turin", "italy"): (45.0703, 7.6869),
    ("vienna", "austria"): (48.2082, 16.3738),
    ("dublin", "ireland"): (53.3498, -6.2603),
    ("brussels", "belgium"): (50.8503, 4.3517),
    ("lisbon", "portugal"): (38.7223, -9.1393),
    ("prague", "czech republic"): (50.0755, 14.4378),
    ("budapest", "hungary"): (47.4979, 19.0402),
    ("athens", "greece"): (37.9838, 23.7275),
    # Other
    ("sydney", "australia"): (-33.8688, 151.2093),
    ("melbourne", "australia"): (-37.8136, 144.9631),
    ("toronto", "canada"): (43.6532, -79.3832),
    ("vancouver", "canada"): (49.2827, -123.1207),
    ("montreal", "canada"): (45.5017, -73.5673),
    ("waterloo", "canada"): (43.4643, -80.5204),
    ("sao paulo", "brazil"): (-23.5505, -46.6333),
    ("mexico city", "mexico"): (19.4326, -99.1332),
}

# Country centroids for fallback when city is blank
COUNTRY_CENTROIDS = {
    "usa": (39.5, -98.5),
    "united states": (39.5, -98.5),
    "us": (39.5, -98.5),
    "china": (35.0, 103.0),
    "japan": (36.2, 138.3),
    "south korea": (36.5, 127.8),
    "korea": (36.5, 127.8),
    "india": (20.6, 78.96),
    "germany": (51.2, 10.45),
    "united kingdom": (54.0, -2.0),
    "uk": (54.0, -2.0),
    "france": (46.227, 2.213),
    "italy": (41.87, 12.57),
    "spain": (40.46, -3.75),
    "netherlands": (52.13, 5.29),
    "switzerland": (46.82, 8.23),
    "sweden": (60.13, 18.64),
    "finland": (61.92, 25.75),
    "denmark": (56.26, 9.50),
    "norway": (60.47, 8.47),
    "poland": (51.92, 19.15),
    "austria": (47.52, 14.55),
    "belgium": (50.50, 4.47),
    "ireland": (53.41, -8.24),
    "portugal": (39.40, -8.22),
    "israel": (31.05, 34.85),
    "singapore": (1.35, 103.82),
    "taiwan": (23.70, 120.96),
    "hong kong": (22.32, 114.17),
    "thailand": (15.87, 100.99),
    "vietnam": (14.06, 108.28),
    "australia": (-25.27, 133.78),
    "canada": (56.13, -106.35),
    "brazil": (-14.24, -51.93),
    "mexico": (23.63, -102.55),
    "russia": (61.52, 105.32),
    "turkey": (38.96, 35.24),
    "uae": (23.42, 53.85),
    "united arab emirates": (23.42, 53.85),
    "saudi arabia": (23.89, 45.08),
    "south africa": (-30.56, 22.94),
    "new zealand": (-40.90, 174.89),
    "estonia": (58.60, 25.01),
    "czech republic": (49.82, 15.47),
    "hungary": (47.16, 19.50),
    "greece": (39.07, 21.82),
    "ukraine": (48.38, 31.17),
    "romania": (45.94, 24.97),
}


COUNTRY_ALIASES = {
    "us": "usa",
    "united states": "usa",
    "u.s.a.": "usa",
    "u.s.": "usa",
    "uk": "united kingdom",
    "gb": "united kingdom",
    "great britain": "united kingdom",
    "england": "united kingdom",
    "ch": "switzerland",
    "cn": "china",
    "fr": "france",
    "de": "germany",
    "jp": "japan",
    "kr": "south korea",
    "korea": "south korea",
    "in": "india",
    "it": "italy",
    "es": "spain",
    "nl": "netherlands",
    "sg": "singapore",
    "tw": "taiwan",
    "hk": "hong kong",
    "ca": "canada",
    "au": "australia",
}

CITY_ALIASES = {
    "mountain view, ca": "mountain view",
    "sunnyvale, ca": "sunnyvale",
    "san juan, pr": "san juan",
    "bengaluru": "bangalore",
}


def norm(s):
    return (s or "").strip().lower()


def norm_country(s):
    n = norm(s)
    return COUNTRY_ALIASES.get(n, n)


def norm_city(s):
    n = norm(s)
    return CITY_ALIASES.get(n, n)


def load_cache():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_cache(cache):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2))


def nominatim_lookup(city, country):
    q = f"{city}, {country}".strip(", ")
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": q, "format": "json", "limit": 1}
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"  [nominatim ERROR] {q}: {e}", file=sys.stderr)
    return None


def main():
    rows = list(csv.DictReader(IN_CSV.open()))
    pairs = set()
    for r in rows:
        c = (r.get("hq_city") or "").strip()
        ctry = (r.get("hq_country") or "").strip()
        if not c and not ctry:
            continue
        pairs.add((c, ctry))

    print(f"Loaded {len(rows)} rows; {len(pairs)} unique (city, country) pairs")

    cache = load_cache()
    results = []  # list of dict
    counts = {"hardcoded": 0, "nominatim": 0, "country_centroid": 0, "cache": 0, "skipped": 0, "failed": 0}

    sorted_pairs = sorted(pairs)
    for i, (city, country) in enumerate(sorted_pairs):
        cl, ctryl = norm_city(city), norm_country(country)
        cache_key = f"{cl}|{ctryl}"
        source = None
        latlon = None

        # 1. Hardcoded
        if (cl, ctryl) in HARDCODED:
            latlon = HARDCODED[(cl, ctryl)]
            source = "hardcoded"
        # 2. Cache
        elif cache_key in cache:
            entry = cache[cache_key]
            latlon = (entry["lat"], entry["lon"])
            source = entry.get("source", "cache")
            if source == "nominatim":
                source = "nominatim"  # keep original
            counts["cache"] += 1 if source == "cache" else 0
        # 3. Try Nominatim if we have a city
        elif city:
            print(f"[{i+1}/{len(sorted_pairs)}] nominatim: {city}, {country}")
            res = nominatim_lookup(city, country)
            time.sleep(1.1)  # respect 1 req/sec rate limit
            if res:
                latlon = res
                source = "nominatim"
                cache[cache_key] = {"lat": res[0], "lon": res[1], "source": "nominatim"}
                save_cache(cache)
        # 4. Country centroid fallback
        if latlon is None and ctryl in COUNTRY_CENTROIDS:
            latlon = COUNTRY_CENTROIDS[ctryl]
            source = "country_centroid"

        if latlon is None:
            counts["skipped" if not city and not country else "failed"] += 1
            print(f"  [SKIP] {city!r}, {country!r} - no match")
            continue

        if source in counts:
            counts[source] += 1
        results.append({
            "hq_city": city,
            "hq_country": country,
            "lat": round(latlon[0], 4),
            "lon": round(latlon[1], 4),
            "source": source,
        })

    # Write output
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["hq_city", "hq_country", "lat", "lon", "source"])
        w.writeheader()
        w.writerows(results)

    print("\n=== Summary ===")
    print(f"Total input rows:        {len(rows)}")
    print(f"Unique (city,country):   {len(pairs)}")
    print(f"Geocoded rows written:   {len(results)}")
    for k, v in counts.items():
        print(f"  {k:20s} {v}")
    print(f"\nWrote {OUT_CSV}")


if __name__ == "__main__":
    main()
