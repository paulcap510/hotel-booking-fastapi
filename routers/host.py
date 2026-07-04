from fastapi import APIRouter, Request, Depends, status, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from auth import get_user_id_from_session
from fastapi.templating import Jinja2Templates
import shutil
import models
from pathlib import Path



router = APIRouter(
    prefix="/host",
    tags=['Host']
)

templates = Jinja2Templates(directory="templates")


@router.get("/properties/{hotel_id}/bookings")
def host_manage_bookings_page(request: Request, hotel_id: int, db: Session = Depends(get_db)):

    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+manage+your+property",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(status_code=404, detail="Property not found")

    if hotel.owner_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this property")

    bookings = (
        db.query(models.Booking)
        .join(models.Room)
        .filter(models.Room.hotel_id == hotel_id)
        .order_by(models.Booking.check_in_date.asc())
        .all()
    )

    return templates.TemplateResponse(request, "host_manage_bookings_page.html",
            {
                "hotel": hotel,
                "bookings": bookings,
            })



@router.post("/properties/{hotel_id}/rooms/{room_id}/delete")
def host_page_delete_room(request: Request, hotel_id: int, room_id: int, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+manage+your+property",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(status_code=404, detail="Property not found")

    if hotel.owner_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this property")

    room = db.query(models.Room).filter(models.Room.id == room_id).first()

    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    active_bookings = db.query(models.Booking).filter(
        models.Booking.room_id == room_id,
        models.Booking.booking_status != "cancelled"
    ).first()

    if active_bookings:
        return RedirectResponse(
            url=f"/host/properties/{hotel_id}/manage?error=Cannot+delete+a+room+with+active+bookings",
            status_code=status.HTTP_303_SEE_OTHER,
    )

    db.delete(room)
    db.commit()

    return RedirectResponse(
        url=f"/host/properties/{hotel_id}/manage?message=Room+deleted+successfully",
        status_code=status.HTTP_303_SEE_OTHER,
    )



@router.get("/properties/{hotel_id}/rooms/{room_id}/edit")
def edit_room_form(request: Request, hotel_id: int, room_id: int, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+manage+your+property",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(status_code=404, detail="Property not found")

    if hotel.owner_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this property")

    room = db.query(models.Room).filter(models.Room.id == room_id).first()

    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    return templates.TemplateResponse(request, "edit_room.html",
            {
                "hotel": hotel,
                "room": room,
            })


@router.get("/properties/{hotel_id}/manage")
def manage_specific_property_page(request: Request, hotel_id: int, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+manage+your+property",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(status_code=404, detail="Property not found")

    if hotel.owner_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this property")

    rooms = db.query(models.Room).filter(models.Room.hotel_id == hotel_id).all()

    return templates.TemplateResponse(
        request, "manage_property.html", {"hotel": hotel, "rooms": rooms}
    )


@router.get("/properties/{hotel_id}/rooms/new")
def new_room_form(request: Request, hotel_id: int, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+manage+your+property",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(status_code=404, detail="Property not found")

    if hotel.owner_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this property")

    return templates.TemplateResponse(
        request, "add_room.html", {"hotel": hotel}
    )


@router.post("/properties/{hotel_id}/edit")
def edit_property(
    request: Request,
    hotel_id: int,
    name: str = Form(...),
    city: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db),
):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+manage+your+property",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(status_code=404, detail="Property not found")

    if hotel.owner_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this property")

    hotel.name = name
    hotel.city = city
    hotel.description = description

    db.commit()

    return RedirectResponse(
        url=f"/host/properties/{hotel_id}/manage?message=Property+updated+successfully",
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.post("/properties/{hotel_id}/rooms/{room_id}/edit")
def edit_room(
    request: Request,
    hotel_id: int,
    room_id: int,
    room_type: str = Form(...),
    price_per_night: int = Form(...),
    max_guests: int = Form(...),
    total_inventory: int = Form(1),
    db: Session = Depends(get_db),
):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+manage+your+property",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(status_code=404, detail="Property not found")

    if hotel.owner_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this property")

    room = db.query(models.Room).filter(models.Room.id == room_id).first()

    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    room.room_type = room_type
    room.price_per_night = price_per_night
    room.max_guests = max_guests
    room.total_inventory = total_inventory

    db.commit()

    return RedirectResponse(
        url=f"/host/properties/{hotel_id}/manage?message=Room+updated+successfully",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/properties/{hotel_id}/rooms/new")
def create_room(
    request: Request,
    hotel_id: int,
    room_type: str = Form(...),
    price_per_night: int = Form(...),
    max_guests: int = Form(...),
    total_inventory: int = Form(1),
    db: Session = Depends(get_db),
):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+manage+your+property",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(status_code=404, detail="Property not found")

    if hotel.owner_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this property")

    new_room = models.Room(
        hotel_id=hotel.id,
        room_type=room_type,
        price_per_night=price_per_night,
        max_guests=max_guests,
        total_inventory=total_inventory,
    )

    db.add(new_room)
    db.commit()

    return RedirectResponse(
        url=f"/host/properties/{hotel_id}/manage?message=Room+added+successfully",
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.post("/properties/new", include_in_schema=False)
def add_new_property(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    image: UploadFile = File(...),
    city: str = Form(...),
    db: Session = Depends(get_db),
):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+list+your+property",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user.is_host:
        return RedirectResponse(
            url="/host/become",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    upload_dir = Path("static/uploads/hotels")
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / image.filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    image_path = f"uploads/hotels/{image.filename}"

    new_hotel = models.Hotel(
        name=name,
        description=description,
        image_path=image_path,
        city=city,
        owner_id=user_id,
    )

    db.add(new_hotel)
    db.commit()
    db.refresh(new_hotel)

    return RedirectResponse(
        url="/host/dashboard/",
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.get("/properties/manage", response_class=HTMLResponse, include_in_schema=False)
def manage_properties_page(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+list+your+property",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user.is_host:
        return RedirectResponse(
            url="/host/become",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(request, "manage_properties.html", {
        "request": request,
        "user": user,
    })

@router.get("/properties/new", response_class=HTMLResponse, include_in_schema=False)
def list_new_property_page(
    request: Request,
    db: Session = Depends(get_db),
):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+list+your+property",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user.is_host:
        return RedirectResponse(
            url="/host/become",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(request, "list_new_property.html", {
        "request": request,
        "user": user,
    })



@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def host_dashboard(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+list+your+property",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user.is_host:
        return RedirectResponse(url="/host/become", status_code=status.HTTP_303_SEE_OTHER)

    properties = db.query(models.Hotel).filter(models.Hotel.owner_id == user_id).all()

    return templates.TemplateResponse(request, "host_dashboard.html",
            {
                "request": request,
                "user": user,
                "properties": properties,
            })


@router.post("/become", include_in_schema=False)
def become_host_action(
    request: Request,
    db: Session = Depends(get_db),
):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+list+your+property",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user.is_host:
        return RedirectResponse(
            url="/host/dashboard",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    user.is_host = True
    db.commit()

    return RedirectResponse(
        url="/host/dashboard",
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.get("/become", response_class=HTMLResponse, include_in_schema=False)
def become_host(request: Request, db: Session = Depends(get_db)):

    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+list+your+property",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user.is_host:
        return RedirectResponse(
            url="/host/dashboard",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(request, "become_host.html",
            {
                "request": request,
                "user": user,
            })




@router.patch("/api/hotels/{hotel_id}/deactivate")
def deactivate_hotel(hotel_id: int, db: Session = Depends(get_db)):
    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(status_code=404, detail="Hotel not found")

    hotel.is_active = False
    db.commit()

    return {"message": "Hotel deactivated successfully"}


@router.post("/properties/{hotel_id}/deactivate")
def deactivate_property(request: Request, hotel_id: int, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+manage+your+property",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(status_code=404, detail="Property not found")

    if hotel.owner_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this property")

    hotel.is_active = False
    db.commit()

    return RedirectResponse(
        url=f"/host/properties/{hotel_id}/manage?message=Property+deactivated+successfully",
        status_code=status.HTTP_303_SEE_OTHER,
    )



@router.post("/properties/{hotel_id}/reactivate")
def reactivate_property(request: Request, hotel_id: int, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+manage+your+property",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()

    if hotel is None:
        raise HTTPException(status_code=404, detail="Property not found")

    if hotel.owner_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this property")

    hotel.is_active = True
    db.commit()

    return RedirectResponse(
        url=f"/host/dashboard?message=Property+reactivated+successfully",
        status_code=status.HTTP_303_SEE_OTHER,
    )