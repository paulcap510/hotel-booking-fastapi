from fastapi import APIRouter, Request, Depends, status, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from datetime import date

from database import get_db
from auth import get_user_id_from_session
import models

router = APIRouter(
    prefix="/bookings",
    tags=["Reviews"]
)

templates = Jinja2Templates(directory="templates")


@router.get("/{booking_id}/review", response_class=HTMLResponse, include_in_schema=False)
def submit_review_page(request: Request, booking_id: int, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+leave+a+review",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()

    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this booking")

    if booking.check_out_date > date.today():
        raise HTTPException(status_code=400, detail="You can only review a stay after checkout")

    if booking.booking_status == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot review a cancelled booking")

    existing_review = db.query(models.Review).filter(models.Review.booking_id == booking_id).first()
    if existing_review:
        raise HTTPException(status_code=400, detail="You've already reviewed this booking")

    return templates.TemplateResponse(request, "submit_review.html", {
        "booking": booking,
    })



@router.post("/{booking_id}/review")
def submit_review(
    request: Request,
    booking_id: int,
    review_score: int = Form(...),
    review_description: str = Form(...),
    db: Session = Depends(get_db),
):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+leave+a+review",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()

    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this booking")

    if booking.check_out_date > date.today():
        raise HTTPException(status_code=400, detail="You can only review a stay after checkout")

    if booking.booking_status == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot review a cancelled booking")

    if not (1 <= review_score <= 10):
        raise HTTPException(status_code=400, detail="Review score must be between 1 and 10")

    existing_review = db.query(models.Review).filter(models.Review.booking_id == booking_id).first()
    if existing_review:
        raise HTTPException(status_code=400, detail="You've already reviewed this booking")

    new_review = models.Review(
        booking_id=booking_id,
        user_id=user_id,
        review_score=review_score,
        review_description=review_description,
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return RedirectResponse(
        url=f"/bookings/{booking_id}?message=Review+submitted+successfully",
        status_code=status.HTTP_303_SEE_OTHER,
    )