from database import SessionLocal
from utils.geocoding import geocode_city
import models

db = SessionLocal()

hotels = db.query(models.Hotel).all()
print(f"Found {len(hotels)} hotels")

for hotel in hotels:
    geocode_result = geocode_city(hotel.city)
    if geocode_result:
        hotel.latitude = geocode_result["latitude"]
        hotel.longitude = geocode_result["longitude"]
        print(f"Updated {hotel.name}: {geocode_result}")
    else:
        print(f"Could not geocode {hotel.name} (city: {hotel.city})")

db.commit()
db.close()
print("Backfill complete.")