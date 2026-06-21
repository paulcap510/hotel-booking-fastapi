from datetime import date
from sqlalchemy.orm import Session

import models


def calculate_available_inventory(
    db: Session,
    room_id: int,
    check_in_date: date,
    check_out_date: date,
    exclude_booking_id: int | None = None,
):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()

    if room is None:
        return 0

    query = (
        db.query(models.Booking)
        .filter(models.Booking.room_id == room_id)
        .filter(models.Booking.check_in_date < check_out_date)
        .filter(models.Booking.check_out_date > check_in_date)
    )

    if exclude_booking_id is not None:
        query = query.filter(models.Booking.id != exclude_booking_id)

    bookings_for_dates = query.count()

    available_inventory = room.total_inventory - bookings_for_dates

    return available_inventory