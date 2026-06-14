#!/usr/bin/env python3
"""
scripts/fetch_osm.py
One-time build: fetch Guangzhou + Foshan Metro from Overpass API → GeoJSON + CSV.

Usage:
  python3 scripts/fetch_osm.py           # uses cache when available
  python3 scripts/fetch_osm.py --force   # re-fetches even if cache exists

Outputs:
  data/overpass_raw.json        raw Overpass response (cache, do not edit)
  data/guangzhou_metro.geojson  stations (Point) + line segments (LineString / MultiLineString)
  data/history_template.csv     worksheet with blank opened / closed columns
"""

import csv
import http.client
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict

# SSL context — use certifi on macOS where the stdlib bundle is often missing.
try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl.create_default_context()

# ── Fallback color palette (metro_reference.md; line ref → hex) ───────────────
# Used when an OSM relation carries no colour= tag.
LINE_COLORS_FALLBACK = {
    "1":   "#FDD835",   # yellow
    "2":   "#1E88E5",   # blue
    "3":   "#FB8C00",   # orange
    "4":   "#43A047",   # green
    "5":   "#E53935",   # red
    "6":   "#8E24AA",   # purple
    "7":   "#7CB342",   # lime green
    "8":   "#00897B",   # teal
    "9":   "#00BFA5",   # teal-green
    "13":  "#827717",   # olive
    "14":  "#6D4C41",   # brown
    "18":  "#3949AB",   # indigo
    "21":  "#1A237E",   # dark navy
    "APM": "#00B0FF",   # light blue
    "GF":  "#C0CA33",   # yellow-green  (Guangfo / 广佛线)
    "22":  "#D08693",   # rose — short express line; verify against OSM colour= tag
}

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_PATH   = os.path.join(ROOT, "data", "overpass_raw.json")
GEOJSON_PATH = os.path.join(ROOT, "data", "guangzhou_metro.geojson")
CSV_PATH     = os.path.join(ROOT, "data", "history_template.csv")

# ── Overpass ──────────────────────────────────────────────────────────────────
# Tried in order; first to respond fully wins.
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]
USER_AGENT = "gz-metro-timemap/1.0 (educational project; github.com/user/gz-metro)"

# Constrain by network/operator name — never use a bounding box.
# A bbox covering GZ+Foshan also captures HK MTR, Shenzhen Metro, etc.
# The network/operator regex matches all known tag variants in OSM.
OVERPASS_QUERY = """\
[out:json][timeout:300];
(
  relation["route_master"="subway"]["network"~"广州|广佛|佛山|Guangzhou|Foshan|Guangfo",i];
  relation["route_master"="subway"]["operator"~"广州|佛山|Guangzhou|Foshan",i];
  relation["route"="subway"]["network"~"广州|广佛|佛山|Guangzhou|Foshan|Guangfo",i];
  relation["route"="subway"]["operator"~"广州|佛山|Guangzhou|Foshan",i];
)->.routes;
.routes out body geom;
(
  node(r.routes:"stop");
  node(r.routes:"stop_position");
  node(r.routes:"platform");
);
out body;
"""


# ── Step 1: fetch / cache ─────────────────────────────────────────────────────

def _read_chunked(resp, label=""):
    """Read response in 256 KB chunks; returns bytes. Tolerates IncompleteRead."""
    chunks = []
    while True:
        try:
            chunk = resp.read(262144)
        except http.client.IncompleteRead as exc:
            # Server closed early — keep whatever arrived
            chunks.append(exc.partial)
            break
        if not chunk:
            break
        chunks.append(chunk)
    payload = b"".join(chunks)
    if label:
        print(f"  received {len(payload)//1024} KB from {label}")
    return payload


def fetch_overpass(force=False):
    if not force and os.path.exists(CACHE_PATH):
        print("  cache hit →", CACHE_PATH)
        with open(CACHE_PATH, encoding="utf-8") as fh:
            return json.load(fh)

    print("  querying Overpass API (single batched request, may take 1–3 min)…")
    body = urllib.parse.urlencode({"data": OVERPASS_QUERY}).encode()

    # Try each mirror; within each mirror do up to 3 attempts with backoff.
    last_exc = None
    for endpoint in OVERPASS_ENDPOINTS:
        for attempt in range(3):
            try:
                req = urllib.request.Request(
                    endpoint,
                    data=body,
                    headers={
                        "User-Agent":   USER_AGENT,
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                )
                with urllib.request.urlopen(req, timeout=360, context=_SSL_CTX) as resp:
                    payload = _read_chunked(resp, endpoint)

                raw = json.loads(payload.decode("utf-8"))
                _ensure_dir(CACHE_PATH)
                with open(CACHE_PATH, "w", encoding="utf-8") as fh:
                    json.dump(raw, fh, ensure_ascii=False)
                kb = os.path.getsize(CACHE_PATH) // 1024
                print(f"  saved → {CACHE_PATH}  ({kb} KB)")
                return raw

            except (urllib.error.URLError, OSError, json.JSONDecodeError,
                    http.client.HTTPException) as exc:
                last_exc = exc
                wait = 5 * (2 ** attempt)
                print(f"  {endpoint} attempt {attempt+1}/3 failed: {exc}", file=sys.stderr)
                if attempt < 2:
                    print(f"  retrying in {wait} s…", file=sys.stderr)
                    time.sleep(wait)
        print(f"  giving up on {endpoint}, trying next mirror…", file=sys.stderr)

    sys.exit(f"\nFATAL: All Overpass endpoints failed.\nLast error: {last_exc}")


# ── Step 2: parse ─────────────────────────────────────────────────────────────

def _ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _names(tags):
    """(name_zh, name_en) from an OSM tags dict."""
    zh = (tags.get("name:zh")
          or tags.get("name:zh-Hans")
          or tags.get("name:zh-Hant")
          or tags.get("name", "")).strip()
    en = (tags.get("name:en")
          or tags.get("name", "")).strip()
    return zh, en


def _ref(tags):
    """Normalise line reference string: '1', '2', 'APM', 'GF', …"""
    raw = (tags.get("ref") or tags.get("local_ref") or "").strip()
    raw = raw.replace("Line ", "").replace("号线", "").strip()
    return raw or None


def _color(tags, ref):
    """Return (hex_or_None, source_string)."""
    c = (tags.get("colour") or tags.get("color") or "").strip()
    if c and c.startswith("#") and len(c) in (4, 7):
        return c.upper(), "osm"
    if ref and ref in LINE_COLORS_FALLBACK:
        return LINE_COLORS_FALLBACK[ref], "fallback"
    return None, "missing"


def parse(raw):
    """
    Returns:
      node_index     : {osm_id → {lat, lon, tags}}
      route_masters  : {osm_id → element}
      routes         : {osm_id → element}
    """
    node_index    = {}
    route_masters = {}
    routes        = {}

    for el in raw.get("elements", []):
        t = el.get("type")
        tags = el.get("tags", {})
        if t == "node":
            node_index[el["id"]] = el        # may include lat/lon + tags
        elif t == "relation":
            if tags.get("route_master") == "subway":
                route_masters[el["id"]] = el
            elif tags.get("route") == "subway":
                routes[el["id"]] = el

    return node_index, route_masters, routes


# ── Step 3: build GeoJSON features ───────────────────────────────────────────

def build_features(node_index, route_masters, routes):
    """Returns (line_features, station_features, missing_color_set)."""

    # route relation id → parent route_master id
    route_to_master = {}
    for rm_id, rm in route_masters.items():
        for m in rm.get("members", []):
            if m["type"] == "relation":
                route_to_master[m["ref"]] = rm_id

    # Fallback: if route_masters are absent or incomplete, synthesise a virtual
    # master per unique ref tag so routes on the same line share an rm_osm_id.
    ref_to_synthetic = {}
    for r_id, route in routes.items():
        if r_id not in route_to_master:
            ref = _ref(route.get("tags", {}))
            if ref:
                if ref not in ref_to_synthetic:
                    ref_to_synthetic[ref] = f"synthetic:{ref}"
                route_to_master[r_id] = ref_to_synthetic[ref]

    n_real_masters = len(route_masters)
    n_synthetic    = len(ref_to_synthetic)

    line_features    = []
    missing_colors   = set()        # refs/ids with no color

    # Stations: collect by node id across all routes, then deduplicate
    # station_id → {"lat", "lon", "name_zh", "name_en", "name", "tags", "line_refs"}
    station_map = {}

    for r_id, route in routes.items():
        r_tags  = route.get("tags", {})
        rm_id   = route_to_master.get(r_id)
        rm      = route_masters.get(rm_id) if rm_id else {}
        rm_tags = rm.get("tags", {}) if rm else {}

        # Stable line-level metadata: prefer route_master, fall back to route
        ref             = _ref(rm_tags) or _ref(r_tags)
        zh, en          = _names(rm_tags) if rm_tags.get("name") else _names(r_tags)
        color, col_src  = _color(rm_tags, ref)
        if color is None:
            color, col_src = _color(r_tags, ref)
        if color is None:
            missing_colors.add(ref or f"osm:{r_id}")

        # ── Line geometry ────────────────────────────────────────────────────
        # way members carry geometry embedded by `out geom`
        segments = []
        for m in route.get("members", []):
            if m["type"] == "way" and m.get("geometry"):
                seg = [[pt["lon"], pt["lat"]] for pt in m["geometry"] if "lon" in pt]
                if len(seg) >= 2:
                    segments.append(seg)

        if segments:
            if len(segments) == 1:
                geometry = {"type": "LineString", "coordinates": segments[0]}
            else:
                geometry = {"type": "MultiLineString", "coordinates": segments}

            props = {
                "feature_type": "line",
                "osm_id":       r_id,
                "rm_osm_id":    rm_id,
                "ref":          ref,
                "name_zh":      zh,
                "name_en":      en,
                "color":        color,
                "color_source": col_src,
                "operator":     r_tags.get("operator") or rm_tags.get("operator"),
                "network":      r_tags.get("network")  or rm_tags.get("network"),
                "direction":    r_tags.get("direction") or r_tags.get("name", ""),
                "opened":       None,
                "closed":       None,
            }
            line_features.append({"type": "Feature", "geometry": geometry, "properties": props})

        # ── Station collection ───────────────────────────────────────────────
        for m in route.get("members", []):
            role = m.get("role", "")
            if m["type"] != "node":
                continue
            if role not in ("stop", "stop_position", "platform", "entrance"):
                continue

            node_id = m["ref"]
            node_el = node_index.get(node_id, {})

            # Position: node element (from pass 2) wins; member lat/lon as fallback
            lat = node_el.get("lat") or m.get("lat")
            lon = node_el.get("lon") or m.get("lon")
            if lat is None or lon is None:
                continue

            node_tags = node_el.get("tags", {})

            if node_id not in station_map:
                s_zh, s_en = _names(node_tags)
                station_map[node_id] = {
                    "lat":     lat,
                    "lon":     lon,
                    "name":    node_tags.get("name", ""),
                    "name_zh": s_zh,
                    "name_en": s_en,
                    "railway": node_tags.get("railway", ""),
                    "line_refs": set(),
                }
            if ref:
                station_map[node_id]["line_refs"].add(ref)

    # Drop completely unnamed nodes (pure track waypoints slipped through)
    station_features = []
    for node_id, info in station_map.items():
        if not info["name"] and not info["name_zh"]:
            continue
        props = {
            "feature_type": "station",
            "osm_id":       node_id,
            "name":         info["name"],
            "name_zh":      info["name_zh"],
            "name_en":      info["name_en"],
            "railway":      info["railway"],
            "line_refs":    sorted(info["line_refs"]),
            "opened":       None,
            "closed":       None,
        }
        station_features.append({
            "type":       "Feature",
            "geometry":   {"type": "Point", "coordinates": [info["lon"], info["lat"]]},
            "properties": props,
        })

    return line_features, station_features, missing_colors, n_real_masters, n_synthetic


# ── Step 4: write outputs ─────────────────────────────────────────────────────

def write_geojson(line_features, station_features):
    fc = {
        "type": "FeatureCollection",
        # GeoJSON spec: lon/lat in WGS-84 (default, no CRS needed per RFC 7946,
        # but including for clarity with legacy parsers)
        "features": line_features + station_features,
    }
    _ensure_dir(GEOJSON_PATH)
    with open(GEOJSON_PATH, "w", encoding="utf-8") as fh:
        json.dump(fc, fh, ensure_ascii=False, separators=(",", ":"))
    kb = os.path.getsize(GEOJSON_PATH) // 1024
    print(f"  saved → {GEOJSON_PATH}  ({kb} KB, "
          f"{len(line_features)} line features, {len(station_features)} station features)")


def write_csv(line_features):
    FIELDS = [
        "osm_relation_id",
        "rm_osm_id",
        "line_ref",
        "line_name_zh",
        "line_name_en",
        "direction",
        "color",
        "color_source",
        "opened",     # ← fill from Wikipedia
        "closed",     # ← fill if applicable
        "notes",
    ]

    rows = []
    for feat in line_features:
        p = feat["properties"]
        rows.append({
            "osm_relation_id": p["osm_id"],
            "rm_osm_id":       p["rm_osm_id"] or "",
            "line_ref":        p["ref"] or "",
            "line_name_zh":    p["name_zh"],
            "line_name_en":    p["name_en"],
            "direction":       p["direction"] or "",
            "color":           p["color"] or "",
            "color_source":    p["color_source"],
            "opened":          "",
            "closed":          "",
            "notes":           "",
        })

    # Sort by line ref (numeric where possible), then direction
    def sort_key(r):
        ref = r["line_ref"] or "zz"
        try:
            return (f"{int(ref):04d}", r["direction"])
        except ValueError:
            return (ref, r["direction"])

    rows.sort(key=sort_key)

    _ensure_dir(CSV_PATH)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  saved → {CSV_PATH}  ({len(rows)} rows)")


# ── Summary ───────────────────────────────────────────────────────────────────

def summarise(route_masters, line_features, station_features, missing_colors,
              n_real_masters=0, n_synthetic=0):
    unique_refs = sorted({f["properties"]["ref"] for f in line_features if f["properties"]["ref"]},
                         key=lambda r: (f"{int(r):04d}" if r.isdigit() else r))

    print()
    print("══ Summary " + "═" * 60)
    if n_real_masters:
        print(f"  Route master relations (OSM)   : {n_real_masters}")
    else:
        print(f"  Route master relations (OSM)   : 0  ← none found; used ref-grouping fallback")
    if n_synthetic:
        print(f"  Synthetic masters (by ref tag) : {n_synthetic}")
    print(f"  Route segment features         : {len(line_features)}")
    print(f"  Station features (named, dedup): {len(station_features)}")
    print(f"  Distinct line refs seen        : {', '.join(unique_refs) or '(none)'}")

    if missing_colors:
        print(f"\n  ⚠  Lines with no color match in fallback map ({len(missing_colors)}):")
        for ref in sorted(missing_colors, key=lambda r: (f"{int(r):04d}" if r.isdigit() else r)):
            print(f"       ref={ref!r}  ← add to LINE_COLORS_FALLBACK or check OSM colour= tag")
    else:
        print("\n  ✓  All line segments have a color (osm or fallback).")

    print()
    print("  Next steps:")
    print("    1. Open data/history_template.csv and fill in 'opened'/'closed' from Wikipedia.")
    print("    2. Wire data/guangzhou_metro.geojson into the frontend (replace gz-data.js).")
    print()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    force = "--force" in sys.argv

    print("── [1/4] fetch ──────────────────────────────────────────────────")
    raw = fetch_overpass(force=force)

    total_elements = len(raw.get("elements", []))
    print(f"  {total_elements} elements in raw response")

    print("── [2/4] parse ──────────────────────────────────────────────────")
    node_index, route_masters, routes = parse(raw)
    print(f"  {len(route_masters)} route_master relations, "
          f"{len(routes)} route relations, "
          f"{len(node_index)} stop/platform nodes")

    print("── [3/4] build GeoJSON ──────────────────────────────────────────")
    line_features, station_features, missing_colors, n_real_masters, n_synthetic = build_features(
        node_index, route_masters, routes
    )

    print("── [4/4] write outputs ──────────────────────────────────────────")
    write_geojson(line_features, station_features)
    write_csv(line_features)

    summarise(route_masters, line_features, station_features, missing_colors,
              n_real_masters, n_synthetic)


if __name__ == "__main__":
    main()
