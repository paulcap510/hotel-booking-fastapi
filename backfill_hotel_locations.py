import time
from database import SessionLocal
from utils.geocoding import geocode_city
import models

db = SessionLocal()

hotels = db.query(models.Hotel).all()

for hotel in hotels:
    geocode_result = geocode_city(hotel.city)

    if geocode_result:
        hotel.metro_area = geocode_result["metro_area"]
        hotel.latitude = geocode_result["latitude"]
        hotel.longitude = geocode_result["longitude"]
        print(f"Updated {hotel.name}: metro_area={geocode_result['metro_area']}")
    else:
        print(f"Could not geocode {hotel.name} (city: {hotel.city})")

    time.sleep(1)

db.commit()
db.close()

print("Backfill complete.")