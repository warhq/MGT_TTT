"""HTTP wrappers for the travellermap.com data API.

Functions here perform live HTTP requests; importing this module no longer
triggers network I/O. Callers must invoke `fetch_jump_worlds()` explicitly.
"""

from urllib.parse import quote

import requests

BASE_URL = "https://travellermap.com"

DEFAULT_SECTOR = "Spinward Marches"
DEFAULT_HEX = "1433"
DEFAULT_JUMP = 3


def fetch_jump_worlds(sector: str, hex_id: str, jump: int) -> dict:
    """GET worlds within `jump` parsecs of `hex_id` in `sector`.

    Returns the parsed JSON, shape `{"Worlds": [{...}, ...]}`.
    Raises `requests.HTTPError` on non-2xx responses.
    """
    url = f"{BASE_URL}/data/{quote(sector)}/{hex_id}/jump/{jump}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    data = fetch_jump_worlds(DEFAULT_SECTOR, DEFAULT_HEX, DEFAULT_JUMP)
    for world in data["Worlds"]:
        print(
            f"World: {world['Name']:<16} UWP: {world['UWP']:<10} "
            f"Hex: {world['Hex']} Sector: {world['SectorAbbreviation']}"
        )
