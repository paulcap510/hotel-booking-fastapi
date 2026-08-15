import time
from database import SessionLocal
import models
from utils.geocoding import geocode_city

db = SessionLocal()

HOTELS_TO_SEED = [
    {
        "name": "Windowview Courtyard Hotel",
        "description": "A striking building wrapped around a quiet courtyard.",
        "city": "Santa Fe, NM",
        "image": "https://images.unsplash.com/photo-1667125094717-47e0ff6d0608?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"free_wifi": True, "has_parking": True},
    },
    {
        "name": "Northside Vacancy Inn",
        "description": "Simple, minimal rooms with plenty of natural light.",
        "city": "Burlington, VT",
        "image": "https://images.unsplash.com/photo-1549638441-b787d2e11f14?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"free_wifi": True, "smoke_free": True},
    },
    {
        "name": "Harborview Table & Terrace",
        "description": "Waterfront dining and calm coastal views.",
        "city": "Newport, RI",
        "image": "https://images.unsplash.com/photo-1498503182468-3b51cbb6cb24?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"free_wifi": True, "free_breakfast": True},
    },
    {
        "name": "The Windowlight Hotel",
        "description": "Moody, quiet rooms perfect for unwinding after a day out.",
        "city": "New York, NY",
        "image": "https://images.unsplash.com/photo-1592229505726-ca121723b8ef?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"free_wifi": True, "air_conditioned": True},
    },
    {
        "name": "Mission Bay Suites",
        "description": "Palm-lined poolside relaxation close to the water.",
        "city": "San Diego, CA",
        "image": "https://images.unsplash.com/photo-1623718649591-311775a30c43?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"has_pool": True, "free_wifi": True, "has_parking": True},
    },
    {
        "name": "Hillside Garden Villa",
        "description": "A peaceful villa-style hotel surrounded by greenery.",
        "city": "Asheville, NC",
        "image": "https://images.unsplash.com/photo-1614957004131-9e8f2a13123c?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"free_wifi": True, "has_balcony": True},
    },
    {
        "name": "Twin Bed Mirror Suites",
        "description": "Bright, colorful rooms with twin beds and modern decor.",
        "city": "Nashville, TN",
        "image": "https://images.unsplash.com/photo-1737517302831-e7b8a8eaa97c?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"free_wifi": True, "has_cribs": True},
    },
    {
        "name": "Grand Window Hotel",
        "description": "Spacious rooms with oversized windows and city views.",
        "city": "Denver, CO",
        "image": "https://images.unsplash.com/photo-1675409145919-277c0fc2aa7d?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"free_wifi": True, "air_conditioned": True},
    },
    {
        "name": "Sunset Pool Villas",
        "description": "A relaxed poolside stay with warm evening light.",
        "city": "Palm Springs, CA",
        "image": "https://images.unsplash.com/photo-1439130490301-25e322d88054?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"has_pool": True, "free_wifi": True, "smoke_free": True},
    },
    {
        "name": "Cancun-Style Poolside Resort",
        "description": "A tropical-inspired pool and building backdrop.",
        "city": "Fort Lauderdale, FL",
        "image": "https://images.unsplash.com/photo-1663998468593-1f104e7c9213?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"has_pool": True, "free_wifi": True, "airport_shuttle": True},
    },
    {
        "name": "Wood Table Inn",
        "description": "Comfortable, no-frills rooms with a warm wooden touch.",
        "city": "Boise, ID",
        "image": "https://images.unsplash.com/photo-1631049035182-249067d7618e?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"free_wifi": True, "has_parking": True},
    },
    {
        "name": "Empire View Hotel & Pool",
        "description": "A grand building overlooking a scenic outdoor pool.",
        "city": "Orlando, FL",
        "image": "https://images.unsplash.com/photo-1709809328185-ba9ee5a06121?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"has_pool": True, "free_wifi": True, "has_gym": True},
    },
    {
        "name": "Coastal Terrace Resort",
        "description": "Poolside comfort with sweeping coastal scenery nearby.",
        "city": "Myrtle Beach, SC",
        "image": "https://images.unsplash.com/photo-1598598795009-f80c5072e665?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"has_pool": True, "free_wifi": True},
    },
    {
        "name": "Cyprus Dining Hotel",
        "description": "A warm, welcoming dining space and comfortable stay.",
        "city": "Savannah, GA",
        "image": "https://images.unsplash.com/photo-1625244695851-1fc873f942bc?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"free_breakfast": True, "free_wifi": True},
    },
    {
        "name": "Crestline Bedding Hotel",
        "description": "Understated, comfortable rooms with clean white linens.",
        "city": "Minneapolis, MN",
        "image": "https://images.unsplash.com/photo-1631049552240-59c37f38802b?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"free_wifi": True, "air_conditioned": True},
    },
]

created = 0
skipped = []

for data in HOTELS_TO_SEED:
    geocode_result = geocode_city(data["city"])

    hotel = models.Hotel(
        name=data["name"],
        description=data["description"],
        image_path=data["image"],
        city=data["city"],
        latitude=geocode_result["latitude"] if geocode_result else None,
        longitude=geocode_result["longitude"] if geocode_result else None,
        **data["amenities"],
    )
    db.add(hotel)
    db.flush()

    room = models.Room(
        hotel_id=hotel.id,
        room_type="Standard Queen",
        price_per_night=99,
        max_guests=2,
        total_inventory=3,
    )
    db.add(room)

    if geocode_result is None:
        skipped.append(data["city"])

    created += 1
    print(f"Created hotel '{data['name']}' in {data['city']}")

    time.sleep(1)

db.commit()

print(f"\nDone. Created {created} hotels.")
if skipped:
    print(f"WARNING: geocoding failed for: {skipped}")

db.close()
