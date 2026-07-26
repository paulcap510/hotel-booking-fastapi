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

    metro_area = (
        address.get("city")
        or address.get("town")
        or address.get("state")
        or address.get("municipality")
        or address.get("province")
        or address.get("county")
    )

    return {
        "metro_area": metro_area,
        "latitude": float(result["lat"]),
        "longitude": float(result["lon"]),
    }