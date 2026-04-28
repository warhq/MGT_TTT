# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MGT TTT (Mongoose Traveller 2e Trade Tool) generates passenger, trade, and freight data for the Mongoose Traveller 2e tabletop RPG. It fetches live world data from the [travellermap.com](https://travellermap.com) API and applies MGT2e game mechanics (2d6 dice rolls with hex-coded modifiers). It runs as both a CLI (`main.py`) and a Flask web app (`app.py`).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the CLI
python main.py

# Run the web interface
python app.py        # serves on http://127.0.0.1:5000

# Lint (mirrors CI checks)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Run tests
pytest
```

CI runs on Python 3.10.

## Architecture

### Source files

- **`api_calls.py`** — `fetch_worlds(sector, hex_code, jump_distance)` makes a GET to `https://travellermap.com/data/{sector}/{hex}/jump/{distance}` and returns a flat list of world dicts. All failure modes (connection error, timeout, HTTP error, bad JSON) print a message and return `[]`. Each world dict is the single working record for that world — app-generated data is added as new keys on the same dict.

- **`world_data.py`** — Shared processing layer used by both `main.py` and `app.py`.
  - `load_tables(path)` — loads `worldTables.json`, returns `{'starports': ..., 'zones': ..., 'bases': ...}`
  - `process_world(world, origin_hex, tables)` — enriches a world dict in-place with `uwp_parsed`, `starport_detail` (including rolled berthing cost), `zone_description`, `base_description`, `jump_distance`, and `passengers` (counts, revenue, per-type breakdown). Returns the same dict.

- **`passengers.py`** — One 2d6 availability roll per passage type (High/Middle/Basic/Low), modified by starport class and UWP population digit. `find_passengers(starport, pop, jump)` returns `(counts_dict, total_revenue)`. Table values (`POPULATION_DM`, `PASSAGE_TYPE_DM`, `AVAILABILITY_TABLE`) are marked for verification against the rulebook.

- **`main.py`** — CLI entry point. Fetches worlds, processes `worlds[0]`, prints a formatted summary.

- **`app.py`** — Flask web interface. `GET /` shows the search form; `POST /` fetches and processes all worlds in range, renders them via `templates/index.html`. Tables are loaded once at startup into `_tables`.

### Data files

- **`gameSys.json`** — MGT2e lookup tables: `diceModStd` (hex digit → DM, 0–F → −3 to +3) and `taskEffectMod` (task roll result → effect modifier).

- **`worldTables.json`** — Starport definitions (class, quality, berthing formula `"1d6*N"`, fuel, facilities), TAS travel zones (Amber/Red), and system base codes.

### Templates / static

- **`templates/index.html`** — Flask/Jinja2 template. Uses a dark terminal aesthetic as a placeholder; full Travellesque UI is a planned future milestone. Future CSS/JS assets belong in `static/`.

## Data Model

UWP (Universal World Profile) is a 9-character string like `"C566662-7"`:
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

Hex coordinates use a 4-digit `XXYY` format (e.g. `"1433"`). `world_data._hex_distance` computes Chebyshev distance on an offset grid.

## Implementation Roadmap

1. **Passengers** ✓ — availability rolls, passage types (High/Middle/Basic/Low), costs per jump, DMs from starport and population
2. **Freight lots** — Major/Minor/Incidental lot availability rolls, base freight costs per ton/jump, DMs from starport and trade codes
3. **Speculative trade** — trade good tables, purchase/sale DM resolution, trade code interactions, profit/loss calculation
4. **Travellesque UI** — full visual redesign of the web interface with a Traveller-universe aesthetic (starfield, ANSI-terminal styling, ship computer display). CSS/JS goes in `static/`; layout lives in `templates/`.
