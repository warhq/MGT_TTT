# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MGT TTT (Mongoose Traveller 2e Trade Tool) is a Python CLI application that generates passenger, trade, and freight data for the Mongoose Traveller 2e tabletop RPG. It fetches live world data from the [travellermap.com](https://travellermap.com) API and applies MGT2e game mechanics (2d6 dice rolls with hex-coded modifiers).

## Commands

```bash
# Run the application (note: hits the live travellermap.com API on every run)
python main.py

# Install dependencies (requests is the only external dependency)
pip install requests

# Lint (mirrors CI checks)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Run tests (no tests exist yet — pytest will collect 0 items and exit 5)
pytest

# Run a single test once tests are added
pytest path/to/test_file.py::test_name
```

CI (`.github/workflows/python-app.yml`) runs on Python 3.10 and triggers on push and pull-request to `main` only — other branches do not run CI. There is no `requirements.txt`; CI installs `flake8` and `pytest` directly and only `pip install -r requirements.txt` if the file exists, so add one if new runtime dependencies are introduced.

## Architecture

The app has two Python source files and two JSON data files. There is no package/module structure — everything runs as top-level scripts in the repo root.

- **`api_calls.py`** — Builds a URL of the form `https://travellermap.com/data/{sector}/{hex}/jump/{distance}` (sector, subsector, hex, and jump distance are hard-coded constants) and makes a single HTTP GET. Exposes the parsed JSON as the module-level `data` variable. The response shape is `{"Worlds": [{...}, ...]}` where each world has `Name`, `Hex`, `UWP`, `Bases`, `Zone`, `Remarks`, `Allegiance`, `Sector`, `SubsectorName`, etc. **Import-time side effects:** simply `import api_calls` performs the network request and prints the full payload plus a per-world summary to stdout. Any test or refactor needs to either mock `requests.get` or restructure this into a function.

- **`main.py`** — Imports `api_calls.data`, loads the two JSON files, parses the UWP string (positional character offsets: index 0=Starport, 1=Size, 2=Atmo, 3=Hydro, 4=Pop, 5=Gov, 6=Law, 8=TL), looks up starport berthing costs, calculates hex-grid distances between worlds, and prints a formatted world summary. Note that `main.py` only ever inspects `worlds["Worlds"][0]` — it does not iterate the full result set.

- **`gameSys.json`** — MGT2e lookup tables: `diceModStd` (hex digit → dice modifier, values 0–F → −3 to +3) and `taskEffectMod` (task roll result → effect modifier). Uses C-style `/* */` comments which are not valid JSON — use a comment-tolerant parser or strip comments before loading.

- **`worldTables.json`** — Starport class definitions (`Berthing` formula `"1d6*N"`, fuel type, facilities), TAS travel zones (Amber/Red as `tasZones`), and system base codes (`systemBases`). The `tasZones` and `systemBases` blocks are what should back the missing `worldZones_dict` and `worldBases_dict` in `main.py`. Also contains C-style comments and uses `=` instead of `:` in two places (`"tasZones" =` and `"systemBases" =`) — the file has syntax errors that must be fixed before it can be parsed.

- **`TravellerMapAPIOutput`** — Not code. A scratch reference file containing example API URLs, raw JSON payloads, and Python prototypes. Useful for understanding the data shape without making a live API call. Do not import from it.

### Data Duplication to Watch For

The starport class table is currently defined **twice**: as a hard-coded JSON string `starPortInfo` at `main.py:16`, and again in `worldTables.json`. Only the string in `main.py` is actually used at runtime (parsed into `starports` on line 23); the `Starport` block in `worldTables.json` is loaded into `WorldTables` but never read. When fixing the JSON parsing issues, plan to consolidate these.

## Known Issues to Be Aware Of

1. **`gameSys.json` and `worldTables.json`** both contain C-style `/* */` comments and `worldTables.json` uses `=` instead of `:` for two keys — standard `json.load()` will fail on both. These need to be fixed (remove comments, fix `=` → `:`) before the JSON loaders work. CI lint passes because flake8 doesn't validate JSON, but `python main.py` crashes immediately on the `open('gameSys.json')` call.

2. **`main.py` line 11** has `import gameSys.json` which is invalid Python (you cannot `import` a `.json` file) — this is a syntax-level dead line that will raise `ModuleNotFoundError` before any other code runs. The actual JSON loading is done correctly via `open('gameSys.json')` on line 26. Remove the bogus import.

3. **`worldZones_dict` and `worldBases_dict`** are referenced on `main.py` lines 65–66 but never defined — the app will raise `NameError` at runtime. These need to be built from the `tasZones` and `systemBases` arrays in `worldTables.json` after that file is fixed.

4. **Berthing cost randomisation** on `main.py:71` reads `berthingRange.split('*')[1]` — works for classes A–D whose formula is `"1d6*N"`, but starport classes E (`"Free"`) and X (`"-"`) will raise `IndexError`/`ValueError`. Needs a branch for non-formula berthing values.

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
