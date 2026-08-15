from database import SessionLocal
import models
from utils.geocoding import geocode_city

db = SessionLocal()

city = "Scottsdale, AZ"
geocode_result = geocode_city(city)

hotel = models.Hotel(
    name="Desert Palms Motel",
    description="A simple roadside motel with an outdoor pool, just off the highway.",
    image_path="https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?fm=jpg&q=60&w=3000&auto=format&fit=crop",
    city=city,
    latitude=geocode_result["latitude"] if geocode_result else None,
    longitude=geocode_result["longitude"] if geocode_result else None,
    has_pool=True,
    free_wifi=True,
    has_parking=True,
    smoke_free=True,
)
db.add(hotel)
db.flush()  # get hotel.id before creating the room

room = models.Room(
    hotel_id=hotel.id,
    room_type="Standard Queen",
    price_per_night=79,
    max_guests=2,
    total_inventory=4,
)
db.add(room)

db.commit()
db.refresh(hotel)
db.refresh(room)

print(f"Created hotel id {hotel.id} (lat={hotel.latitude}, lon={hotel.longitude})")
print(f"Created room id {room.id} for hotel {hotel.id}")

db.close()
