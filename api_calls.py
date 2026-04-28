import requests

BASE_URL = "https://travellermap.com"


def fetch_worlds(sector, hex_code, jump_distance=3):
    """
    Download all worlds within jump_distance of hex_code in sector.

    Returns a list of world dicts. Each dict contains all fields from the
    travellermap.com API response (Name, Hex, UWP, Bases, Zone, Remarks,
    Allegiance, Sector, SubsectorName, Stellar, PBG, etc.) and is intended
    to be the single working record for that world — app-generated data
    (passengers, freight, trade) should be added as new keys on each dict.

    Returns an empty list on any failure.
    """
    url = f"{BASE_URL}/data/{sector}/{hex_code}/jump/{jump_distance}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json().get("Worlds", [])
    except requests.exceptions.ConnectionError:
        print(f"Error: Cannot connect to {BASE_URL}. Check your internet connection.")
    except requests.exceptions.Timeout:
        print(f"Error: Request to {BASE_URL} timed out.")
    except requests.exceptions.HTTPError as e:
        print(f"Error: API returned HTTP {e.response.status_code} for {url}")
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error: API request failed — {e}")

    return []
