from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import RoomCreate, RoomResponse


router = APIRouter(
    tags=["Rooms"]
)


#! Get rooms for a hotel
@router.get("/api/hotels/{hotel_id}/rooms", response_model=list[RoomResponse])
def get_rooms_for_hotel(hotel_id: int, db: Session = Depends(get_db)):
    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotel not found"
        )

    rooms = db.query(models.Room).filter(models.Room.hotel_id == hotel_id).all()

    return rooms


#! Update
@router.put("/api/rooms/{room_id}", response_model=RoomResponse)
def update_room(room_id: int, updated_room: RoomCreate, db: Session = Depends(get_db)):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()

    if room is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Room not found"
        )

    room.room_type = updated_room.room_type
    room.price_per_night = updated_room.price_per_night
    room.max_guests = updated_room.max_guests
    room.available = updated_room.available

    db.commit()
    db.refresh(room)
    return room


#! Create a Room
@router.post("/api/hotels/{hotel_id}/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
def create_room(hotel_id: int, room: RoomCreate, db: Session = Depends(get_db)):
    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotel not found"
            )

    new_room = models.Room(
        hotel_id=hotel_id,
        room_type=room.room_type,
        price_per_night=room.price_per_night,
        max_guests=room.max_guests,
        available=room.available,
    )

    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    return new_room

#! Delete a room
@router.delete("/api/rooms/{room_id}")
def delete_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if room is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Room not found"
        )
    db.delete(room)
    db.commit()
    return {"message": "ROOM deleted successfully"}
