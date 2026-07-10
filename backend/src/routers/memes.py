from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..auth import get_current_user, get_current_user_optional
from ..config import get_settings
from ..database import get_db

router = APIRouter(tags=["Memes"])
settings = get_settings()


def _page_params(page: int, page_size: int) -> tuple[int, int]:
    page = max(1, page)
    page_size = min(max(1, page_size), settings.max_page_size)
    return page, page_size


@router.post("/memes", response_model=schemas.MemeOut, status_code=201)
def create_meme(
    payload: schemas.MemeCreate,
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(get_current_user_optional),
):
    name = payload.name or (user.username if user else "Anonymous")
    if crud.get_same_meme(db, name=name, url=payload.url, caption=payload.caption):
        raise HTTPException(status_code=409, detail="Meme already exists")
    meme = crud.create_meme(db, payload, user)
    return crud.serialize_meme(meme, user)


@router.get("/memes", response_model=schemas.PaginatedMemes)
def list_memes(
    page: int = Query(1, ge=1),
    page_size: int = Query(None),
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(get_current_user_optional),
):
    size = page_size or settings.default_page_size
    page, size = _page_params(page, size)
    return crud.list_memes(db, page=page, page_size=size, current_user=user)


@router.get("/memes/trending", response_model=schemas.PaginatedMemes)
def trending(
    page: int = Query(1, ge=1),
    page_size: int = Query(None),
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(get_current_user_optional),
):
    size = page_size or settings.default_page_size
    page, size = _page_params(page, size)
    return crud.trending_memes(db, page=page, page_size=size, current_user=user)


@router.get("/memes/{meme_id}", response_model=schemas.MemeOut)
def get_meme(
    meme_id: int,
    track_view: bool = Query(False),
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(get_current_user_optional),
):
    meme = crud.get_meme(db, meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail="Meme not found")
    if track_view:
        meme = crud.increment_views(db, meme)
    return crud.serialize_meme(meme, user)


@router.patch("/memes/{meme_id}", response_model=schemas.MemeOut)
def update_meme(
    meme_id: int,
    payload: schemas.MemeUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    meme = crud.get_meme(db, meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail="Meme not found")
    if meme.user_id and meme.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed to edit this meme")
    updated = crud.update_meme(db, meme, payload)
    return crud.serialize_meme(updated, user)


@router.delete("/memes/{meme_id}", status_code=204)
def delete_meme(
    meme_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    meme = crud.get_meme(db, meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail="Meme not found")
    if meme.user_id and meme.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this meme")
    crud.delete_meme(db, meme)
    return None


@router.post("/memes/{meme_id}/like")
def like_meme(
    meme_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    meme = crud.get_meme(db, meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail="Meme not found")
    liked, count = crud.toggle_like(db, meme, user)
    return {"liked": liked, "like_count": count}


@router.get("/memes/{meme_id}/comments", response_model=list[schemas.CommentOut])
def get_comments(meme_id: int, db: Session = Depends(get_db)):
    if not crud.get_meme(db, meme_id):
        raise HTTPException(status_code=404, detail="Meme not found")
    return crud.list_comments(db, meme_id)


@router.post("/memes/{meme_id}/comments", response_model=schemas.CommentOut, status_code=201)
def post_comment(
    meme_id: int,
    payload: schemas.CommentCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    meme = crud.get_meme(db, meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail="Meme not found")
    comment = crud.add_comment(db, meme, user, payload.body.strip())
    return schemas.CommentOut(
        id=comment.id,
        body=comment.body,
        meme_id=comment.meme_id,
        user_id=comment.user_id,
        username=user.username,
        created_at=comment.created_at,
    )
