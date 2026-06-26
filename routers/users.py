from fastapi import APIRouter, status, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import UserCreate, UserPrivateResponse, UserPublicResponse, UserUpdate
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from auth import (
    hash_password,
    verify_password,
    create_session,
    get_user_id_from_session,
    delete_session,
)

router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)


@router.post("", response_model=UserPrivateResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):

    existing_user = (
        db.query(models.User)
        .filter(func.lower(models.User.username) == user.username.lower())
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    existing_email = (
        db.query(models.User)
        .filter(func.lower(models.User.email) == user.email.lower())
        .first()
    )
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = models.User(
        username=user.username,
        email=user.email.lower(),
        hashed_password=hash_password(user.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login")
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # OAuth2PasswordRequestForm uses "username" field, but we treat it as email
    user = (
        db.query(models.User)
        .filter(func.lower(models.User.email) == form_data.username.lower())
        .first()
    )

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    session_id = create_session(user.id)

    # Set secure=True once you're running on https
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 1 week
    )

    return {"message": "Logged in successfully"}


@router.post("/logout")
def logout(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    delete_session(session_id)
    response.delete_cookie("session_id")
    return {"message": "Logged out successfully"}


# "Given the session cookie you sent me, tell me which user is currently logged in."
def get_current_user(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_id = get_user_id_from_session(session_id)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


@router.get("/me", response_model=UserPrivateResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


# Public User response for when users do things like comment or leave reviews,
# doesn't contain sensitive info (email, etc.)
@router.get("/{user_id}", response_model=UserPublicResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user:
        return user

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.delete(user)
    db.commit()
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.delete(user)
    db.commit()