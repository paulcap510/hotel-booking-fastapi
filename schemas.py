from pydantic import BaseModel, ConfigDict, Field, EmailStr
from datetime import date
from utils.booking_status import BookingStatus


#! Hotels
class HotelBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)
    image_path: str = Field(min_length=1)
    city: str = Field(min_length=1)

class HotelCreate(HotelBase):
    pass

class HostHotelUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    image_path: str | None = None
    city: str | None = None

class HotelResponse(HotelBase):
    id: int

    model_config = ConfigDict(from_attributes=True) #Allow Pydantic/FastAPI to turn SQLAlchemy objects into API responses



#! ROOMS
class RoomBase(BaseModel):
    room_type: str = Field(min_length=1, max_length=100)
    price_per_night: int = Field(gt=0)
    max_guests: int = Field(gt=0)
    # available: bool

class RoomCreate(RoomBase):
    pass

class RoomResponse(RoomBase):
    id: int
    hotel_id: int
    model_config = ConfigDict(from_attributes=True)


#! BOOKINGS
class BookingBase(BaseModel):
    guest_name: str = Field(min_length=1, max_length=100)
    guest_email: EmailStr
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
    booking_status: BookingStatus

    model_config = ConfigDict(from_attributes=True)

class BookingContactUpdate(BaseModel):
    guest_name: str = Field(min_length=1, max_length=100)
    guest_email: EmailStr

class MyBookingsResponse(BaseModel):
    upcoming_bookings: list[BookingResponse]
    current_bookings: list[BookingResponse]
    past_bookings: list[BookingResponse]


#! USER
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str
    #* TODO: Implmenet min_length = 8
    # password: str = Field(min_length=8)

class UserPrivateResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)

class UserPublicResponse(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = None


#! TOKEN
class Token(BaseModel):
    access_token: str
    token_type: str

#! EMAIL UPDATE
class EmailUpdate(BaseModel):
    email: EmailStr


#! PASSWORD RESET
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(min_length=8)





class ExperienceBase(BaseModel):
    title: str
    description: str
    price_per_person: int
    location: str

class ExperienceCreate(ExperienceBase):
    pass

class ExperienceResponse(ExperienceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_path: str
    user_id: int