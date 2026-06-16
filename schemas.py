from pydantic import BaseModel, ConfigDict, Field
#* TODO: Add Bookings and User models

class HotelBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)
    price: str = Field(min_length=1)
    image_path: str = Field(min_length=1)
    #** Adding city
    city: str = Field(min_length=1)

class HotelCreate(HotelBase):
    pass

class HotelResponse(HotelBase):
    id: int

    model_config = ConfigDict(from_attributes=True) #Allow Pydantic/FastAPI to turn SQLAlchemy objects into API responses


class RoomBase(BaseModel):
    room_type: str = Field(min_length=1, max_length=100)
    price: str = Field(min_length=1)
    max_guests: int = Field(gt=0)
    available: bool

class RoomCreate(RoomBase):
    pass

class RoomResponse(RoomBase):
    id: int
    hotel_id: int
    model_config = ConfigDict(from_attributes=True)