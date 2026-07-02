from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import BookingCreate, BookingResponse, MyBookingsResponse, BookingContactUpdate

from utils.pricing import calculate_nights, calculate_total_price
from utils.inventory import calculate_available_inventory
from utils.booking_status import BookingStatus
from utils.booking_logic import create_booking_for_user
from utils.booking_queries import get_bookings_for_user


from routers.users import get_current_user

router = APIRouter(
    tags=['Bookings']
)

#! Create Booking
@router.post("/api/rooms/{room_id}/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    room_id: int,
    booking: BookingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return create_booking_for_user(
        db=db,
        room_id=room_id,
        user_id=current_user.id,
        guest_name=booking.guest_name,
        guest_email=booking.guest_email,
        check_in_date=booking.check_in_date,
        check_out_date=booking.check_out_date,
        number_of_guests=booking.number_of_guests,
    )


#! Get Bookings All
@router.get("/api/bookings", response_model=list[BookingResponse])
def get_bookings(db: Session = Depends(get_db)):
    bookings = db.query(models.Booking).all()
    return bookings

#! Get Bookings for a Specific User
@router.get("/api/bookings/me", response_model=MyBookingsResponse)
def get_my_bookings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    upcoming, current, past, cancelled = get_bookings_for_user(db, current_user.id)
    return MyBookingsResponse(
        upcoming_bookings=upcoming,
        current_bookings=current,
        past_bookings=past,
        cancelled_bookings=cancelled,
    )

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
def update_booking(
    booking_id: int,
    updated_booking: BookingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this booking"
        )

    if booking.booking_status == BookingStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a completed booking"
        )

    if booking.booking_status == BookingStatus.cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a cancelled booking"
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

    try:
        available_inventory = calculate_available_inventory(
            db=db,
            room_id=booking.room_id,
            check_in_date=updated_booking.check_in_date,
            check_out_date=updated_booking.check_out_date,
            exclude_booking_id=booking_id,
        )

        if available_inventory <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No rooms available for these dates"
            )

        number_of_nights = calculate_nights(updated_booking.check_in_date, updated_booking.check_out_date)
        price_per_night = booking.price_per_night
        total_price = calculate_total_price(price_per_night, number_of_nights)

        booking.guest_name = updated_booking.guest_name
        booking.guest_email = updated_booking.guest_email
        booking.check_in_date = updated_booking.check_in_date
        booking.check_out_date = updated_booking.check_out_date
        booking.number_of_guests = updated_booking.number_of_guests
        booking.number_of_nights = number_of_nights
        booking.total_price = total_price

        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(booking)
    return booking

#! Complete A Booking
@router.patch("/api/bookings/{booking_id}/complete", response_model=BookingResponse)
def complete_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    if booking.booking_status == BookingStatus.cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot complete a booking that has been cancelled"
        )

    if booking.booking_status == BookingStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already completed"
        )

    booking.booking_status = BookingStatus.completed

    db.commit()
    db.refresh(booking)

    return booking

#! Cancel A Booking
@router.patch("/api/bookings/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(booking_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    if booking.booking_status == BookingStatus.cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot complete a booking that has been cancelled"
        )

    if booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this booking")

    if booking.booking_status == BookingStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already completed"
        )

    booking.booking_status = BookingStatus.cancelled

    db.commit()
    db.refresh(booking)

    return booking

#! Delete Booking - For Admin Use
@router.delete("/api/bookings/{booking_id}")
def delete_booking(booking_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):

    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    db.delete(booking)
    db.commit()

    return {"message": "Booking deleted successfully"}





#! Update Booking Contact Info (name/email only — no date/availability logic)
@router.patch("/api/bookings/{booking_id}/details", response_model=BookingResponse)
def update_booking_details(
    booking_id: int,
    contact_update: BookingContactUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()

    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this booking")

    if booking.booking_status == BookingStatus.cancelled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot update a cancelled booking")

    booking.guest_name = contact_update.guest_name
    booking.guest_email = contact_update.guest_email

    db.commit()
    db.refresh(booking)

    return booking



