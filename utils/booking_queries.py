from datetime import date

from sqlalchemy.orm import Session
from schemas import BookingStatus

import models


def get_bookings_for_user(db: Session, user_id: int):

    today = date.today()

    all_bookings = (
        db.query(models.Booking)
        .filter(models.Booking.user_id == user_id)
        .order_by(models.Booking.check_in_date)
        .all()
    )

    cancelled_bookings = [b for b in all_bookings if b.booking_status == BookingStatus.cancelled]
    active_bookings = [b for b in all_bookings if b.booking_status != BookingStatus.cancelled]

    upcoming_bookings = [b for b in active_bookings if b.check_in_date > today]
    current_bookings = [b for b in active_bookings if b.check_in_date <= today <= b.check_out_date]
    past_bookings = [b for b in active_bookings if b.check_out_date < today]

    return upcoming_bookings, current_bookings, past_bookings, cancelled_bookings