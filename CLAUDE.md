# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MGT TTT (Mongoose Traveller 2e Trade Tool) is a Python CLI application that generates passenger, trade, and freight data for the Mongoose Traveller 2e tabletop RPG. It fetches live world data from the [travellermap.com](https://travellermap.com) API and applies MGT2e game mechanics (2d6 dice rolls with hex-coded modifiers).

## Commands

```bash
# Run the application (note: hits the live travellermap.com API on every run)
python main.py

# Generate a single world surface map without running the full app
python worldMap.py C566662-7 tarkine.png

# Install dependencies
pip install -r requirements.txt

# Lint (mirrors CI checks)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Run tests (no tests exist yet — pytest will collect 0 items and exit 5)
pytest

# Run a single test once tests are added
pytest path/to/test_file.py::test_name
```

CI (`.github/workflows/python-app.yml`) runs on Python 3.10 and triggers on push and pull-request to `main` only — other branches do not run CI. `requirements.txt` exists and CI installs from it; runtime deps are `requests` and `Pillow`. CI installs `flake8` and `pytest` separately.

## Architecture

The app has three Python source files and two JSON data files. There is no package/module structure — everything runs as top-level scripts in the repo root.

- **`api_calls.py`** — Exposes `fetch_jump_worlds(sector, hex_id, jump) -> dict`. The URL is `https://travellermap.com/data/{sector}/{hex}/jump/{distance}`; sector is URL-encoded. Response shape is `{"Worlds": [{...}, ...]}` where each world has `Name`, `Hex`, `UWP`, `Bases`, `Zone`, `Remarks`, `Allegiance`, `Sector`, `SubsectorName`, etc. `DEFAULT_SECTOR`/`DEFAULT_HEX`/`DEFAULT_JUMP` constants hold the values previously hard-coded at import time. `python api_calls.py` runs a sample request.

- **`main.py`** — Calls `api_calls.fetch_jump_worlds(...)`, loads the two JSON files, parses the UWP string (positional character offsets: index 0=Starport, 1=Size, 2=Atmo, 3=Hydro, 4=Pop, 5=Gov, 6=Law, 8=TL), looks up starport berthing costs, calculates hex-grid distances between worlds, prints a formatted world summary, and writes a surface map PNG via `worldMap.generate_world_map`. Only ever inspects `worlds["Worlds"][0]` — it does not iterate the full result set.

- **`worldMap.py`** — Generates an icosahedral world surface map for a UWP. `generate_world_map(uwp, out_path=None, seed=None) -> PIL.Image.Image`. Renders the unfolded 20-triangle icosahedron as two horizontal zigzag strips, subdivides each face into N² small terrain cells (N scales with UWP Size: 4/6/8/10), and chooses cell terrain via fractal value noise seeded by the UWP. Hydrographics sets the water-area fraction (threshold picked to match exactly, via sorted-noise indexing). Atmosphere selects the palette (breathable / dusty / vacuum / exotic / corrosive). A "big hex" labelled with km-per-cell-edge, color swatches, and the world's UWP stats are drawn below the map. Same UWP always yields the same image (`seed` defaults to a SHA-256 hash of the UWP). The 2-strip layout means polar ice manifests as zigzag bands along the top/bottom edges rather than triangular caps — that's the layout's projection artifact, not a bug. Runnable: `python worldMap.py <UWP> [out.png]`.

- **`gameSys.json`** — MGT2e lookup tables: `diceModStd` (hex digit → dice modifier, values 0–F → −3 to +3) and `taskEffectMod` (task roll result → effect modifier). Uses C-style `/* */` comments which are not valid JSON — use a comment-tolerant parser or strip comments before loading.

- **`worldTables.json`** — Starport class definitions (`Berthing` formula `"1d6*N"`, fuel type, facilities), TAS travel zones (Amber/Red as `tasZones`), and system base codes (`systemBases`). The `tasZones` and `systemBases` blocks are what should back the missing `worldZones_dict` and `worldBases_dict` in `main.py`. Also contains C-style comments and uses `=` instead of `:` in two places (`"tasZones" =` and `"systemBases" =`) — the file has syntax errors that must be fixed before it can be parsed.

- **`TravellerMapAPIOutput`** — Not code. A scratch reference file containing example API URLs, raw JSON payloads, and Python prototypes. Useful for understanding the data shape without making a live API call. Do not import from it.

### Data Duplication to Watch For

The starport class table is currently defined **twice**: as a hard-coded JSON string `starPortInfo` at `main.py:16`, and again in `worldTables.json`. Only the string in `main.py` is actually used at runtime (parsed into `starports` on line 23); the `Starport` block in `worldTables.json` is loaded into `WorldTables` but never read. When fixing the JSON parsing issues, plan to consolidate these.

## Known Issues to Be Aware Of

1. **`gameSys.json` and `worldTables.json`** both contain C-style `/* */` comments and `worldTables.json` uses `=` instead of `:` for two keys — standard `json.load()` will fail on both. These need to be fixed (remove comments, fix `=` → `:`) before the JSON loaders work. CI lint passes because flake8 doesn't validate JSON, but `python main.py` crashes immediately on the `open('gameSys.json')` call.

2. **`worldZones_dict` and `worldBases_dict`** are referenced in `main.py` but never defined — the app will raise `NameError` at runtime. These need to be built from the `tasZones` and `systemBases` arrays in `worldTables.json` after that file is fixed.

3. **Berthing cost randomisation** in `main.py` reads `berthingRange.split('*')[1]` — works for classes A–D whose formula is `"1d6*N"`, but starport classes E (`"Free"`) and X (`"-"`) will raise `IndexError`/`ValueError`. Needs a branch for non-formula berthing values.

## Data Model

UWP (Universal World Profile) is a 9-character string like `"C566662-7"`. Positions are:
```
[0] Starport class (A/B/C/D/E/X)
[1] World size      (0–9, A)
[2] Atmosphere      (0–9, A–F)
[3] Hydrographics   (0–9, A)
[4] Population      (0–9, A–C)
[5] Government      (0–9, A–F)
[6] Law level       (0–9, A–L)
[7] dash separator
[8] Tech level      (0–9, A–F)
```

Hex coordinates use a 4-digit `XXYY` format (e.g. `"1433"`). The `hex_distance` function in `main.py` computes Chebyshev distance on an offset grid (`max(|Δq|, |Δr|, |Δq+Δr|)` on `q=XX, r=YY`).
