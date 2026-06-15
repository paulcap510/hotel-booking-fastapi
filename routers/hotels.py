from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import HotelCreate, HotelResponse


router = APIRouter(
    prefix="/api/hotels",
    tags=["Hotels"]
)


@router.get("", response_model=list[HotelResponse])
def get_hotels(db: Session = Depends(get_db)):
    hotels = db.query(models.Hotel).all()
    return hotels


@router.get("/{hotel_id}", response_model=HotelResponse)
def get_hotel(hotel_id: int, db: Session = Depends(get_db)):
    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotel not found"
        )

    return hotel


@router.post("", response_model=HotelResponse, status_code=status.HTTP_201_CREATED)
def create_hotel(hotel: HotelCreate, db: Session = Depends(get_db)):
    new_hotel = models.Hotel(
        name=hotel.name,
        description=hotel.description,
        price=hotel.price,
        image_path=hotel.image_path,
    )

    db.add(new_hotel)
    db.commit()
    db.refresh(new_hotel)

    return new_hotel

@router.put("/{hotel_id}", response_model=HotelResponse)
def update_hotel(hotel_id: int, updated_hotel: HotelCreate, db: Session = Depends(get_db)):
    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotel not found"
        )

    hotel.name = updated_hotel.name
    hotel.description = updated_hotel.description
    hotel.price = updated_hotel.price
    hotel.image_path = updated_hotel.image_path

    db.commit()
    db.refresh(hotel)

    return hotel

@router.delete("/{hotel_id}")
def delete_hotel(hotel_id: int, db: Session = Depends(get_db)):
    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotel not found"
        )

    db.delete(hotel)
    db.commit()

    return {"message": "Hotel deleted successfully"}