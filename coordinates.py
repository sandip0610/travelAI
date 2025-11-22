import requests

def get_coordinates(place_name):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": place_name,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "YourAppName/1.0 (sandipsubudhi123@gmail.com)"  # REQUIRED
    }

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()   # raises error if request failed

    data = response.json()
    if not data:
        return None

    return float(data[0]['lat']), float(data[0]['lon'])

