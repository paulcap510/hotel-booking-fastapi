import requests


def geocode_city(city: str):
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city, "format": "json", "addressdetails": 1, "limit": 1},
            headers={"User-Agent": "hot-hotels-portfolio-app (contact: pc510892@gmail.com)",
                     "Accept-Language": "en"},
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
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city, "format": "json", "addressdetails": 1, "limit": limit},
            headers={"User-Agent": "hot-hotels-portfolio-app (contact: pc510892@gmail.com)", "Accept-Language": "en"},
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException:
        return []

    results = response.json()

    candidates = []
    for result in results:
        candidates.append({
            "display_name": result.get("display_name"),
            "latitude": float(result["lat"]),
            "longitude": float(result["lon"]),
        })

    return candidates