from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import BookingCreate, BookingResponse


router = APIRouter(
    # prefix="/api/bookings",
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

    if booking.check_out_date <= booking.check_in_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Check-out date must be after check-in date"
        )

    overlapping_booking = find_overlapping_booking(
        db=db,
        room_id=room_id,
        check_in_date=booking.check_in_date,
        check_out_date=booking.check_out_date,
    )

    if overlapping_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room is already booked for these dates"
        )

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

#! Get Bookings All
@router.get("/api/bookings", response_model=list[BookingResponse])
def get_bookings(db: Session = Depends(get_db)):
    bookings = db.query(models.Booking).all()
    return bookings

#! Get Specific Booking
@router.get("/api/bookings/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    return booking

#! Update Booking
@router.put("/api/bookings/{booking_id}", response_model=BookingResponse)
def update_booking(booking_id: int, updated_booking: BookingCreate, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    room = db.query(models.Room).filter(models.Room.id == booking.room_id).first()

    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    if updated_booking.check_out_date <= updated_booking.check_in_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Check-out date must be after check-in date"
        )

    if updated_booking.number_of_guests > room.max_guests:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Number of guests exceeds room capacity"
        )

    overlapping_booking = find_overlapping_booking(
        db=db,
        room_id=booking.room_id,
        check_in_date=updated_booking.check_in_date,
        check_out_date=updated_booking.check_out_date,
        exclude_booking_id=booking_id,
    )

    if overlapping_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room is already booked for these dates"
        )

    booking.guest_name = updated_booking.guest_name
    booking.guest_email = updated_booking.guest_email
    booking.check_in_date = updated_booking.check_in_date
    booking.check_out_date = updated_booking.check_out_date
    booking.number_of_guests = updated_booking.number_of_guests

    db.commit()
    db.refresh(booking)

    return booking
#! Delete Booking
@router.delete("/api/bookings/{booking_id}")
def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    db.delete(booking)
    db.commit()

    return {"message": "Booking deleted successfully"}


#! Helper Function to Check Duplicate Bookings
def find_overlapping_booking(db: Session, room_id: int, check_in_date, check_out_date, exclude_booking_id: int | None = None,
    ):
    query = (db.query(models.Booking).filter(models.Booking.room_id == room_id).filter(models.Booking.check_in_date < check_out_date).filter(models.Booking.check_out_date > check_in_date))

    if exclude_booking_id is not None:
        query = query.filter(models.Booking.id != exclude_booking_id)

    return query.first()

