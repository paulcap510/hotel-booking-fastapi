from fastapi import APIRouter, Request, Depends, status, Form, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from fastapi.responses import RedirectResponse, HTMLResponse
from auth import get_user_id_from_session
import models
import shutil
from pathlib import Path
from datetime import date


router = APIRouter(
    prefix="/experiences",
    tags=['Experiences']
)

templates = Jinja2Templates(directory="templates")


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



@router.get("/{experience_id}/bookings", response_class=HTMLResponse, include_in_schema=False)
def manage_experience_bookings_page(request: Request, experience_id: int, db: Session = Depends(get_db)):
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

    requests = (
        db.query(models.ExperienceRequest)
        .filter(models.ExperienceRequest.experience_id == experience_id)
        .order_by(models.ExperienceRequest.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(request, "manage_experience_bookings.html", {
        "experience": experience,
        "requests": requests,
    })


@router.get("/{experience_id}/edit", response_class=HTMLResponse, include_in_schema=False)
def edit_experience_page(request: Request, experience_id: int, db: Session = Depends(get_db)):
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


@router.get("/{experience_id}/request", include_in_schema=False)
def experience_booking_request_page(request: Request, experience_id: int, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+book+an+experience",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    experience = (
        db.query(models.Experience)
        .filter(models.Experience.id == experience_id)
        .filter(models.Experience.is_active == True)
        .first()
    )

    if experience is None:
        raise HTTPException(status_code=404, detail="Experience not found")

    return templates.TemplateResponse(request, "book_experience.html", {
        "experience": experience,
    })



@router.get("/my-requests", response_class=HTMLResponse, include_in_schema=False)
def my_experience_requests_page(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+view+your+requests",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    requests = (
        db.query(models.ExperienceRequest)
        .filter(models.ExperienceRequest.user_id == user_id)
        .order_by(models.ExperienceRequest.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(request, "my_experience_requests.html", {
        "requests": requests,
    })

@router.get("/{experience_id}", response_class=HTMLResponse, include_in_schema=False)
def experience_detail(request: Request, experience_id: int, db: Session = Depends(get_db)):
    experience = db.query(models.Experience).filter(models.Experience.id == experience_id).first()

    if experience is None:
        raise HTTPException(status_code=404, detail="Experience not found")

    return templates.TemplateResponse(request, "experience_detail.html", {
        "experience": experience,
    })



@router.post("/{experience_id}/request", include_in_schema=False)
def experience_booking_request_post(
    request: Request,
    experience_id: int,
    requested_date: date = Form(...),
    num_guests: int = Form(...),
    message: str = Form(None),
    db: Session = Depends(get_db),
):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+book+an+experience",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    experience = (
        db.query(models.Experience)
        .filter(models.Experience.id == experience_id)
        .filter(models.Experience.is_active == True)
        .first()
    )

    if experience is None:
        raise HTTPException(status_code=404, detail="Experience not found")

    total_price = experience.price_per_person * num_guests

    new_request = models.ExperienceRequest(
        experience_id=experience_id,
        user_id=user_id,
        requested_date=requested_date,
        num_guests=num_guests,
        total_price=total_price,
        message=message,
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return RedirectResponse(
        url=f"/experiences/{experience_id}?message=Request+submitted.+The+host+will+confirm+within+24+hours.",
        status_code=status.HTTP_303_SEE_OTHER,
    )



@router.post("/requests/{experience_request_id}/confirm", include_in_schema=False)
def confirm_experience_request(request: Request, experience_request_id: int, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+manage+your+experience",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    experience_request = (
        db.query(models.ExperienceRequest)
        .filter(models.ExperienceRequest.id == experience_request_id)
        .first()
    )

    if experience_request is None:
        raise HTTPException(status_code=404, detail="Request not found")

    experience = experience_request.experience

    if experience.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this experience")

    experience_request.status = "confirmed"
    db.commit()

    return RedirectResponse(
        url=f"/experiences/{experience.id}/bookings?message=Request+confirmed",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/requests/{experience_request_id}/decline", include_in_schema=False)
def decline_experience_request(request: Request, experience_request_id: int, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+manage+your+experience",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    experience_request = (
        db.query(models.ExperienceRequest)
        .filter(models.ExperienceRequest.id == experience_request_id)
        .first()
    )

    if experience_request is None:
        raise HTTPException(status_code=404, detail="Request not found")

    experience = experience_request.experience

    if experience.user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't own this experience")

    experience_request.status = "declined"
    db.commit()

    return RedirectResponse(
        url=f"/experiences/{experience.id}/bookings?message=Request+declined",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/my-requests", response_class=HTMLResponse, include_in_schema=False)
def my_experience_requests_page(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        return RedirectResponse(
            url="/login?message=Please+log+in+to+view+your+requests",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    requests = (
        db.query(models.ExperienceRequest)
        .filter(models.ExperienceRequest.user_id == user_id)
        .order_by(models.ExperienceRequest.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(request, "my_experience_requests.html", {
        "requests": requests,
    })