#!/usr/bin/env python3
"""
scripts/build_temporal.py
Merge data/guangzhou_metro.geojson (OSM geometry) + data/history_template.csv
(phase opening dates) → data/guangzhou_metro_temporal.geojson.

Algorithm:
  For each CSV phase row (line, "StationA – StationB", opened, closed):
    1. Fuzzy-match both endpoint station names against the OSM station index.
    2. Find the OSM route geometry (by ref) where both matched station points
       project within MAX_SNAP_M metres of the line.
    3. Slice that geometry between the two projected measures.
    4. Emit a line Feature with opened/closed as YYYYMMDD ints (null if absent).
  Station features: emit each OSM station point whose opened date is the
  minimum of any output line chunk within STN_ASSOC_M metres.

Usage:
    pip install shapely rapidfuzz pyproj
    python3 scripts/build_temporal.py
"""

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# ── Dependency checks ─────────────────────────────────────────────────────────
try:
    from shapely.geometry import Point, shape, mapping
    from shapely.ops import substring, transform, linemerge
except ImportError:
    sys.exit("Missing dependency: pip install shapely")

try:
    from rapidfuzz import process as rfprocess, fuzz as rfuzz
except ImportError:
    sys.exit("Missing dependency: pip install rapidfuzz")

try:
    import pyproj
    _T_WGS_UTM = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32649", always_xy=True)
    _T_UTM_WGS = pyproj.Transformer.from_crs("EPSG:32649", "EPSG:4326", always_xy=True)
except ImportError:
    sys.exit("Missing dependency: pip install pyproj")

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parent.parent
GEO_IN   = ROOT / "data" / "guangzhou_metro.geojson"
CSV_IN   = ROOT / "data" / "history_template.csv"
ALIAS_IN = ROOT / "config" / "station_aliases.json"
GEO_OUT  = ROOT / "data" / "guangzhou_metro_temporal.geojson"

# ── Constants ─────────────────────────────────────────────────────────────────
# CSV "line" field → OSM ref mapping (where they differ)
CSV_LINE_TO_OSM = {"Guangfo": "GF", "APM": "APM", "Haizhu Tram": "HZT"}

# Colour fallback — lines in gz-data.js LINE_COLORS are authoritative;
# newer lines (10, 11, 12, 16, 20, 22) use confirmed GZ OSM colours where known.
FALLBACK_COLORS: dict[str, str] = {
    "1": "#FDD835", "2": "#1E88E5", "3": "#FB8C00", "4": "#43A047",
    "5": "#E53935", "6": "#8E24AA", "7": "#7CB342", "8": "#00897B",
    "9": "#00BFA5", "10": "#7389B2", "11": "#FAC525", "12": "#435428",
    "13": "#827717", "14": "#6D4C41", "16": "#EC407A", "18": "#3949AB",
    "20": "#26C6DA", "21": "#1A237E", "22": "#CD5228",
    "GF": "#C0CA33", "APM": "#00B0FF",
}

MAX_SNAP_M   = 150.0   # max metres for station → branch snap
FUZZY_THRESH = 85      # rapidfuzz score threshold (0–100)
STN_ASSOC_M  = 80.0    # radius for station→phase-chunk association

# Bounding box covering Guangzhou + Foshan metro (excludes HK / Shenzhen / Dongguan)
GZ_LON = (112.2, 114.0)
GZ_LAT = (22.0, 23.8)


# ── Projection helpers ────────────────────────────────────────────────────────
def _to_utm(geom):
    return transform(_T_WGS_UTM.transform, geom)


def _to_wgs84(geom):
    return transform(_T_UTM_WGS.transform, geom)


# ── Parsing helpers ───────────────────────────────────────────────────────────
def parse_date(s: str):
    """'1997-06-28' or '19970628' → 19970628. Blank/invalid → None."""
    s = (s or "").strip()
    if not s:
        return None
    s = s.replace("-", "")
    return int(s) if len(s) == 8 and s.isdigit() else None


def clean_name(raw: str) -> str:
    """Strip trailing parenthetical annotations from a station name."""
    return re.sub(r"\s*\([^)]*\)", "", raw).strip()


def parse_segment(seg: str):
    """'StationA – StationB' → ('StationA', 'StationB').
    Returns (None, None) for full-circle or single-token special cases."""
    seg = seg.strip()
    if re.search(r"full\s+circle|loop\s+line", seg, re.I):
        return None, None
    for sep in (" – ", " — ", " - ", " - "):
        if sep in seg:
            a, b = seg.split(sep, 1)
            return clean_name(a), clean_name(b)
    return seg, None


# ── Geometry helpers ──────────────────────────────────────────────────────────
def flatten_to_linestrings(geom) -> list:
    """Recursively flatten a shapely geometry to a list of LineStrings."""
    if geom.geom_type == "LineString":
        return [geom]
    if geom.geom_type == "MultiLineString":
        merged = linemerge(geom)
        if merged.geom_type == "LineString":
            return [merged]
        return list(merged.geoms)
    return []


def in_gz_bbox(geom) -> bool:
    """True if the geometry's centroid falls within the GZ metro bounding box.
    The conditional excludes Shenzhen Metro (lat ~22.4–22.85, lon ~113.70–114.40)
    while preserving GZ Nansha/Foshan routes in that lat band (all west of 113.70)."""
    c = geom.centroid
    lon, lat = c.x, c.y
    if not (GZ_LON[0] <= lon <= GZ_LON[1] and GZ_LAT[0] <= lat <= GZ_LAT[1]):
        return False
    if lat < 22.85 and lon > 113.70:
        return False
    return True


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    if not GEO_IN.exists():
        sys.exit(f"FATAL: {GEO_IN} not found — run scripts/fetch_osm.py first")
    if not CSV_IN.exists():
        sys.exit(f"FATAL: {CSV_IN} not found")

    # ── Load aliases ──────────────────────────────────────────────────────────
    aliases: dict[str, str] = {}
    ref_fallbacks: dict[str, list] = {}
    if ALIAS_IN.exists():
        with open(ALIAS_IN) as f:
            raw = json.load(f)
        ref_fallbacks = raw.pop("_ref_fallbacks", {})
        aliases = raw

    # ── Load OSM GeoJSON ──────────────────────────────────────────────────────
    with open(GEO_IN, encoding="utf-8") as f:
        fc = json.load(f)

    osm_line_feats = [x for x in fc["features"] if x["properties"].get("feature_type") == "line"]
    osm_stn_feats  = [x for x in fc["features"] if x["properties"].get("feature_type") == "station"]

    # ── Station index: name → list of WGS84 Points ───────────────────────────
    stn_idx: dict[str, list] = defaultdict(list)
    for feat in osm_stn_feats:
        c = feat["geometry"]["coordinates"]
        pt = Point(c[0], c[1])
        for key in (feat["properties"].get("name_en"),
                    feat["properties"].get("name_zh"),
                    feat["properties"].get("name")):
            if key and key.strip():
                stn_idx[key.strip()].append(pt)

    all_stn_names = list(stn_idx.keys())

    # ── Line geometry index: OSM ref → list of WGS84 geometries ──────────────
    ref_geoms: dict[str, list] = defaultdict(list)
    # Pre-seed with official gz-data.js colors for known lines so that reclassified
    # empty-ref features (e.g. Knowledge City → '14') cannot overwrite them.
    _OFFICIAL = {"1","2","3","4","5","6","7","8","9","10","11","12","13","14","18","21","22","APM","GF"}
    ref_colors: dict[str, str] = {k: v for k, v in FALLBACK_COLORS.items() if k in _OFFICIAL}
    for feat in osm_line_feats:
        p       = feat["properties"]
        ref     = str(p.get("ref") or "")
        name_en = (p.get("name_en") or "").strip()

        # Reclassify Knowledge City line (OSM stores it with empty ref)
        if not ref and "Knowledge City" in name_en:
            ref = "14"
        elif not ref:
            ref = "?"

        g = shape(feat["geometry"])
        ref_geoms[ref].append(g)

        # Populate ref_colors only from GZ-area routes so SZ/HK colors don't win
        if p.get("color") and ref not in ref_colors:
            cen = g.centroid
            clon, clat = cen.x, cen.y
            if (GZ_LON[0] <= clon <= GZ_LON[1] and GZ_LAT[0] <= clat <= GZ_LAT[1]
                    and not (clat < 22.85 and clon > 113.70)):
                ref_colors[ref] = p["color"]

    def get_color(osm_ref: str, csv_line: str) -> str:
        return (ref_colors.get(osm_ref)
                or FALLBACK_COLORS.get(osm_ref)
                or FALLBACK_COLORS.get(csv_line)
                or "#888888")

    # ── Name resolution ───────────────────────────────────────────────────────
    def resolve(name: str):
        """Returns (points_list, matched_name, method_str). Empty list = unmatched.
        Alias values starting with '@' are parsed as '@lon,lat' coordinate literals."""
        resolved = aliases.get(name, name)
        method_pfx = "alias+" if resolved != name else ""
        # Coordinate-literal alias: "@lon,lat"
        if isinstance(resolved, str) and resolved.startswith("@"):
            try:
                lon, lat = resolved[1:].split(",")
                return [Point(float(lon), float(lat))], name, method_pfx + "coord"
            except Exception:
                pass
        pts = stn_idx.get(resolved)
        if pts:
            return pts, resolved, method_pfx + "exact"
        hit = rfprocess.extractOne(resolved, all_stn_names, scorer=rfuzz.token_sort_ratio)
        if hit and hit[1] >= FUZZY_THRESH:
            return stn_idx[hit[0]], hit[0], method_pfx + f"fuzzy({hit[1]:.0f})"
        return [], resolved, "UNMATCHED"

    # ── Load CSV ──────────────────────────────────────────────────────────────
    phases: list[dict] = []
    with open(CSV_IN, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if (row.get("opened") or "").strip():
                phases.append(row)

    # ── Process phases ────────────────────────────────────────────────────────
    out_line_feats: list[dict] = []

    rpt: dict = dict(
        total=len(phases), matched=0,
        skip_no_geom=[], skip_dist=[], skip_name=[],
        aliases_used=[], fuzzies=[],
    )

    for row in phases:
        csv_line = row["line"].strip()
        segment  = row["segment"].strip()
        opened   = parse_date(row.get("opened", ""))
        closed   = parse_date(row.get("closed", ""))
        osm_ref  = CSV_LINE_TO_OSM.get(csv_line, csv_line)
        color    = get_color(osm_ref, csv_line)

        start_name, end_name = parse_segment(segment)

        # ── Full-circle / whole-line special case ─────────────────────────
        if start_name is None:
            raw_geoms = ref_geoms.get(osm_ref, [])
            branches  = []
            for g in raw_geoms:
                for b in flatten_to_linestrings(g):
                    if in_gz_bbox(b):
                        branches.append(b)
            if not branches:
                rpt["skip_no_geom"].append(f"line={csv_line} seg={segment!r}")
                continue
            best = max(branches, key=lambda b: b.length)
            out_line_feats.append({
                "type": "Feature",
                "geometry": mapping(best),
                "properties": {"kind": "line", "line": osm_ref,
                               "segment": segment, "color": color,
                               "opened": opened, "closed": closed},
            })
            rpt["matched"] += 1
            continue

        # ── Normal two-endpoint segment ───────────────────────────────────
        start_pts, start_m, start_how = resolve(start_name)
        end_pts,   end_m,   end_how   = resolve(end_name)

        for orig, matched, how in [(start_name, start_m, start_how),
                                   (end_name,   end_m,   end_how)]:
            if "alias" in how:
                rpt["aliases_used"].append(f"'{orig}' → '{matched}' ({how})")
            elif "fuzzy" in how:
                rpt["fuzzies"].append(f"'{orig}' → '{matched}' ({how})")

        if not start_pts or not end_pts:
            missing = [n for n, p in [(start_name, start_pts), (end_name, end_pts)] if not p]
            rpt["skip_name"].append(
                f"line={csv_line} seg={segment!r}: unmatched {missing}"
            )
            continue

        # Collect GZ-area branches: primary ref + any configured fallback refs
        # primary_branches_wgs = only from osm_ref (used for multi-branch fallback
        # to prevent cross-ref geometry leaking across restructured lines, e.g. L2+L8)
        search_refs = [osm_ref] + list(ref_fallbacks.get(csv_line, []))
        primary_branches_wgs: list = []
        all_branches_wgs: list = []
        for ref in search_refs:
            for g in ref_geoms.get(ref, []):
                for b in flatten_to_linestrings(g):
                    if in_gz_bbox(b):
                        all_branches_wgs.append(b)
                        if ref == osm_ref:
                            primary_branches_wgs.append(b)

        if not all_branches_wgs:
            rpt["skip_no_geom"].append(f"line={csv_line} seg={segment!r}")
            continue

        all_branches_utm     = [_to_utm(b) for b in all_branches_wgs]
        primary_branches_utm = [_to_utm(b) for b in primary_branches_wgs]

        # Find best (branch, start_point, end_point) triple by min total snap distance
        best_result = None
        best_score  = float("inf")

        for pt_a in start_pts:
            pt_a_utm = _to_utm(pt_a)
            for pt_b in end_pts:
                pt_b_utm = _to_utm(pt_b)
                for branch_utm in all_branches_utm:
                    da = branch_utm.distance(pt_a_utm)
                    db = branch_utm.distance(pt_b_utm)
                    if max(da, db) > MAX_SNAP_M:
                        continue
                    score = da + db
                    if score < best_score:
                        best_score  = score
                        best_result = (branch_utm, pt_a_utm, pt_b_utm)

        if best_result is None:
            # Multi-branch fallback: if each endpoint is on a DIFFERENT primary-ref
            # branch within MAX_SNAP_M, emit the two closest branches as MultiLineString.
            # Deliberately uses only primary_branches_utm (not fallback refs) so that
            # restructured lines (e.g. Line 2 fallback refs Line 8) don't bleed geometry
            # from the other line into this phase's emission.
            best_start_b, best_start_d = None, float("inf")
            best_end_b,   best_end_d   = None, float("inf")
            for pt_a in start_pts:
                pt_a_utm = _to_utm(pt_a)
                for b in primary_branches_utm:
                    d = b.distance(pt_a_utm)
                    if d < best_start_d:
                        best_start_d = d; best_start_b = b
            for pt_b in end_pts:
                pt_b_utm = _to_utm(pt_b)
                for b in primary_branches_utm:
                    d = b.distance(pt_b_utm)
                    if d < best_end_d:
                        best_end_d = d; best_end_b = b

            if (best_start_d <= MAX_SNAP_M and best_end_d <= MAX_SNAP_M
                    and best_start_b is not None and best_start_b is not best_end_b):
                from shapely.geometry import MultiLineString as MLStr
                # Emit only the two specific closest branches, not all branches
                pair = MLStr([list(_to_wgs84(b).coords)
                              for b in [best_start_b, best_end_b]])
                out_line_feats.append({
                    "type": "Feature",
                    "geometry": mapping(pair),
                    "properties": {"kind": "line", "line": osm_ref,
                                   "segment": segment, "color": color,
                                   "opened": opened, "closed": closed},
                })
                rpt["matched"] += 1
                continue

            rpt["skip_dist"].append(
                f"line={csv_line} seg={segment!r}: "
                f"no branch within {MAX_SNAP_M}m "
                f"(start_candidates={len(start_pts)}, end_candidates={len(end_pts)}, "
                f"branches={len(all_branches_utm)})"
            )
            continue

        branch_utm, pa_utm, pb_utm = best_result
        ma = branch_utm.project(pa_utm)
        mb = branch_utm.project(pb_utm)
        sliced_utm = substring(branch_utm, min(ma, mb), max(ma, mb))

        if sliced_utm.is_empty or sliced_utm.length < 1.0:
            rpt["skip_dist"].append(f"line={csv_line} seg={segment!r}: degenerate slice")
            continue

        out_line_feats.append({
            "type": "Feature",
            "geometry": mapping(_to_wgs84(sliced_utm)),
            "properties": {"kind": "line", "line": osm_ref,
                           "segment": segment, "color": color,
                           "opened": opened, "closed": closed},
        })
        rpt["matched"] += 1

    # ── Station features ──────────────────────────────────────────────────────
    # Pre-build UTM versions of all output line chunks
    chunk_data: list[tuple] = []
    for feat in out_line_feats:
        g_utm = _to_utm(shape(feat["geometry"]))
        chunk_data.append((g_utm, feat["properties"]["opened"],
                           feat["properties"]["color"], feat["properties"]["line"]))

    out_stn_feats: list[dict] = []
    seen_stn: dict = {}  # name_key → feature dict (for merging refs across OSM nodes)

    for feat in osm_stn_feats:
        p      = feat["properties"]
        name_en = (p.get("name_en") or "").strip()
        name_zh = (p.get("name_zh") or "").strip()
        if not (name_en or name_zh):
            continue

        c   = feat["geometry"]["coordinates"]
        # Skip stations outside GZ metro bbox
        if not (GZ_LON[0] <= c[0] <= GZ_LON[1] and GZ_LAT[0] <= c[1] <= GZ_LAT[1]):
            continue

        pt_utm = _to_utm(Point(c[0], c[1]))

        min_opened = None
        stn_color  = "#888888"
        nearby_refs: set = set()

        for chunk_geom, chunk_opened, chunk_color, chunk_line in chunk_data:
            if chunk_geom.distance(pt_utm) <= STN_ASSOC_M:
                nearby_refs.add(chunk_line)
                if chunk_opened and (min_opened is None or chunk_opened < min_opened):
                    min_opened = chunk_opened
                    stn_color  = chunk_color or stn_color

        if min_opened is None:
            continue  # station not near any output phase chunk

        # Deduplicate by station name — merge _refs when the same station name
        # appears from multiple OSM nodes (platform nodes, separate exits, etc.)
        dedup_name = name_zh or name_en
        if dedup_name in seen_stn:
            ep = seen_stn[dedup_name]["properties"]
            ep["_refs"] = sorted(set(ep["_refs"]) | nearby_refs)
            if min_opened < ep["opened"]:
                ep["opened"] = min_opened
                ep["color"]  = stn_color
            continue

        new_feat = {
            "type": "Feature",
            "geometry": feat["geometry"],
            "properties": {
                "kind":    "station",
                "name":    p.get("name") or "",
                "name_en": name_en,
                "name_zh": name_zh,
                "color":   stn_color,
                "opened":  min_opened,
                "closed":  None,
                "_refs":   sorted(nearby_refs),
            },
        }
        out_stn_feats.append(new_feat)
        seen_stn[dedup_name] = new_feat

    # ── Write output ──────────────────────────────────────────────────────────
    out_fc = {"type": "FeatureCollection",
              "features": out_line_feats + out_stn_feats}
    GEO_OUT.parent.mkdir(exist_ok=True)
    with open(GEO_OUT, "w", encoding="utf-8") as f:
        json.dump(out_fc, f, ensure_ascii=False, separators=(",", ":"))

    kb = GEO_OUT.stat().st_size // 1024

    # ── Report ────────────────────────────────────────────────────────────────
    all_opened = sorted(set(
        f["properties"]["opened"]
        for f in out_line_feats
        if f["properties"]["opened"] is not None
    ))
    width = 78
    print()
    print("══ build_temporal report " + "═" * (width - 25))
    print(f"  CSV phases (with dates)        : {rpt['total']}")
    print(f"  Phases matched + sliced        : {rpt['matched']}")
    print(f"  Line features written          : {len(out_line_feats)}")
    print(f"  Station features written       : {len(out_stn_feats)}")
    print(f"  Output                         : {GEO_OUT.name}  ({kb} KB)")
    if all_opened:
        print(f"  Date range                     : {all_opened[0]} → {all_opened[-1]}")

    if rpt["aliases_used"]:
        print(f"\n  Aliases applied ({len(rpt['aliases_used'])}):")
        for a in sorted(set(rpt["aliases_used"])):
            print(f"    {a}")

    if rpt["fuzzies"]:
        print(f"\n  Fuzzy name resolutions ({len(rpt['fuzzies'])}):")
        for a in sorted(set(rpt["fuzzies"])):
            print(f"    {a}")

    if rpt["skip_name"]:
        print(f"\n  ⚠  Skipped — station name unmatched ({len(rpt['skip_name'])}):")
        for s in rpt["skip_name"]:
            print(f"    {s}")

    if rpt["skip_dist"]:
        print(f"\n  ⚠  Skipped — projection > {MAX_SNAP_M}m or degenerate ({len(rpt['skip_dist'])}):")
        for s in rpt["skip_dist"]:
            print(f"    {s}")

    if rpt["skip_no_geom"]:
        print(f"\n  ⚠  Skipped — no OSM geometry for line ({len(rpt['skip_no_geom'])}):")
        for s in rpt["skip_no_geom"]:
            print(f"    {s}")

    print()


if __name__ == "__main__":
    main()
