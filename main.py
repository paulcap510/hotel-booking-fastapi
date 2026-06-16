from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import Session
from routers import hotels, rooms

import models
from database import engine, Base, get_db

from schemas import HotelCreate, HotelResponse, RoomCreate, RoomResponse

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(hotels.router)
app.include_router(rooms.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

def load_hotels():
    with open("data/hotels.json", "r") as file:
        hotels = json.load(file)
    return hotels

@app.get("/", response_class=HTMLResponse)
def home(request:Request, db: Session = Depends(get_db)):
    hotels = db.query(models.Hotel).all()

    return templates.TemplateResponse(request, "home.html",
                                      {
                                          "request": request,
                                          "hotels": hotels,
                                      })

@app.get("/hotel_info/{hotel_id}", response_class=HTMLResponse, include_in_schema=False)
def hotel_info(request: Request, hotel_id: int, db: Session = Depends(get_db)):
    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Hotel not found"
        )

    rooms = db.query(models.Room).filter(models.Room.hotel_id == hotel_id).all()

    return templates.TemplateResponse(
        request, 'hotel_info.html',
                {
            "request": request,
            "hotel": hotel,
            "rooms": rooms,
        },
    )


@app.get("/search", response_class=HTMLResponse)
def search_hotels(request: Request, city: str = "", guests: int = 1, db: Session = Depends(get_db)):
    hotels = (
        db.query(models.Hotel)
        .join(models.Room)
        .filter(models.Hotel.city.ilike(f"%{city}%"))
        .filter(models.Room.max_guests >= guests)
        .distinct()
        .all()
    )

    return templates.TemplateResponse(
        request,
        "search_results.html",
        {
            "request": request,
            "hotels": hotels,
            "search_city": city,
            "guests": guests,
        },
    )



# @app.put("/api/hotels/{hotel_id}", response_model=HotelResponse)
# def update_hotel(hotel_id: int, updated_hotel: HotelCreate, db: Session = Depends(get_db)):
#     hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

#     if hotel is None:
#         raise HTTPException(
#             status_code = status.HTTP_404_NOT_FOUND,
#             detail = "Hotel not found"
#         )

#     hotel.name = updated_hotel.name
#     hotel.description = updated_hotel.description
#     hotel.price = updated_hotel.price
#     hotel.image_path = updated_hotel.image_path

#     db.commit()
#     db.refresh(hotel)
#     return hotel

# @app.put("/api/rooms/{room_id}", response_model=RoomResponse)
# def update_room(room_id: int, updated_room: RoomCreate, db: Session=Depends(get_db)):
#     room = db.query(models.Room).filter(models.Room.id == room_id).first()

#     if room is None:
#         raise HTTPException(
#             status_code = status.HTTP_404_NOT_FOUND,
#             detail = "Room not found"
#         )

#     room.room_type = updated_room.room_type
#     room.price = updated_room.price
#     room.max_guests = updated_room.max_guests
#     room.available = updated_room.available

#     db.commit()
#     db.refresh(room)
#     return room


# @app.get("/api/hotels/{hotel_id}", response_model=HotelResponse)
# def get_hotel(hotel_id: int, db: Session = Depends(get_db)):
#     hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

#     if hotel is None:
#         raise HTTPException(
#             status_code = status.HTTP_404_NOT_FOUND,
#             detail = "Hotel not found"
#         )
#     return hotel

# @app.get("/api/hotels", response_model=list[HotelResponse])
# def get_hotels(hotel_id: int, db: Session = Depends(get_db)):
#     # Depends(get_db) tells FastAPI to run get_db() before this route runs.
#     # get_db() creates a database session and gives it to this route as db.
#     # Session is a type hint saying db should be a SQLAlchemy Session.
#     hotels = db.query(models.Hotel).all()
#     return hotels

# @app.get("/api/{hotel_id}/rooms", response_model=list[RoomResponse])
# def get_rooms_for_hotel(hotel_id: int, db: Session = Depends(get_db)):
#     hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

#     if hotel is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Hotel not found"
#         )

#     rooms = db.query(models.Room).filter(models.Room.hotel_id == hotel_id).all()

#     return rooms



# @app.post("/api/hotels", response_model=HotelResponse, status_code=status.HTTP_201_CREATED)
# def create_hotel(hotel: HotelCreate, db: Session = Depends(get_db)):
#     new_hotel = models.Hotel(name=hotel.name, description=hotel.description, price=hotel.price, image_path=hotel.image_path)

#     db.add(new_hotel)
#     db.commit()
#     db.refresh(new_hotel)

#     return new_hotel

# @app.post("/api/hotels/{hotel_id}/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
# def create_room(hotel_id: int, room: RoomCreate, db: Session = Depends(get_db)):
#     hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

#     if hotel is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Hotel not found"
#             )

#     new_room = models.Room(
#         hotel_id=hotel_id,
#         room_type=room.room_type,
#         price=room.price,
#         max_guests=room.max_guests,
#         available=room.available,
#     )

#     db.add(new_room)
#     db.commit()
#     db.refresh(new_room)

#     return new_room


# @app.delete("/api/rooms/{room_id}")
# def delete_room(room_id: int, db: Session = Depends(get_db)):
#     room = db.query(models.Room).filter(models.Room.id == room_id).first()
#     if room is None:
#         raise HTTPException(
#             status_code = status.HTTP_404_NOT_FOUND,
#             detail = "Hotel not found"
#         )
#     db.delete(room)
#     db.commit()
#     return {"message": "ROOM deleted successfully"}


# @app.delete("/api/hotels/{hotel_id}")
# def delete_hotel(hotel_id: int, db: Session = Depends(get_db)):
#     hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

#     if hotel is None:
#         raise HTTPException(
#             status_code = status.HTTP_404_NOT_FOUND,
#             detail = "Hotel not found"
#         )

#     db.delete(hotel)
#     db.commit()
#     return {"message": "Hotel deleted successfully"}





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