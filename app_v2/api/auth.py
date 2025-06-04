# app/api/auth.py

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app_v2 import schemas, models
from app_v2.core.auth import (
    get_db,
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app_v2.config import settings

router = APIRouter(tags=["auth"])


@router.post("/signup", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def signup(user_create: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user_create.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = get_password_hash(user_create.password)
    new_user = models.User(
        email=user_create.email,
        name=user_create.name,
        hashed_password=hashed_pw,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    On success, returns both an access token (short expiry) and a refresh token (longer expiry).
    """
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "scope": "access_token"},
        expires_delta=access_expires
    )

    # Create a refresh token. Note the “scope”: “refresh_token” so we can validate it differently.
    refresh_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": user.email, "scope": "refresh_token"},
        expires_delta=refresh_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }


@router.post("/refresh", response_model=schemas.Token)
def refresh_access_token(*, token_request: schemas.RefreshRequest):
    """
    Called by client when the access token expires. Expects:
      {
        "refresh_token": "<the_token>"
      }
    Returns a new pair of (access_token, refresh_token).
    """
    try:
        # Decode only if it has scope=refresh_token
        username = decode_token(token_request.refresh_token, check_scope="refresh_token")
    except HTTPException:
        # decode_token already raises 401 if invalid/expired
        raise

    # You might want to check if the user still exists or is active:
    # db = next(get_db())
    # user = db.query(models.User).filter(models.User.email == username).first()
    # if not user or not user.is_active:
    #     raise HTTPException(...)

    # Create a *new* access token:
    access_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access = create_access_token(
        data={"sub": username, "scope": "access_token"},
        expires_delta=access_expires
    )

    # Optionally, issue a brand‐new refresh token (rotating refresh tokens):
    refresh_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh = create_refresh_token(
        data={"sub": username},
        expires_delta=refresh_expires
    )

    return {
        "access_token": new_access,
        "token_type": "bearer",
        "refresh_token": new_refresh
    }
