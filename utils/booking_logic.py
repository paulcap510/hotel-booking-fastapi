from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import models
from utils.pricing import calculate_nights, calculate_total_price
from utils.inventory import calculate_available_inventory
from utils.booking_status import BookingStatus


def create_booking_for_user(
    db: Session,
    room_id: int,
    user_id: int,
    guest_name: str,
    guest_email: str,
    check_in_date: date,
    check_out_date: date,
    number_of_guests: int,
) -> models.Booking:
    """
    Shared booking-creation logic used by both the JSON API route
    (create_booking) and the HTML form route (submit_booking_form).
    Raises HTTPException on any validation failure. Returns the
    newly created Booking on success.
    """
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if number_of_guests > room.max_guests:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Number of guests exceeds room capacity")

    if check_out_date <= check_in_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Check-out date must be after check-in date")

    number_of_nights = calculate_nights(check_in_date, check_out_date)
    price_per_night = room.price_per_night
    total_price = calculate_total_price(price_per_night, number_of_nights)


    try:
        available_inventory = calculate_available_inventory(
            db=db,
            room_id=room_id,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
        )

        if available_inventory <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No rooms available for these dates")

        new_booking = models.Booking(
            room_id=room_id,
            user_id=user_id,
            guest_name=guest_name,
            guest_email=guest_email,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            number_of_guests=number_of_guests,
            number_of_nights=number_of_nights,
            price_per_night=price_per_night,
            booking_status=BookingStatus.confirmed,
            total_price=total_price,
        )
        db.add(new_booking)
        db.commit()
    except:
        db.rollback()
        raise

    db.refresh(new_booking)
    return new_booking