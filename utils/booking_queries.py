from datetime import date

from sqlalchemy.orm import Session

import models


def get_bookings_for_user(db: Session, user_id: int):
    """
    Fetch all of a user's bookings and split them into three groups:
    upcoming (not started yet), current (checked in right now),
    and past (already checked out).

    Used by both the JSON API route (/api/bookings/me) and the
    Jinja page route (/bookings) so this logic only lives in one place.
    """
    today = date.today()

    all_bookings = (
        db.query(models.Booking)
        .filter(models.Booking.user_id == user_id)
        .order_by(models.Booking.check_in_date)
        .all()
    )

    upcoming_bookings = [b for b in all_bookings if b.check_in_date > today]
    current_bookings = [b for b in all_bookings if b.check_in_date <= today <= b.check_out_date]
    past_bookings = [b for b in all_bookings if b.check_out_date < today]

    return upcoming_bookings, current_bookings, past_bookings