from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app_v2 import models, schemas
from app_v2.core.auth import get_current_user, get_db

router = APIRouter(tags=["user"])

@router.get("/view_profile", response_model=schemas.UserOut)
def get_user_profile(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.put("/update_profile", response_model=schemas.UserOut)
def update_my_profile(
    updates: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    for field, value in updates.dict(exclude_unset=True).items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/view_projects", response_model=List[schemas.ProjectBase])
def list_my_projects(
    current_user: models.User = Depends(get_current_user),
):
    return current_user.projects