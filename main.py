from fastapi import FastAPI, Request, HTTPException, status, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Annotated
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from routers import hotels, rooms, bookings
from datetime import date

import models
from database import engine, Base, get_db

from utils.pricing import calculate_nights, calculate_total_price, calculate_starting_price
from utils.inventory import calculate_available_inventory


from schemas import HotelCreate, HotelResponse, RoomCreate, RoomResponse

app = FastAPI()

app.include_router(hotels.router)
app.include_router(rooms.router)
app.include_router(bookings.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def home(request:Request, db: Session = Depends(get_db)):
    hotels = db.query(models.Hotel).all()

    for hotel in hotels:
        rooms = (db.query(models.Room).filter(models.Room.hotel_id == hotel.id).all())
        hotel.starting_price = calculate_starting_price(rooms)

    return templates.TemplateResponse(request, "home.html",
                                      {
                                          "request": request,
                                          "hotels": hotels,

                                      })

@app.get("/hotel_info/{hotel_id}", response_class=HTMLResponse, include_in_schema=False)
def hotel_info(
    request: Request,
    hotel_id: int,
    guests: int = 1,
    check_in: date | None = None,
    check_out: date | None = None,
    db: Session = Depends(get_db)
):
    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotel not found"
        )

    if check_in and check_out:
        booking_count_table = (
            db.query(
                models.Booking.room_id.label("room_id"), #? show the room ID from Bookings table
                func.count(models.Booking.id).label("bookings_for_dates") #? count bookings for each room ID
            )
            .filter(models.Booking.check_in_date < check_out) #? filtering bookings based on the dates
            .filter(models.Booking.check_out_date > check_in)
            .group_by(models.Booking.room_id)
            .subquery()
        )

        room_rows = (
            db.query(
                models.Room,
                func.coalesce(
                    booking_count_table.c.bookings_for_dates, #? get bookings_for_dates column from the temporary subquery table
                    0
                ).label("bookings_for_dates")
            )
            .outerjoin(
                booking_count_table,
                models.Room.id == booking_count_table.c.room_id
            )
            .filter(models.Room.hotel_id == hotel_id)
            .filter(models.Room.max_guests >= guests)
            .all()
        )

        rooms = []

        for room, bookings_for_dates in room_rows:
            room.bookings_for_dates = bookings_for_dates
            room.available_inventory = room.total_inventory - bookings_for_dates
            room.available = room.available_inventory > 0

            rooms.append(room)

            # if room.available:
            #     rooms.append(room)

    else:
        rooms = (
            db.query(models.Room)
            .filter(models.Room.hotel_id == hotel_id)
            .filter(models.Room.max_guests >= guests)
            .all()
        )

        for room in rooms:
            room.bookings_for_dates = 0
            room.available_inventory = room.total_inventory
            room.available = True

    return templates.TemplateResponse(
        request,
        "hotel_info.html",
        {
            "request": request,
            "check_in": check_in,
            "check_out": check_out,
            "hotel": hotel,
            "rooms": rooms,
            "guests": guests,
        },
    )

@app.get("/search", response_class=HTMLResponse)
def search_hotels(request: Request, city: str = "", guests: int = 1,
                        check_in: date | None = None,
                        check_out: date | None = None,
                        db: Session = Depends(get_db)):
    hotels = (
        db.query(models.Hotel)
        .join(models.Room)
        .filter(models.Hotel.city.ilike(f"%{city}%"))
        .filter(models.Room.max_guests >= guests)
        .distinct()
        .all()
    )


    for hotel in hotels:
        rooms = (
            db.query(models.Room)
            .filter(models.Room.hotel_id == hotel.id)
            .filter(models.Room.max_guests >= guests)
            .all()
        )

        hotel.starting_price = calculate_starting_price(rooms)

    return templates.TemplateResponse(
        request,
        "search_results.html",
        {
            "request": request,
            "hotels": hotels,
            "search_city": city,
            "check_in": check_in,
            "check_out": check_out,
            "guests": guests,

        },
    )

@app.get("/booking/rooms/{room_id}", response_class=HTMLResponse, include_in_schema=False)
def booking_page(request: Request, room_id: int, check_in: date | None = None, check_out: date | None = None, guests: int = 1, db: Session = Depends(get_db)):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()

    if room is None:
        raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Room not found"
    )

    hotel = db.query(models.Hotel).filter(models.Hotel.id == room.hotel_id).first()


    if hotel is None:
        raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Hotel not found"
    )


    nights = calculate_nights(check_in, check_out)
    total_price = calculate_total_price(room.price_per_night, nights) if nights > 0 else 0


    return templates.TemplateResponse(
    request,
    "booking.html",
    {
        "request": request,
        "hotel": hotel,
        "room": room,
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
        "nights": nights,
        "total_price": total_price,
    },
        )

@app.post("/booking/rooms/{room_id}", include_in_schema=False)
def submit_booking_form(
    room_id: int,
    guest_name: str = Form(...),
    guest_email: str = Form(...),
    check_in_date: date = Form(...),
    check_out_date: date = Form(...),
    number_of_guests: int = Form(...),
    db: Session = Depends(get_db),
):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()

    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    if check_out_date <= check_in_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Check-out date must be after check-in date"
        )

    if number_of_guests > room.max_guests:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Number of guests exceeds room capacity"
        )

    available_inventory = calculate_available_inventory(
    db=db,
    room_id=room_id,
    check_in_date=check_in_date,
    check_out_date=check_out_date,
    )

    if available_inventory <= 0:
        raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No rooms available for these dates"
    )

    number_of_nights = calculate_nights(check_in_date, check_out_date)
    price_per_night = room.price_per_night
    total_price = calculate_total_price(price_per_night, number_of_nights)

    new_booking = models.Booking(
        room_id=room_id,
        guest_name=guest_name,
        guest_email=guest_email,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        number_of_guests=number_of_guests,
        number_of_nights=number_of_nights,
        price_per_night=price_per_night,
        total_price=total_price,
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return RedirectResponse(
        url=f"/booking/confirmation/{new_booking.id}",
        status_code=status.HTTP_303_SEE_OTHER
    )

@app.get("/booking/confirmation/{booking_id}", include_in_schema=False)
def booking_confirmation_page(request: Request, booking_id: int, db: Session = Depends(get_db)):

    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()

    if booking is None:
        raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Booking not found"
    )


    return templates.TemplateResponse(
        request,
        "booking_confirmation_page.html",
        {
            "request": request,
            "booking": booking,
            "room": booking.room,
            "hotel": booking.room.hotel,
        },
    )


#! Error handling the 404
@app.exception_handler(StarletteHTTPException)
def general_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occured. Please check request again"
    )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )

#! Validation Error Handling
@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "title": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "message": "Invalid request. Please check the hotel link and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )