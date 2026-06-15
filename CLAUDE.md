# Guangzhou Metro Time-Map

An interactive, full-viewport web app that replays the growth of the Guangzhou Metro network from its 1997 opening through the present day. The aesthetic is "transit authority archive" — official metro signage crossed with data-journalism interactives (NYT/Reuters style, Vignelli-influenced).

## Goal

Visualise every phase of the Guangzhou Metro's expansion as a zoomable, pannable **MapLibre GL JS map**. A time-slider lets users scrub or play through 30 years of history; lines and stations appear on the map exactly when they opened in real life.

## How to run

```bash
# 1. Build the temporal GeoJSON (requires Python deps)
pip install shapely rapidfuzz pyproj
python3 scripts/build_temporal.py

# 2. Serve the app (ES modules need HTTP, not file://)
python3 -m http.server 8080
```

Then visit `http://localhost:8080`.

## File overview

| File | Purpose |
|------|---------|
| `index.html` | Main entry point — MapLibre map + DC component logic |
| `gz-data.js` | Metro dataset: lines, schematic station coords, opening dates, official colors, events |
| `support.js` | DC runtime — loads React 18 from unpkg, compiles the `<x-dc>` template |
| `scripts/build_temporal.py` | Build script: merges OSM geometry + CSV phases → `data/guangzhou_metro_temporal.geojson` |
| `scripts/fetch_osm.py` | Fetches raw OSM route/station data → `data/guangzhou_metro.geojson` |
| `data/guangzhou_metro.geojson` | Raw OSM geometry (lines + stations, ~4 MB) |
| `data/guangzhou_metro_temporal.geojson` | Built output: time-stamped line chunks + station dots |
| `data/history_template.csv` | Phase opening dates for every line segment |
| `config/station_aliases.json` | Station name overrides + `_ref_fallbacks` for OSM ref lookup |

## Architecture

The app runs on the **DC component system** (see `support.js`). It:

1. Loads React 18 (UMD) from unpkg at runtime
2. Parses the `<x-dc>` HTML block in `index.html` as a reactive template (`{{ }}` interpolation, `<sc-if>`, `<sc-for>`)
3. Evaluates the `<script type="text/x-dc" data-dc-script>` block as the component logic class (`class Component extends DCLogic`)
4. Dynamically imports `gz-data.js` (ES module) for line metadata and sidebar data
5. Loads `data/guangzhou_metro_temporal.geojson` into a MapLibre GL JS source

The component class uses React-style `setState` / `renderVals()` rather than JSX. The MapLibre map is initialised in `buildMap()`; the timeline track in `buildTrack()`.

## Design constraints (do not violate)

- **No gradients, no glassmorphism, no glow effects** — flat surfaces only
- **No saturated color in the UI chrome** — all color comes exclusively from the official metro line palette defined in `gz-data.js`
- **Palette**: warm off-white panels (`#FAFAF7`), ink text (`#1A1A1A`), hairline borders (`#E3E1DA`), desaturated map background (`#E9E7E1`)
- **Typography**: Space Grotesk (headings/numerals), Inter (body), Noto Sans SC (Chinese) — all from Google Fonts
- **Rounded corners**: 10–12 px on panels, fully round on line bullets and slider handle
- **Depth**: one subtle shadow only (`0 1px 3px rgba(0,0,0,0.08)`) plus hairline borders

## Data: `gz-data.js`

Exports:

- `LINE_COLORS` — official hex per line id (authoritative; only lines open as of initial authoring)
- `LINES` — array of line objects, each with `id`, `name_en`, `name_zh`, `color`, `opened` (ISO date), `stations` array, optional `branch` array. **Every line visible in the sidebar or usable via station-chip clicks must be in LINES.** Newer lines (10, 11, 12, 22 …) were added manually once they opened.
- `EVENTS` — notable network milestones for the timeline event markers
- `allDates()` — sorted array of every phase-opening date (utility for the SVG schematic only)

Each station entry is `[en, zh, x, y, openedISO, interchange?]` where `x`/`y` are schematic coordinates in a 1680×1060 SVG space (used by the schematic view, not the MapLibre map).

## Data: `data/guangzhou_metro_temporal.geojson`

Built by `scripts/build_temporal.py`. Two feature kinds:

**Line features** (`kind: "line"`):
```json
{ "kind": "line", "line": "2", "segment": "…", "color": "#1E88E5",
  "opened": 20030628, "closed": 20100925 }
```
- `opened`/`closed` are **YYYYMMDD integers** (not strings). `null` means no close date.
- `closed` is only set for restructure events (Line 2→8, Line 3 branch→10, Line 21→11).

**Station features** (`kind: "station"`):
```json
{ "kind": "station", "name_en": "Changgang", "name_zh": "昌岗",
  "color": "#00897B", "opened": 20100925, "closed": null,
  "_refs": ["2", "8"] }
```
- `color` = the line color of the earliest-opened line chunk within `STN_ASSOC_M` (80 m).
- `_refs` = **sorted list of all line ids** whose chunks pass within 80 m. Required by the station detail panel (`buildDetail()` reads `p._refs || []` to build line chips).
- `closed` is always `null` on station features (stations don't close).

**Temporal filter** in `index.html`:
```js
const openedOk = ['case', ['==', ['get', 'opened'], null], true, ['<=', ['get', 'opened'], d]];
const closedOk = ['case', ['==', ['get', 'closed'],  null], true, ['>', ['get', 'closed'],  d]];
```
where `d` is the current date as a YYYYMMDD integer.

## Build script: `scripts/build_temporal.py`

Algorithm:
1. Load `config/station_aliases.json` (pop `_ref_fallbacks` before treating rest as name aliases).
2. Build station index (`name → [WGS84 Point, …]`) and line index (`ref → [WGS84 geometry, …]`) from OSM GeoJSON.
3. For each CSV phase row: resolve both endpoint names → coordinates, find the best OSM branch within `MAX_SNAP_M` (150 m), slice with `shapely.ops.substring`, emit a line feature.
4. Emit station features: for each OSM station node in the GZ bbox, find all nearby line chunks within `STN_ASSOC_M` (80 m), record `_refs` and minimum-opened line color.

**Key constants:**
```python
MAX_SNAP_M   = 150.0   # max metres for station→branch snap
FUZZY_THRESH = 85      # rapidfuzz token_sort_ratio threshold
STN_ASSOC_M  = 80.0    # radius for station→chunk association
GZ_LON = (112.2, 114.0)
GZ_LAT = (22.0, 23.8)
```

**OSM contamination from Shenzhen/HK** — The OSM extract covers a bbox that includes Shenzhen (lat 22.4–22.8, lon 113.7–114.4). `in_gz_bbox()` applies an extra check: if `lat < 22.85 AND lon > 113.70` → reject. This cleanly excludes Shenzhen metro while keeping GZ Nansha/Foshan routes (all west of 113.70 in that lat band).

**ref_colors (color selection)** — `ref_colors` is pre-seeded with `LINE_COLORS` from `gz-data.js` for all lines with official colors (`_OFFICIAL` set). OSM colors only fill in for newer lines (10, 11, 12, 22 …). This prevents empty-ref reclassified routes (e.g. Knowledge City → ref='14') from overwriting the correct Line 14 brown.

**Knowledge City line** — OSM stores "Subway Line 14 Knowledge City Line" with `ref=''` (empty). The build script reclassifies any line feature with `"Knowledge City" in name_en` to `ref='14'`.

**Multi-branch fallback** — When no single branch has both endpoints within 150 m (e.g. Line 12's disconnected west+east sections), the script finds the nearest primary-ref branch for each endpoint and emits a `MultiLineString`. **Only `primary_branches_utm` (from `osm_ref`, not `_ref_fallbacks`) are searched** to prevent cross-ref geometry leaking (e.g. Line 2 fallback searching Line 8 branches, causing Line 8 to appear in 2002 as Line 2).

**Line 2 / Line 8 restructure** — `_ref_fallbacks: {"2": ["8"]}` is needed so that "Xiaogang – Wanshengwei (pre-restructure Line 2, 2003–2010)" can find the Line 8 geometry in OSM. The `closed: 20100925` on that feature makes it disappear at the restructure date, when the Line 8 features (teal) open. The single-branch match finds both Xiaogang and Wanshengwei on the same Line 8 branch, so no multi-branch fallback triggers. The "Sanyuanli – Xiaogang" 2002 opening is split in the CSV into "Sanyuanli – Changgang" (stays on Line 2 in OSM) + "Changgang – Xiaogang (pre-restructure)" (on Line 8 via fallback, closed 2010).

**Station dedup** — Uses `(name_zh or name_en, int(c[0] * 500), int(c[1] * 500))` as the dedup key, giving ~200 m radius. This prevents duplicate dots at interchange stations whose OSM nodes are spread across multiple platforms.

## Sidebar and station click: what `gz-data.js` `LINES` must contain

The sidebar (`lineRows`) is built directly from `this.LINES`. Any line NOT in `LINES`:
- Does not appear in the sidebar.
- Cannot be found by the station detail panel (`LINES.find(x => x.id === r)` returns null → chip is filtered out).

**Every line that appears in the GeoJSON output must have an entry in LINES** with at least `id`, `name_en`, `name_zh`, `color`, `opened`. The `stations` array can be empty `[]` for lines without schematic positions.

## Key interactions

| Interaction | Behaviour |
|-------------|-----------|
| Drag / click timeline | Scrubs the network to that date |
| Play button | Animates 1997 → present at ~26 s/year |
| Hover event marker (red notch) | Shows tooltip with opening details |
| Click a line in the index | Selects it; map dims other lines; detail panel shows chronology |
| Click a line on the map | Same as above (uses `properties.line` to call `selectLine`) |
| Click a station dot | Detail panel reads `properties._refs` to show line chips |
| Scroll / pinch on map | Zoom to cursor |
| Drag on map | Pan |
| +/–/FIT buttons | Zoom in, zoom out, fit whole network |
| Collapse button (–) | Hides the line index panel |

## Known data gaps / accepted limitations

- **APM Line** and **Haizhu Tram** — no OSM route geometry; skipped in the build output.
- **Line 14 Phase 2 (Jiahewanggang – Lejialu)** — "Lejialu" unmatched in OSM station index; skipped.
- **Line 21 city-centre extension (Zhenlong – Yuancun)** — no OSM branch within 150 m; skipped.
- **Sanyuanli – Xiaogang 2002 original section** — represented as two sub-phases in the CSV: "Sanyuanli – Changgang" (Line 2) and "Changgang – Xiaogang pre-restructure" (Line 2 until 2010, via Line 8 OSM geometry).
- **Line 22 color** — `#D08693` from OSM; verify against official GZ Metro branding.
- **Foshan Metro (F2, F3)** — present in OSM extract but not in the CSV phases; ignored.
