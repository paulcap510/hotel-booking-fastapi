import requests
from functools import lru_cache
from time import time

_geocode_cache = {}
CACHE_TTL = 86400  # 24 hours


def geocode_city(city: str):
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city, "format": "json", "addressdetails": 1, "limit": 1},
            headers={
                "User-Agent": "hot-hotels-portfolio-app (contact: pc510892@gmail.com)",
                "Accept-Language": "en",
            },
            timeout=5,
        )

        response.raise_for_status()
    except requests.RequestException:
        return None

    results = response.json()

    if not results:
        return None

    result = results[0]
    address = result.get("address", {})

    return {
        "latitude": float(result["lat"]),
        "longitude": float(result["lon"]),
    }


def geocode_city_candidates(city: str, limit: int = 5):
    key = city.strip().lower()
    now = time()

    if key in _geocode_cache:
        cached_time, cached_result = _geocode_cache[key]
        if now - cached_time < CACHE_TTL:
            return cached_result

    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city, "format": "json", "addressdetails": 1, "limit": limit},
            headers={
                "User-Agent": "hot-hotels-portfolio-app (contact: pc510892@gmail.com)",
                "Accept-Language": "en",
            },
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException:
        return []

    results = response.json()

    candidates = []
    for result in results:
        candidates.append(
            {
                "display_name": result.get("display_name"),
                "latitude": float(result["lat"]),
                "longitude": float(result["lon"]),
            }
        )

    _geocode_cache[key] = (now, candidates)
    return candidates
