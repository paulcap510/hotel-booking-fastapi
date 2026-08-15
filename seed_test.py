import time
from database import SessionLocal
import models
from utils.geocoding import geocode_city

db = SessionLocal()

HOTELS_TO_SEED = [
    {
        "name": "Palmwood Suites",
        "description": "A relaxed hotel with a lush, palm-lined lobby.",
        "city": "Miami, FL",
        "image": "https://images.unsplash.com/photo-1455587734955-081b22074882?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"free_wifi": True, "has_pool": True},
    },
    {
        "name": "The Harbor Inn",
        "description": "A cozy, well-appointed room to unwind after a day exploring.",
        "city": "Portland, ME",
        "image": "https://images.unsplash.com/photo-1711059985570-4c32ed12a12c?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"free_wifi": True, "free_breakfast": True},
    },
    {
        "name": "Coral Bay Resort",
        "description": "A tropical-style pool retreat with pastel poolside charm.",
        "city": "Key West, FL",
        "image": "https://images.unsplash.com/photo-1596436889106-be35e843f974?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"has_pool": True, "free_wifi": True, "smoke_free": True},
    },
    {
        "name": "Lakeside Dock Lodge",
        "description": "Lounge chairs on a private dock, right on the water.",
        "city": "Lake Tahoe, CA",
        "image": "https://images.unsplash.com/photo-1582719508461-905c673771fd?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"has_pool": True, "free_wifi": True},
    },
    {
        "name": "The Gilded Room Hotel",
        "description": "An elegant lobby with chandelier lighting and classic details.",
        "city": "New Orleans, LA",
        "image": "https://images.unsplash.com/photo-1625244724120-1fd1d34d00f6?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"free_wifi": True, "has_spa": True},
    },
    {
        "name": "Crescent Bedding Hotel",
        "description": "Simple, comfortable rooms with crisp white linens.",
        "city": "Austin, TX",
        "image": "https://images.unsplash.com/photo-1631049552057-403cdb8f0658?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"free_wifi": True, "air_conditioned": True},
    },
    {
        "name": "Azure Pool House",
        "description": "A bright blue outdoor pool right outside your room.",
        "city": "Scottsdale, AZ",
        "image": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"has_pool": True, "free_wifi": True, "has_parking": True},
    },
    {
        "name": "The Tablecloth Hotel & Bistro",
        "description": "A boutique hotel known for its in-house restaurant.",
        "city": "Charleston, SC",
        "image": "https://images.unsplash.com/photo-1551632436-cbf8dd35adfa?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"free_breakfast": True, "free_wifi": True},
    },
    {
        "name": "Oceanfront Eighty Resort",
        "description": "A tropical-style pool with sweeping ocean views.",
        "city": "Honolulu, HI",
        "image": "https://images.unsplash.com/photo-1540541338287-41700207dee6?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"has_pool": True, "free_wifi": True, "airport_shuttle": True},
    },
    {
        "name": "Redbrick Loft Hotel",
        "description": "A relaxed urban room with a pop of color.",
        "city": "Brooklyn, NY",
        "image": "https://images.unsplash.com/photo-1590490360182-c33d57733427?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"free_wifi": True},
    },
    {
        "name": "Green Terrace Hotel",
        "description": "A calm, plant-filled lobby and lounge area.",
        "city": "Seattle, WA",
        "image": "https://images.unsplash.com/photo-1590447158019-883d8d5f8bc7?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"free_wifi": True, "has_laundry": True},
    },
    {
        "name": "Shoreline Towers",
        "description": "High-rise hotel with beachfront views.",
        "city": "San Diego, CA",
        "image": "https://images.unsplash.com/photo-1454388683759-ee76c15fee26?fm=jpg&q=60&w=3000&auto=format&fit=crop",
        "amenities": {"has_pool": True, "free_wifi": True, "has_gym": True},
    },
    {
        "name": "Downtown Comfort Hotel",
        "description": "Clean, modern rooms in a central location.",
        "city": "Chicago, IL",
        "image": "https://images.unsplash.com/photo-1631049421450-348ccd7f8949?fm=jpg&q=60&w=3000&auto=format&fit=crop",
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
    db.flush()  # get hotel.id before creating the room

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
    print(
        f"Created hotel '{data['name']}' in {data['city']} (id will be assigned on commit)"
    )

    time.sleep(1)  # be polite to the geocoding API

db.commit()

print(f"\nDone. Created {created} hotels.")
if skipped:
    print(f"WARNING: geocoding failed for: {skipped}")

db.close()
