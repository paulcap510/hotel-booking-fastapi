from fastapi import APIRouter, Request, Depends, status, Form, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from fastapi.responses import RedirectResponse
from auth import get_user_id_from_session
import models
from models import User
from sqlalchemy import func
from schemas import ExperienceCreate



router = APIRouter(
    prefix="/experiences",
    tags=['Experiences']
)

templates = Jinja2Templates(directory="templates")

@router.post("/create_experience")
def create_experience_post(experience: ExperienceCreate, db: Session = Depends(get_db)):

    new_experience = models.Experience(
        title=experience.title,
        description=experience.description,
        price_per_person=experience.price_per_person,
        location=experience.location,
        # image_path: Mapped[str] = mapped_column(String, nullable=False)
    )

    db.add(new_experience)
    db.commit()
    db.refresh(new_experience)

    return new_experience



@router.get("/create_experience")
def create_experience_page(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+manage+your+property",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    user = db.query(User).filter(User.id == user_id).first()

    if user is None or user.is_host is not True:
        return RedirectResponse(
            url="/host/become",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        request,
        "create_experience.html",
        {"user": user},
    )