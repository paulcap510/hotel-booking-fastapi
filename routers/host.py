from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from auth import get_user_id_from_session
from fastapi.templating import Jinja2Templates
import models



router = APIRouter(
    prefix="/host",
    tags=['Host']
)

templates = Jinja2Templates(directory="templates")


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

