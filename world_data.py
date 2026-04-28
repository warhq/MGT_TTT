import json
import random
import passengers


def _hex_distance(hex_a, hex_b):
    ax, ay = int(hex_a[:2]), int(hex_a[2:])
    bx, by = int(hex_b[:2]), int(hex_b[2:])
    return max(abs(ax - bx), abs(ay - by), abs(ax + ay - bx - by))


def _roll_berthing(berthing_str):
    if berthing_str in ('Free', '-'):
        return 0
    return random.randint(1, 6) * int(berthing_str.split('*')[1])


def load_tables(path='worldTables.json'):
    """Load all game lookup tables. Returns a dict used by process_world."""
    with open(path) as f:
        wt = json.load(f)
    return {
        'starports': {s['Class']: s for s in wt['Starport']},
        'zones':     {z['Class']: z['Description'] for z in wt['tasZones']},
        'bases':     {b['Code']: b['Type'] for b in wt['systemBases']},
    }


def process_world(world, origin_hex, tables):
    """
    Enrich a raw API world dict in-place with parsed UWP, starport details,
    hex distance, and passenger availability.

    Returns the same dict so callers can keep appending data (freight,
    trade, etc.) to the same object as features are added.
    """
    uwp = world['UWP']
    starport_class = uwp[0].upper()

    starport = tables['starports'].get(starport_class, {})
    berthing = _roll_berthing(starport.get('Berthing', '-'))

    jump_distance = max(1, _hex_distance(origin_hex, world['Hex']))

    passenger_counts, passenger_revenue = passengers.find_passengers(
        starport_class, uwp[4], jump_distance
    )

    world['uwp_parsed'] = {
        'Starport':      uwp[0],
        'Size':          uwp[1],
        'Atmosphere':    uwp[2],
        'Hydrographics': uwp[3],
        'Population':    uwp[4],
        'Government':    uwp[5],
        'LawLevel':      uwp[6],
        'TechLevel':     uwp[8],
    }
    world['starport_detail'] = {**starport, 'BerthingCost': berthing}
    world['zone_description'] = tables['zones'].get(world.get('Zone', ''), '')
    world['base_description'] = tables['bases'].get(world.get('Bases', ''), '')
    world['jump_distance'] = jump_distance
    world['passengers'] = {
        'counts':  passenger_counts,
        'revenue': passenger_revenue,
        'breakdown': {
            ptype: {
                'count':          count,
                'cost_per_jump':  passengers.PASSAGE_COSTS[ptype],
                'line_revenue':   count * passengers.PASSAGE_COSTS[ptype] * jump_distance,
            }
            for ptype, count in passenger_counts.items()
        },
    }

    return world
