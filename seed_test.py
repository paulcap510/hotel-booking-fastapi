from database import SessionLocal
import models
from utils.geocoding import geocode_city

db = SessionLocal()

hotel = db.query(models.Hotel).filter(models.Hotel.id == 9).first()

geocode_result = geocode_city(hotel.city)
if geocode_result:
    hotel.latitude = geocode_result["latitude"]
    hotel.longitude = geocode_result["longitude"]
    db.commit()
    print(f"Updated hotel {hotel.id} with lat={hotel.latitude}, lon={hotel.longitude}")
else:
    print("Geocoding failed for:", hotel.city)

db.close()
