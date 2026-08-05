import json
import random
from datetime import date, timedelta
from database import SessionLocal
import models

db = SessionLocal()

with open("seed_reviews.json") as f:
    review_data = json.load(f)

for hotel_name, reviews in review_data.items():

    hotel = (
        db.query(models.Hotel)
        .filter(models.Hotel.name.ilike(hotel_name.strip()))
        .first()
    )

    if hotel is None:
        print(f"Could not find hotel: {hotel_name}")
        continue

    existing_seed_bookings = (
        db.query(models.Booking)
        .join(models.Room)
        .filter(models.Room.hotel_id == hotel.id)
        .filter(models.Booking.guest_email == "testguest@example.com")
        .count()
    )

    if existing_seed_bookings > 0:
        print(f"Skipping {hotel_name} — already has seed reviews")
        continue

    room = db.query(models.Room).filter(models.Room.hotel_id == hotel.id).first()

    if room is None:
        print(f"No room found for hotel: {hotel_name}")
        continue

    for review in reviews:
        check_in = date.today() - timedelta(days=random.randint(30, 200))
        check_out = check_in + timedelta(days=random.randint(1, 4))

        booking = models.Booking(
            room_id=room.id,
            user_id=1,
            guest_name="Test Guest",
            guest_email="testguest@example.com",
            check_in_date=check_in,
            check_out_date=check_out,
            number_of_guests=1,
            number_of_nights=(check_out - check_in).days,
            price_per_night=room.price_per_night,
            total_price=room.price_per_night * (check_out - check_in).days,
            booking_status="confirmed",
        )
        db.add(booking)
        db.flush()

        new_review = models.Review(
            booking_id=booking.id,
            user_id=1,
            review_score=review["score"],
            review_description=review["text"],
        )
        db.add(new_review)

    print(f"Seeded {len(reviews)} reviews for {hotel_name}")

db.commit()
db.close()
print("Done.")
