import random

# Passage costs per jump (Cr) — MGT2e Core Rulebook p.240
PASSAGE_COSTS = {
    'High':   10_000,
    'Middle':  8_000,
    'Basic':   2_000,
    'Low':     1_000,
}

# Starport class → availability DM; key absent = no passengers (X)
STARPORT_DM = {
    'A':  2,
    'B':  1,
    'C':  0,
    'D': -1,
    'E': -3,
}

# UWP population digit → availability DM
POPULATION_DM = {
    '0': -4,
    '1': -4,
    '2': -2,
    '3': -2,
    '4': -1,
    '5':  0,
    '6':  1,
    '7':  2,
    '8':  3,
    '9':  4,
    'A':  5,
    'B':  5,
    'C':  5,
}

# Per-type DM applied on top of starport + population — verify against rulebook
PASSAGE_TYPE_DM = {
    'High':   0,
    'Middle': 0,
    'Basic':  0,
    'Low':    0,
}

# 2d6 result → number of passengers seeking passage
AVAILABILITY_TABLE = {
    2:  0,
    3:  1,
    4:  1,
    5:  2,
    6:  3,
    7:  4,
    8:  5,
    9:  6,
    10: 7,
    11: 8,
    12: 10,
}


def _roll_2d6():
    return random.randint(1, 6) + random.randint(1, 6)


def _lookup(roll):
    return AVAILABILITY_TABLE[max(2, min(12, roll))]


def find_passengers(starport_class, population_digit, jump_distance):
    """
    Roll availability for each passage type at the given world and jump distance.
    Returns (counts_by_type dict, total_potential_revenue).
    Starport X yields zero passengers.
    """
    sp_dm = STARPORT_DM.get(starport_class.upper())
    if sp_dm is None:
        return {t: 0 for t in PASSAGE_COSTS}, 0

    pop_dm = POPULATION_DM.get(population_digit.upper(), 0)
    base_dm = sp_dm + pop_dm

    counts = {
        ptype: _lookup(_roll_2d6() + base_dm + type_dm)
        for ptype, type_dm in PASSAGE_TYPE_DM.items()
    }

    revenue = sum(
        count * PASSAGE_COSTS[ptype] * jump_distance
        for ptype, count in counts.items()
    )

    return counts, revenue
