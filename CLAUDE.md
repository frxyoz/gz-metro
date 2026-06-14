2# Guangzhou Metro Time-Map

An interactive, full-viewport web app that replays the growth of the Guangzhou Metro network from its 1997 opening through the present day. The aesthetic is "transit authority archive" — official metro signage crossed with data-journalism interactives (NYT/Reuters style, Vignelli-influenced).

## Goal

Visualise every phase of the Guangzhou Metro's expansion as a zoomable, pannable schematic diagram. A time-slider lets users scrub or play through 30 years of history; lines and stations appear on the map exactly when they opened in real life.

## How to run

Open `index.html` from a local HTTP server (ES module imports require a server, not `file://`):

```bash
npx serve .
# or
python3 -m http.server 8080
```

Then visit `http://localhost:8080`.

## File overview

| File | Purpose |
|------|---------|
| `index.html` | Main entry point — full app (template + React component logic) |
| `gz-data.js` | Metro dataset: every line, every station, phase-level opening dates, official colors, notable events |
| `support.js` | DC runtime — loads React 18 from unpkg, compiles the `<x-dc>` template, mounts the app |

## Architecture

The app runs on the **DC component system** (see `support.js`). It:

1. Loads React 18 (UMD) from unpkg at runtime
2. Parses the `<x-dc>` HTML block in `index.html` as a reactive template (`{{ }}` interpolation, `<sc-if>`, `<sc-for>`)
3. Evaluates the `<script type="text/x-dc" data-dc-script>` block as the component logic class (`class Component extends DCLogic`)
4. Dynamically imports `gz-data.js` (ES module) for the metro dataset

The component class uses React-style `setState` / `renderVals()` rather than JSX. The SVG map and timeline track are built imperatively with `React.createElement` in `buildMap()` and `buildTrack()`.

## Design constraints (do not violate)

- **No gradients, no glassmorphism, no glow effects** — flat surfaces only
- **No saturated color in the UI chrome** — all color comes exclusively from the official metro line palette defined in `gz-data.js`
- **Palette**: warm off-white panels (`#FAFAF7`), ink text (`#1A1A1A`), hairline borders (`#E3E1DA`), desaturated map background (`#E9E7E1`)
- **Typography**: Space Grotesk (headings/numerals), Inter (body), Noto Sans SC (Chinese) — all from Google Fonts
- **Rounded corners**: 10–12 px on panels, fully round on line bullets and slider handle
- **Depth**: one subtle shadow only (`0 1px 3px rgba(0,0,0,0.08)`) plus hairline borders

## Data

`gz-data.js` exports:

- `LINES` — array of line objects, each with `id`, `name_en`, `name_zh`, `color` (hex), `opened` (ISO date), `stations` array, optional `branch` array
- `EVENTS` — notable network milestones for the timeline event markers
- `allDates()` — sorted array of every phase-opening date (utility)

Each station entry is `[en, zh, x, y, openedISO, interchange?]` where `x`/`y` are schematic coordinates in a 1680×1060 SVG space.

## Key interactions

| Interaction | Behaviour |
|-------------|-----------|
| Drag / click timeline | Scrubs the network to that date |
| Play button | Animates 1997 → present at ~26 s/year |
| Hover event marker (red notch) | Shows tooltip with opening details |
| Click a line in the index | Selects it; map dims other lines; detail panel shows chronology |
| Click a line on the map | Same as above |
| Click a station dot | Detail panel shows that station's line-by-line history |
| Scroll / pinch on map | Zoom to cursor |
| Drag on map | Pan |
| +/–/FIT buttons | Zoom in, zoom out, fit whole network |
| Collapse button (–) | Hides the line index panel |
