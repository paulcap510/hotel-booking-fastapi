from database import Base
from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship
from datetime import date
from sqlalchemy import Integer, String, Boolean, ForeignKey, Date
from enum import Enum
from utils.booking_status import BookingStatus


class Hotel(Base):
    __tablename__ = "hotels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    image_path: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)

    rooms = relationship("Room", back_populates="hotel", cascade="all, delete-orphan")

class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hotel_id: Mapped[int] = mapped_column(ForeignKey("hotels.id"), nullable=False)
    room_type: Mapped[str] = mapped_column(String(100), nullable=False)
    price_per_night:Mapped[int] = mapped_column(Integer, nullable=False)
    max_guests: Mapped[int] = mapped_column(Integer, nullable=False)
    # available: Mapped[bool] = mapped_column(Boolean, default=True)
    total_inventory: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


    hotel = relationship("Hotel", back_populates="rooms")
    bookings = relationship("Booking", back_populates="room", cascade="all, delete-orphan")

class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    guest_name: Mapped[str] = mapped_column(String(100), nullable=False)
    guest_email: Mapped[str] = mapped_column(String(100), nullable=False)
    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[date] = mapped_column(Date, nullable=False)
    number_of_guests: Mapped[int] = mapped_column(Integer, nullable=False)
    number_of_nights: Mapped[int] = mapped_column(Integer, nullable=False)
    price_per_night: Mapped[int] = mapped_column(Integer, nullable=False)
    total_price: Mapped[int] = mapped_column(Integer, nullable=False)
    booking_status: Mapped[str] = mapped_column(String(20), nullable=False, default=BookingStatus.confirmed)

    room = relationship("Room", back_populates="bookings")
    user = relationship("User", back_populates="bookings")


class User(Base):
    __tablename__ = "users"

    #** TODO: later allow users to reserve rooms as guests
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")