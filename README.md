# Guangzhou Metro Time-Map

An interactive, full-viewport web app that replays the growth of the Guangzhou Metro network from its 1997 opening through the present day.

**[Live demo →](https://frxyoz.github.io/gz-metro)**

---

## What it does

Scrub or play a timeline to watch lines and stations appear on the map exactly when they opened in real life — nearly 30 years of expansion from a single 16-station line to one of the world's largest metro systems.

- Zoomable, pannable [MapLibre GL JS](https://maplibre.org/) map
- Time-slider with play/pause — one full animation covers 1997 → present in ~26 s
- Click any line in the sidebar to highlight it and see its opening chronology
- Click any station on the map to see its lines and interchange status
- Event markers on the timeline for major network milestones

## Running locally

```bash
# 1. Install Python dependencies (only needed to rebuild the GeoJSON)
pip install shapely rapidfuzz pyproj

# 2. Rebuild the temporal GeoJSON from OSM geometry + CSV phase dates
python3 scripts/build_temporal.py

# 3. Serve (ES modules require HTTP, not file://)
python3 -m http.server 8080
```

Then open `http://localhost:8080`.

The pre-built `data/guangzhou_metro_temporal.geojson` is included, so step 2 is only needed if you edit the CSV phases or re-fetch OSM data.

## Project layout

```
index.html                  Main app — MapLibre map + DC component logic
gz-data.js                  Metro dataset: line colors, station schematic coords, opening dates
support.js                  DC runtime (React 18 + reactive template compiler)
data/
  guangzhou_metro.geojson         Raw OSM geometry (~4 MB)
  guangzhou_metro_temporal.geojson  Built output: time-stamped line chunks + station dots
  history_template.csv            Phase opening dates for every line segment
config/
  station_aliases.json            Station name overrides + OSM ref fallbacks
scripts/
  build_temporal.py         Merges OSM geometry + CSV → temporal GeoJSON
  fetch_osm.py              Fetches raw OSM route/station data
```

## Data sources

- **OSM geometry** — route and station node data from OpenStreetMap via [Overpass API](https://overpass-api.de/), filtered to the Guangzhou metro bounding box
- **Opening dates** — `data/history_template.csv`, compiled from official GZ Metro press releases and Wikipedia
- **Official line colors** — `gz-data.js` `LINE_COLORS`, cross-referenced with physical signage

## How the build works

`scripts/build_temporal.py` takes the raw OSM GeoJSON and the CSV of phase opening dates and produces a single GeoJSON with two feature kinds:

**Line features** — each CSV row (e.g. "Xilang – Kengkou, Line 1, 1997-06-28") is resolved to a sliced segment of the OSM route geometry. Properties include `opened` and `closed` as YYYYMMDD integers so the MapLibre filter `['<=', ['get', 'opened'], d]` can show/hide features by date.

**Station features** — each OSM station node within 80 m of any output line chunk is emitted as a dot. `_refs` lists every line passing within 80 m; `opened` is the earliest of those lines. Stations with multiple OSM nodes (different platform levels, exits) are merged by name so each station appears as a single dot with complete interchange information.

The temporal filter in `index.html`:
```js
const d = yyyymmddInt(iso);
const openedOk = ['case', ['==', ['get', 'opened'], null], true, ['<=', ['get', 'opened'], d]];
const closedOk = ['case', ['==', ['get', 'closed'],  null], true, ['>', ['get', 'closed'],  d]];
```

## Known gaps

| Item | Status |
|------|--------|
| APM Line, Haizhu Tram | No OSM route geometry — skipped |
| Line 14 Phase 2 (Jiahewanggang – Lejialu) | "Lejialu" unmatched in OSM — skipped |
| Line 21 city-centre extension (Zhenlong – Yuancun) | No OSM branch within 150 m — skipped |
| Foshan Metro (F2, F3) | In OSM extract but not in CSV phases — ignored |

## License

Data derived from [OpenStreetMap](https://www.openstreetmap.org/) contributors, © OpenStreetMap contributors ([ODbL](https://opendatacommons.org/licenses/odbl/)). Code MIT.
