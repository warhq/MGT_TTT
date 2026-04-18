# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MGT TTT (Mongoose Traveller 2e Trade Tool) is a Python CLI application that generates passenger, trade, and freight data for the Mongoose Traveller 2e tabletop RPG. It fetches live world data from the [travellermap.com](https://travellermap.com) API and applies MGT2e game mechanics (2d6 dice rolls with hex-coded modifiers).

## Commands

```bash
# Run the application
python main.py

# Install dependencies (requests is the only external dependency)
pip install requests

# Lint (mirrors CI checks)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Run tests
pytest
```

CI runs on Python 3.10. There is no `requirements.txt` yet — add one if new dependencies are introduced.

## Architecture

The app has two source files and two JSON data files:

- **`api_calls.py`** — Makes a single HTTP GET to `https://travellermap.com/data/{sector}/{hex}/jump/{distance}` and exposes the parsed JSON as the module-level `data` variable. The response shape is `{"Worlds": [{...}, ...]}` where each world has `Name`, `Hex`, `UWP`, `Bases`, `Zone`, `Remarks`, `Allegiance`, `Sector`, `SubsectorName`, etc.

- **`main.py`** — Imports `api_calls.data`, loads the two JSON files, parses the UWP string (positional character offsets: index 0=Starport, 1=Size, 2=Atmo, 3=Hydro, 4=Pop, 5=Gov, 6=Law, 8=TL), looks up starport berthing costs, calculates hex-grid distances between worlds, and prints a formatted world summary.

- **`gameSys.json`** — MGT2e lookup tables: `diceModStd` (hex digit → dice modifier, values 0–F → −3 to +3) and `taskEffectMod` (task roll result → effect modifier). Note: the file uses C-style `/* */` comments which are not valid JSON — use a comment-tolerant parser or strip comments before loading.

- **`worldTables.json`** — Starport class definitions (berthing cost formula `"1d6*N"`, fuel type, facilities), TAS travel zones (Amber/Red), and system base codes. Also contains C-style comments and uses `=` instead of `:` in one object — the file has syntax errors that must be fixed before it can be parsed.

## Known Issues to Be Aware Of

1. **`gameSys.json` and `worldTables.json`** both contain C-style `/* */` comments and at least one `=` assignment operator — standard `json.load()` will fail. These need to be fixed (remove comments, fix `=` → `:`) before the JSON loader works.

2. **`main.py` line 11** has `import gameSys.json` which is dead code (invalid Python import of a `.json` file); the actual loading is done correctly via `open('gameSys.json')` on line 26.

3. **`worldZones_dict` and `worldBases_dict`** are referenced on lines 65–66 but never defined — the app will raise `NameError` at runtime. These need to be built from the `worldTables.json` data after it is fixed.

4. **Berthing cost randomisation** on line 71 reads `berthingRange.split('*')[1]` but the formula string is `"1d6*1000"`, so index `[1]` gives the multiplier correctly — however starport classes E and X have `"Free"` or `"-"` as berthing values, which will cause a crash if those classes are encountered.

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

Hex coordinates use a 4-digit `XXYY` format (e.g. `"1433"`). The `hex_distance` function in `main.py` computes Chebyshev distance on an offset grid.
