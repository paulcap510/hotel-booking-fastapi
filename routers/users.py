from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import UserCreate, UserPrivateResponse, UserPublicResponse, UserUpdate, Token
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from auth import create_access_token, hash_password, oauth2_scheme, verify_access_token, verify_password
from config import settings


router = APIRouter(
    prefix="/api/users",
    tags=["Users"]
)

@router.post("", response_model=UserPrivateResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):

    existing_user = (db.query(models.User).filter(func.lower(models.User.username) == user.username.lower()).first())
    if existing_user: raise HTTPException( status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    existing_email = (db.query(models.User).filter(func.lower(models.User.email) == user.email.lower()).first())
    if existing_email: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    new_user = models.User(
        username=user.username,
        email=user.email.lower(),
        hashed_password=hash_password(user.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),     # form_data = Depends(OAuth2PasswordRequestForm)
                                                        # OAuth2PasswordRequestForm ==>> "FastAPI, read the submitted login form and give me an object with .username and .password.""
    db: Session = Depends(get_db),
):

    #! NOTE: OAuth2PasswordRequestForm uses "username" field, but we treat it as email
    user = db.query(models.User).filter(
        func.lower(models.User.email) == form_data.username.lower()
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")



# “Given the token you sent me, tell me which user is currently logged in.”
# After the user is already logged in; concerns info about the currently logged in user
def get_current_user(
    token: str = Depends(oauth2_scheme), # uses the extractor `oauth2_scheme` to see the extracted token? # set a variable to token and run oauth2 function to extract the token from the incoming header
    db: Session = Depends(get_db),
):
    user_id = verify_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(models.User).filter(models.User.id == user_id_int).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

@router.get("/me", response_model=UserPrivateResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user

#! Public User response for when users do things like comment or leave reviews, doesn't contain sensitive info (email, etc.)
@router.get("/{user_id}", response_model=UserPublicResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user:
        return user

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )




# @router.patch("/{user_id}", response_model=UserPrivateResponse)
# def update_user(
#     user_id: int,
#     user_update: UserUpdate,
#     db: Session = Depends(get_db),
# ):
#     user = db.query(models.User).filter(models.User.id == user_id).first()

#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found",
#         )

#     if (
#         user_update.username is not None
#         and user_update.username.lower() != user.username.lower()
#     ):
#         existing_user = db.query(models.User).filter(
#             func.lower(models.User.username) == user_update.username.lower()
#         ).first()

#         if existing_user:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Username already exists",
#             )

#     if (
#         user_update.email is not None
#         and user_update.email.lower() != user.email.lower()
#     ):
#         existing_email = db.query(models.User).filter(
#             func.lower(models.User.email) == user_update.email.lower()
#         ).first()

#         if existing_email:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Email already registered",
#             )

#     if user_update.username is not None:
#         user.username = user_update.username

#     if user_update.email is not None:
#         user.email = user_update.email.lower()

#     db.commit()
#     db.refresh(user)

#     return user



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