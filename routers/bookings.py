from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import BookingCreate, BookingResponse


router = APIRouter(
    tags=['Bookings']
)

#! Create Booking
@router.post("/api/rooms/{room_id}/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(room_id: int, booking: BookingCreate, db: Session = Depends(get_db)):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()

    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
    )

    if booking.number_of_guests > room.max_guests: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Number of guests exceeds room capacity" )

    new_booking = models.Booking(
         room_id = room_id,
         guest_name = booking.guest_name,
         guest_email = booking.guest_email,
         check_in_date = booking.check_in_date,
         check_out_date = booking.check_out_date,
         number_of_guests = booking.number_of_guests
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return new_booking

