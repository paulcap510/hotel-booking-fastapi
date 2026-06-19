from pydantic import BaseModel, ConfigDict, Field
from datetime import date

#* TODO: Add Bookings and User models

class HotelBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)
    # price: str = Field(min_length=1)
    image_path: str = Field(min_length=1)
    city: str = Field(min_length=1)

class HotelCreate(HotelBase):
    pass

class HotelResponse(HotelBase):
    id: int

    model_config = ConfigDict(from_attributes=True) #Allow Pydantic/FastAPI to turn SQLAlchemy objects into API responses


class RoomBase(BaseModel):
    room_type: str = Field(min_length=1, max_length=100)
    price_per_night: int = Field(gt=0)
    max_guests: int = Field(gt=0)
    available: bool

class RoomCreate(RoomBase):
    pass

class RoomResponse(RoomBase):
    id: int
    hotel_id: int
    model_config = ConfigDict(from_attributes=True)

class BookingBase(BaseModel):
    guest_name: str = Field(min_length=1, max_length=100)
    guest_email: str = Field(min_length=1, max_length=100)
    check_in_date: date
    check_out_date: date
    number_of_guests: int = Field(gt=0)


class BookingCreate(BookingBase):
    pass


class BookingResponse(BookingBase):
    id: int
    room_id: int
    number_of_nights: int
    price_per_night: int
    total_price: int

    model_config = ConfigDict(from_attributes=True)