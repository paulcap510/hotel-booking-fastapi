from sqlalchemy import func
from sqlalchemy.orm import Session
import models


def get_hotel_average_rating(db: Session, hotel_id: int):
    result = (
        db.query(func.avg(models.Review.review_score), func.count(models.Review.id))
        .join(models.Booking, models.Review.booking_id == models.Booking.id)
        .join(models.Room, models.Booking.room_id == models.Room.id)
        .filter(models.Room.hotel_id == hotel_id)
        .first()
    )
    average_rating, review_count = result
    return average_rating, review_count


def get_recent_hotel_reviews(db: Session, hotel_id: int, limit: int = 5):
    reviews = (
        db.query(models.Review)
        .join(models.Booking, models.Review.booking_id == models.Booking.id)
        .join(models.Room, models.Booking.room_id == models.Room.id)
        .filter(models.Room.hotel_id == hotel_id)
        .order_by(models.Review.created_at.desc())
        .limit(limit)
        .all()
    )
    return reviews