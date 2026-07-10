from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..auth import get_current_user, get_current_user_optional
from ..config import get_settings
from ..database import get_db

router = APIRouter(tags=["Users"])
settings = get_settings()


@router.get("/users/{username}", response_model=schemas.UserPublic)
def get_profile(
    username: str,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
):
    profile = crud.get_user_profile(db, username, current_user)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile


@router.get("/users/{username}/memes", response_model=schemas.PaginatedMemes)
def user_memes(
    username: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(None),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
):
    profile = crud.get_user_profile(db, username, current_user)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    size = page_size or settings.default_page_size
    size = min(max(1, size), settings.max_page_size)
    return crud.list_memes(
        db,
        page=page,
        page_size=size,
        current_user=current_user,
        user_id=profile.id,
        status=status,
    )


@router.post("/users/{username}/follow")
def follow_user(
    username: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    try:
        return crud.toggle_follow(db, user, username)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
