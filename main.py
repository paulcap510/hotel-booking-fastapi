from fastapi import FastAPI, Request, HTTPException, status, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Annotated
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from routers import hotels, rooms, bookings, users
from datetime import date

import models
from database import engine, Base, get_db

from utils.pricing import calculate_nights, calculate_total_price, calculate_starting_price
from utils.inventory import calculate_available_inventory
from utils.booking_status import BookingStatus

from schemas import HotelCreate, HotelResponse, RoomCreate, RoomResponse, HotelSearchResult


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(hotels.router)
app.include_router(rooms.router)
app.include_router(bookings.router)
app.include_router(users.router)

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


#! Get Hotel Details API Route
@app.get("/api/hotels/{hotel_id}/details")
def get_hotel_details_api(
    hotel_id: int,
    guests: int = 1,
    check_in: date | None = None,
    check_out: date | None = None,
    db: Session = Depends(get_db),
):
    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotel not found"
        )

    if check_in and check_out:
        bookings_for_dates = (
            db.query(
                models.Booking.room_id.label("room_id"),
                func.count(models.Booking.id).label("booked_count"),
            )
            .filter(models.Booking.booking_status == "confirmed")
            .filter(models.Booking.check_in_date < check_out)
            .filter(models.Booking.check_out_date > check_in)
            .group_by(models.Booking.room_id)
            .subquery()
        )

        room_rows = (
            db.query(
                models.Room,
                func.coalesce(
                    bookings_for_dates.c.booked_count,
                    0
                ).label("booked_count")
            )
            .outerjoin(
                bookings_for_dates,
                models.Room.id == bookings_for_dates.c.room_id
            )
            .filter(models.Room.hotel_id == hotel_id)
            .filter(models.Room.max_guests >= guests)
            .all()
        )

    else:
        room_rows = (
            db.query(
                models.Room,
                func.coalesce(0, 0).label("booked_count")
            )
            .filter(models.Room.hotel_id == hotel_id)
            .filter(models.Room.max_guests >= guests)
            .all()
        )

    rooms = []

    for room, booked_count in room_rows:
        available_inventory = room.total_inventory - booked_count

        rooms.append({
            "id": room.id,
            "room_type": room.room_type,
            "price_per_night": room.price_per_night,
            "max_guests": room.max_guests,
            "total_inventory": room.total_inventory,
            "booked_count": booked_count,
            "available_inventory": available_inventory,
            "available": available_inventory > 0,
        })

    return {
        "id": hotel.id,
        "name": hotel.name,
        "description": hotel.description,
        "image_path": hotel.image_path,
        "city": hotel.city,
        "rooms": rooms,
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
    }



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
            .filter(models.Booking.booking_status == models.BookingStatus.confirmed)
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


#? Updated Api Search Route
@app.get("/api/search", response_model=list[HotelSearchResult])
def search_hotels_api(
    city: str,
    check_in: date,
    check_out: date,
    guests: int = 1,
    db: Session = Depends(get_db),
):
    # 1. Validate search inputs
    if check_out <= check_in:
        raise HTTPException(
            status_code=400,
            detail="Check-out date must be after check-in date."
        )

    if guests < 1:
        raise HTTPException(
            status_code=400,
            detail="Guests must be at least 1."
        )

    # 2. Count bookings that overlap the requested date range
    bookings_for_dates = (
        db.query(
            models.Booking.room_id.label("room_id"),
            func.count(models.Booking.id).label("booked_count"),
        )
        .filter(models.Booking.check_in_date < check_out)
        .filter(models.Booking.check_out_date > check_in)
        .filter(models.Booking.booking_status == "confirmed")
        .group_by(models.Booking.room_id)
        .subquery()
    )

    # 3. Find hotels with rooms that still have inventory left
    rows = (
        db.query(
            models.Hotel.id.label("id"),
            models.Hotel.name.label("name"),
            models.Hotel.description.label("description"),
            models.Hotel.image_path.label("image_path"),
            models.Hotel.city.label("city"),
            func.min(models.Room.price_per_night).label("starting_price"),
            func.count(models.Room.id).label("available_rooms_count"),
        )
        .join(models.Room, models.Room.hotel_id == models.Hotel.id)
        .outerjoin(
            bookings_for_dates,
            bookings_for_dates.c.room_id == models.Room.id,
        )
        .filter(models.Hotel.city.ilike(f"%{city}%"))
        .filter(models.Room.max_guests >= guests)
        .filter(
            models.Room.total_inventory
            > func.coalesce(bookings_for_dates.c.booked_count, 0)
        )
        .group_by(
            models.Hotel.id,
            models.Hotel.name,
            models.Hotel.description,
            models.Hotel.image_path,
            models.Hotel.city,
        )
        .all()
    )

    return [dict(row._mapping) for row in rows]


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




@app.get("/signup")
def signup_page(request: Request):
    return templates.TemplateResponse(
        request,
        "signup.html",
        {"request": request},
    )

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request, "login.html", {"request": request}
    )



#! Error handling the 404
@app.exception_handler(StarletteHTTPException)
def general_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occured. Please check request again"
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
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
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exception.errors()},
        )

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