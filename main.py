from fastapi import FastAPI, Request, HTTPException, status, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from routers import hotels, rooms, bookings, users, host, experiences, reviews
from datetime import date
import random

import models
from database import get_db, SessionLocal

from utils.pricing import calculate_nights, calculate_total_price, calculate_starting_price
from utils.inventory import calculate_available_inventory
from utils.booking_status import BookingStatus
from utils.booking_queries import get_bookings_for_user
from utils.reviews import get_hotel_average_rating, get_recent_hotel_reviews
from routers.users import get_current_user
from auth import get_user_id_from_session, create_reset_token, get_user_id_from_reset_token, delete_reset_token, hash_password



app = FastAPI()


@app.middleware("http")
async def add_current_user_to_request(request: Request, call_next):
    db = SessionLocal()
    try:
        session_id = request.cookies.get("session_id")
        user_id = get_user_id_from_session(session_id)

        if user_id:
            request.state.user = db.query(models.User).filter(models.User.id == user_id).first()
        else:
            request.state.user = None
    finally:
        db.close()

    response = await call_next(request)
    return response


app.include_router(hotels.router)
app.include_router(rooms.router)
app.include_router(bookings.router)
app.include_router(users.router)
app.include_router(host.router)
app.include_router(experiences.router)
app.include_router(reviews.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def home(request:Request, db: Session = Depends(get_db)):
    hotels = db.query(models.Hotel).all()

    for hotel in hotels:
        rooms = (db.query(models.Room).filter(models.Room.hotel_id == hotel.id).all())
        hotel.starting_price = calculate_starting_price(rooms)

    active_experiences = (
        db.query(models.Experience)
        .filter(models.Experience.is_active == True)
        .all()
    )
    experiences = random.sample(active_experiences, min(3, len(active_experiences)))

    return templates.TemplateResponse(request, "home.html",
                                      {
                                        "request": request,
                                        "hotels": hotels,
                                        "experiences": experiences,
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

    average_rating, review_count = get_hotel_average_rating(db, hotel_id)
    recent_reviews = get_recent_hotel_reviews(db, hotel_id)

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
            "average_rating": average_rating,
            "review_count": review_count,
            "recent_reviews": recent_reviews,
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
        .filter(models.Hotel.is_active == True)
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

        average_rating, review_count = get_hotel_average_rating(db, hotel.id)
        hotel.average_rating = average_rating
        hotel.review_count = review_count

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


#! moving to routers/bookings
# @app.post("/booking/rooms/{room_id}", include_in_schema=False)
# def submit_booking_form(
#     room_id: int,
#     guest_name: str = Form(...),
#     guest_email: str = Form(...),
#     check_in_date: date = Form(...),
#     check_out_date: date = Form(...),
#     number_of_guests: int = Form(...),
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_user),
# ):

#     room = db.query(models.Room).filter(models.Room.id == room_id).first()

#     if room is None:
#         raise HTTPException(status_code=404, detail="Room not found")

#     hotel = db.query(models.Hotel).filter(models.Hotel.id == room.hotel_id).first()

#     if hotel is None:
#         raise HTTPException(status_code=404, detail="Hotel not found")

#     if not hotel.is_active:
#         return RedirectResponse(
#             url=f"/hotels/{hotel.id}?error=This+property+is+no+longer+accepting+bookings",
#             status_code=status.HTTP_303_SEE_OTHER,
#         )

#     new_booking = create_booking_for_user(
#         db=db,
#         room_id=room_id,
#         user_id=current_user.id,
#         guest_name=guest_name,
#         guest_email=guest_email,
#         check_in_date=check_in_date,
#         check_out_date=check_out_date,
#         number_of_guests=number_of_guests,
#     )

#     return RedirectResponse(
#         url=f"/booking/confirmation/{new_booking.id}",
#         status_code=status.HTTP_303_SEE_OTHER,
#     )

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



@app.get("/bookings", response_class=HTMLResponse, include_in_schema=False)
def my_bookings_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    upcoming, current, past, cancelled = get_bookings_for_user(db, current_user.id)
    return templates.TemplateResponse(request, "my_bookings.html", {
        "request": request,
        "upcoming_bookings": upcoming,
        "current_bookings": current,
        "past_bookings": past,
        "cancelled_bookings": cancelled,
        "today": date.today(),
    })


@app.get("/support", response_class=HTMLResponse, include_in_schema=False)
def support_page(request: Request):
    return templates.TemplateResponse(request, "support.html", {"request": request})






@app.get("/bookings/{booking_id}", response_class=HTMLResponse, include_in_schema=False)
def booking_detail_page(
    booking_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()

    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this booking")

    return templates.TemplateResponse(request, "booking_detail.html", {
        "request": request,
        "booking": booking,
        "room": booking.room,
        "hotel": booking.room.hotel,
        "today": date.today(),
    })


@app.get("/bookings/{booking_id}/manage", response_class=HTMLResponse, include_in_schema=False)
def manage_booking_page(
    booking_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)):

    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()

    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this booking")

    response = templates.TemplateResponse(request, "manage_booking.html", {
        "request": request,
        "booking": booking,
        "room": booking.room,
        "hotel": booking.room.hotel,
    })
    response.headers["Cache-Control"] = "no-store"
    return response


@app.post("/bookings/{booking_id}/cancel", include_in_schema=False)
def cancel_booking_action(
    booking_id: int,
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

    booking.booking_status = BookingStatus.cancelled

    db.commit()
    return RedirectResponse(
        url=f"/bookings/{booking_id}/manage",
        status_code=status.HTTP_303_SEE_OTHER,
    )




@app.post("/bookings/{booking_id}/update-contact", include_in_schema=False)
def update_booking_contact_form(
    booking_id: int,
    guest_name: str = Form(...),
    guest_email: str = Form(...),
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

    booking.guest_name = guest_name
    booking.guest_email = guest_email

    db.commit()

    return RedirectResponse(
        url=f"/bookings/{booking_id}/manage",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@app.post("/bookings/{booking_id}/update-dates", include_in_schema=False)
def update_booking_dates_form(
    booking_id: int,
    check_in_date: date = Form(...),
    check_out_date: date = Form(...),
    number_of_guests: int = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()

    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this booking")

    if booking.booking_status == BookingStatus.completed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot update a completed booking")

    if booking.booking_status == BookingStatus.cancelled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot update a cancelled booking")

    room = booking.room

    if check_out_date <= check_in_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Check-out date must be after check-in date")

    if number_of_guests > room.max_guests:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Number of guests exceeds room capacity")

    try:
        available_inventory = calculate_available_inventory(
            db=db,
            room_id=booking.room_id,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            exclude_booking_id=booking_id,
        )

        if available_inventory <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No rooms available for these dates")

        number_of_nights = calculate_nights(check_in_date, check_out_date)
        total_price = calculate_total_price(booking.price_per_night, number_of_nights)

        booking.check_in_date = check_in_date
        booking.check_out_date = check_out_date
        booking.number_of_guests = number_of_guests
        booking.number_of_nights = number_of_nights
        booking.total_price = total_price

        db.commit()
    except Exception:
        db.rollback()
        raise

    return RedirectResponse(
        url=f"/bookings/{booking_id}/manage",
        status_code=status.HTTP_303_SEE_OTHER,
    )




@app.get("/account/email", response_class=HTMLResponse, include_in_schema=False)
def update_email_page(
    request: Request,
    current_user: models.User = Depends(get_current_user),
):
    return templates.TemplateResponse(request, "update_email.html", {
        "request": request,
        "current_user": current_user,
    })

@app.post("/account/email", include_in_schema=False)
def update_email_form(
    email: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    existing_email = (
        db.query(models.User)
        .filter(func.lower(models.User.email) == email.lower())
        .filter(models.User.id != current_user.id)
        .first()
    )

    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")

    current_user.email = email.lower()
    db.commit()

    return RedirectResponse(
        url="/?email_updated=true",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@app.get("/account", response_class=HTMLResponse, include_in_schema=False)
def account_page(
    request: Request,
    current_user: models.User = Depends(get_current_user),
):
    return templates.TemplateResponse(request, "account.html", {
        "request": request,
        "current_user": current_user,
    })



@app.get("/account/forgot-password", response_class=HTMLResponse, include_in_schema=False)
def forgot_password_page(request: Request):
    return templates.TemplateResponse(request, "forgot_password.html", {
        "request": request,
    })


#* Form that processes the user input
@app.post("/account/forgot-password", include_in_schema=False)
def forgot_password_form(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(func.lower(models.User.email) == email.lower()).first()

    if user:
        token = create_reset_token(user.id)
        reset_link = f"http://127.0.0.1:8000/account/reset-password?token={token}"
        print(f"\n[DEV MODE] Password reset link for {user.email}:\n{reset_link}\n")

    return templates.TemplateResponse(request, "forgot_password.html", {
        "request": request,
        "message": "If that email is registered, a reset link has been sent.",
    })





@app.get("/account/reset-password", response_class=HTMLResponse, include_in_schema=False)
def reset_password_page(
    request: Request,
    token: str,
):
    user_id = get_user_id_from_reset_token(token)

    if user_id is None:
        return templates.TemplateResponse(request, "reset_password.html", {
            "request": request,
            "error": "This reset link is invalid or has expired.",
            "token": None,
        })

    return templates.TemplateResponse(request, "reset_password.html", {
        "request": request,
        "error": None,
        "token": token,
    })


#* backend for handling form submission
@app.post("/account/reset-password", include_in_schema=False)
def reset_password_form(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    if new_password != confirm_password:
        return templates.TemplateResponse(request, "reset_password.html", {
            "request": request,
            "error": None,
            "token": token,
            "password_error": "Passwords do not match.",
        })

    user_id = get_user_id_from_reset_token(token)

    if user_id is None:
        return templates.TemplateResponse(request, "reset_password.html", {
            "request": request,
            "error": "This reset link is invalid or has expired.",
            "token": None,
                        "password_error": None,
        })

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user is None:
        return templates.TemplateResponse(request, "reset_password.html", {
            "request": request,
            "error": "User not found.",
            "token": None,
            "password_error": None,
        })

    user.hashed_password = hash_password(new_password)
    db.commit()

    delete_reset_token(token)

    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

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