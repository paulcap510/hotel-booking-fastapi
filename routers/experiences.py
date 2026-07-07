from fastapi import APIRouter, Request, Depends, status, Form, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from fastapi.responses import RedirectResponse, HTMLResponse
from auth import get_user_id_from_session
import models
import shutil
from schemas import ExperienceResponse
from pathlib import Path



router = APIRouter(
    prefix="/experiences",
    tags=['Experiences']
)

templates = Jinja2Templates(directory="templates")

@router.get("", response_model=list[ExperienceResponse])
def get_experiences(db: Session = Depends(get_db)):
    experiences = db.query(models.Experience).all()
    return experiences


@router.post("/create_experience", include_in_schema=False)
def create_experience_post(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    price_per_person: int = Form(...),
    location: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+list+an+experience",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user.is_host:
        return RedirectResponse(
            url="/host/become",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    upload_dir = Path("static/uploads/experiences")
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / image.filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    image_path = f"uploads/experiences/{image.filename}"

    new_experience = models.Experience(
        title=title,
        description=description,
        price_per_person=price_per_person,
        location=location,
        image_path=image_path,
        user_id=user_id,
    )

    db.add(new_experience)
    db.commit()
    db.refresh(new_experience)

    return RedirectResponse(
        url="/host/dashboard?message=Experience+added+successfully",
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.get("/create_experience", response_class=HTMLResponse, include_in_schema=False)
def create_experience_page(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+list+an+experience",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user.is_host:
        return RedirectResponse(
            url="/host/become",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(request, "create_experience.html", {
        "request": request,
        "user": user,
    })



@router.post("/{experience_id}/deactivate", include_in_schema=False)
def deactivate_experience(request: Request, experience_id: int, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+manage+your+experience",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+manage+your+experience",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if not user.is_host:
        return RedirectResponse(
            url="/host/become",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    experience = db.query(models.Experience).filter(models.Experience.id == experience_id).first()

    if experience is None:
        raise HTTPException(status_code=404, detail="Experience not found")

    if experience.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this experience")

    experience.is_active = False
    db.commit()

    return RedirectResponse(
        url="/host/dashboard?message=Experience+deactivated+successfully",
        status_code=status.HTTP_303_SEE_OTHER,
    )



@router.post("/{experience_id}/reactivate", include_in_schema=False)
def reactivate_experience(request: Request, experience_id: int, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+manage+your+experience",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+manage+your+experience",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if not user.is_host:
        return RedirectResponse(
            url="/host/become",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    experience = db.query(models.Experience).filter(models.Experience.id == experience_id).first()

    if experience is None:
        raise HTTPException(status_code=404, detail="Experience not found")

    if experience.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this experience")

    experience.is_active = True
    db.commit()

    return RedirectResponse(
        url="/host/dashboard?message=Experience+reactivated+successfully",
        status_code=status.HTTP_303_SEE_OTHER,
    )



@router.get("/{experience_id}/manage", response_class=HTMLResponse, include_in_schema=False)
def manage_experience_page(request: Request, experience_id: int, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+manage+your+experience",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if not user.is_host:
        return RedirectResponse(
            url="/host/become",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    experience = db.query(models.Experience).filter(models.Experience.id == experience_id).first()

    if experience is None:
        raise HTTPException(status_code=404, detail="Experience not found")

    if experience.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this experience")

    return templates.TemplateResponse(request, "manage_experience.html", {
        "experience": experience,
    })


@router.get("/{experience_id}/edit", response_class=HTMLResponse, include_in_schema=False)
def edit_experience_page(request: Request,  experience_id: int, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
            return RedirectResponse(
                url="/login?message=Please+log+in+to+manage+your+experience",
                status_code=status.HTTP_303_SEE_OTHER,
            )

    experience = db.query(models.Experience).filter(models.Experience.id == experience_id).first()

    if experience is None:
        raise HTTPException(status_code=404, detail="Experience not found")

    if experience.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this experience")

    return templates.TemplateResponse(request, "edit_experience.html", {
        "request": request,
        "experience": experience,
    })


@router.post("/{experience_id}/edit", include_in_schema=False)
def edit_experience_post(
    request: Request,
    experience_id: int,
    title: str = Form(...),
    description: str = Form(...),
    price_per_person: int = Form(...),
    location: str = Form(...),
    db: Session = Depends(get_db),
):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+manage+your+experience",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    experience = db.query(models.Experience).filter(models.Experience.id == experience_id).first()

    if experience is None:
        raise HTTPException(status_code=404, detail="Experience not found")

    if experience.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this experience")

    experience.title = title
    experience.description = description
    experience.price_per_person = price_per_person
    experience.location = location

    db.commit()

    return RedirectResponse(
        url="/host/dashboard?message=Experience+updated+successfully",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/{experience_id}", response_model=ExperienceResponse)
def get_experience(experience_id: int, db: Session = Depends(get_db)):
    experience = db.query(models.Experience).filter(models.Experience.id == experience_id).first()

    if experience is None:
        raise HTTPException(status_code=404, detail="Experience not found")

    return experience
