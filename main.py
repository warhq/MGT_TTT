# MGT Trade Tool — CLI entry point

import json
import api_calls
import world_data

SECTOR     = 'Spinward Marches'
ORIGIN_HEX = '1433'
JUMP_RANGE = 3

with open('gameSys.json') as f:
    GameSys = json.load(f)

tables = world_data.load_tables()

worlds = api_calls.fetch_worlds(SECTOR, ORIGIN_HEX, JUMP_RANGE)
if not worlds:
    raise SystemExit("No world data available. Cannot continue.")

w = world_data.process_world(worlds[0], ORIGIN_HEX, tables)

up = w['uwp_parsed']
sp = w['starport_detail']

print(f"## {w['Name']} - {w['SubsectorName']} / {w['Sector']} ({w['Hex']}) {w['zone_description']}")
print(f"   {w['UWP']}  |  {w['Bases']}  |  {w['Remarks']}  |  {w['Allegiance']}")
print()
print(f"Starport:        {up['Starport']}")
print(f"        Quality: {sp.get('Quality', '-')}")
print(f"       Berthing: Cr{sp.get('BerthingCost', 0)}")
print(f"           Fuel: {sp.get('Fuel', '-')}")
print(f"     Facilities: {sp.get('Facilities', '-')}")
print(f"World Size:      {up['Size']}")
print(f"Atmosphere Type: {up['Atmosphere']}")
print(f"Hydrographic %:  {up['Hydrographics']}")
print(f"Population:      {up['Population']}")
print(f"Main Government: {up['Government']}")
print(f"Law Level:       {up['LawLevel']}")
print(f"Tech Level:      {up['TechLevel']}")
print()
print(f"Expanded information:")
print(f"         Bases:  {w['base_description'] or 'no known'}")
print(f"          Zone:  {w['zone_description'] or '-'}")
print()
print(f"Passengers available (Jump-{w['jump_distance']}):")
for ptype, data in w['passengers']['breakdown'].items():
    print(f"  {ptype:8} Passage: {data['count']:2}  @ Cr{data['cost_per_jump']:>6,}/jump  =  Cr{data['line_revenue']:>7,}")
print(f"  {'':38}------------")
print(f"  {'Total potential revenue':38}Cr{w['passengers']['revenue']:>7,}")
