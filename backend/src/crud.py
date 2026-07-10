from math import ceil
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from . import models, schemas
from .models import utcnow


def serialize_meme(
    meme: models.Meme,
    current_user: Optional[models.User] = None,
) -> schemas.MemeOut:
    like_count = len(meme.likes) if meme.likes is not None else 0
    comment_count = len(meme.comments) if meme.comments is not None else 0
    liked_by_me = False
    if current_user is not None and meme.likes:
        liked_by_me = any(like.user_id == current_user.id for like in meme.likes)

    username = meme.owner.username if meme.owner else None
    return schemas.MemeOut(
        id=meme.id,
        name=meme.name,
        url=meme.url,
        caption=meme.caption,
        user_id=meme.user_id,
        username=username,
        created_at=meme.created_at,
        updated_at=meme.updated_at,
        view_count=meme.view_count or 0,
        like_count=like_count,
        comment_count=comment_count,
        liked_by_me=liked_by_me,
    )


def _meme_query(db: Session):
    return db.query(models.Meme).options(
        joinedload(models.Meme.owner),
        joinedload(models.Meme.likes),
        joinedload(models.Meme.comments),
    )


def get_meme(db: Session, meme_id: int) -> Optional[models.Meme]:
    return _meme_query(db).filter(models.Meme.id == meme_id).first()


def get_same_meme(db: Session, name: str, url: str, caption: str):
    return (
        db.query(models.Meme)
        .filter(
            models.Meme.name == name,
            models.Meme.url == url,
            models.Meme.caption == caption,
        )
        .first()
    )


def list_memes(
    db: Session,
    page: int,
    page_size: int,
    current_user: Optional[models.User] = None,
    user_id: Optional[int] = None,
) -> schemas.PaginatedMemes:
    count_q = db.query(func.count(models.Meme.id))
    if user_id is not None:
        count_q = count_q.filter(models.Meme.user_id == user_id)
    total = count_q.scalar() or 0
    pages = max(1, ceil(total / page_size)) if total else 0

    query = _meme_query(db)
    if user_id is not None:
        query = query.filter(models.Meme.user_id == user_id)
    items = (
        query.order_by(models.Meme.created_at.desc(), models.Meme.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return schemas.PaginatedMemes(
        items=[serialize_meme(m, current_user) for m in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


def trending_memes(
    db: Session,
    page: int,
    page_size: int,
    current_user: Optional[models.User] = None,
) -> schemas.PaginatedMemes:
    like_count = func.count(models.Like.id).label("like_count")
    query = (
        db.query(models.Meme, like_count)
        .outerjoin(models.Like, models.Like.meme_id == models.Meme.id)
        .group_by(models.Meme.id)
        .order_by(like_count.desc(), models.Meme.view_count.desc(), models.Meme.id.desc())
    )
    total = db.query(func.count(models.Meme.id)).scalar() or 0
    pages = max(1, ceil(total / page_size)) if total else 0
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    meme_ids = [row[0].id for row in rows]
    memes = []
    if meme_ids:
        loaded = {
            m.id: m
            for m in _meme_query(db).filter(models.Meme.id.in_(meme_ids)).all()
        }
        memes = [loaded[mid] for mid in meme_ids if mid in loaded]

    return schemas.PaginatedMemes(
        items=[serialize_meme(m, current_user) for m in memes],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


def create_meme(
    db: Session,
    data: schemas.MemeCreate,
    user: Optional[models.User] = None,
) -> models.Meme:
    name = data.name or (user.username if user else "Anonymous")
    meme = models.Meme(
        name=name,
        url=data.url,
        caption=data.caption,
        user_id=user.id if user else None,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db.add(meme)
    db.commit()
    db.refresh(meme)
    return get_meme(db, meme.id)


def update_meme(db: Session, meme: models.Meme, data: schemas.MemeUpdate) -> models.Meme:
    payload = data.model_dump(exclude_unset=True)
    for field, value in payload.items():
        if value is not None and value != "":
            setattr(meme, field, value)
    meme.updated_at = utcnow()
    db.add(meme)
    db.commit()
    return get_meme(db, meme.id)


def delete_meme(db: Session, meme: models.Meme) -> None:
    db.delete(meme)
    db.commit()


def increment_views(db: Session, meme: models.Meme) -> models.Meme:
    meme.view_count = (meme.view_count or 0) + 1
    db.add(meme)
    db.commit()
    return get_meme(db, meme.id)


def toggle_like(db: Session, meme: models.Meme, user: models.User) -> tuple[bool, int]:
    existing = (
        db.query(models.Like)
        .filter(models.Like.meme_id == meme.id, models.Like.user_id == user.id)
        .first()
    )
    liked = False
    if existing:
        db.delete(existing)
    else:
        db.add(models.Like(user_id=user.id, meme_id=meme.id))
        liked = True
    db.commit()
    count = db.query(func.count(models.Like.id)).filter(models.Like.meme_id == meme.id).scalar()
    return liked, count or 0


def add_comment(
    db: Session,
    meme: models.Meme,
    user: models.User,
    body: str,
) -> models.Comment:
    comment = models.Comment(body=body, user_id=user.id, meme_id=meme.id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def list_comments(db: Session, meme_id: int) -> list[schemas.CommentOut]:
    comments = (
        db.query(models.Comment)
        .options(joinedload(models.Comment.user))
        .filter(models.Comment.meme_id == meme_id)
        .order_by(models.Comment.created_at.asc())
        .all()
    )
    return [
        schemas.CommentOut(
            id=c.id,
            body=c.body,
            meme_id=c.meme_id,
            user_id=c.user_id,
            username=c.user.username,
            created_at=c.created_at,
        )
        for c in comments
    ]


def get_user_profile(db: Session, username: str) -> Optional[schemas.UserPublic]:
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return None
    meme_count = db.query(func.count(models.Meme.id)).filter(models.Meme.user_id == user.id).scalar() or 0
    like_count = (
        db.query(func.count(models.Like.id))
        .join(models.Meme, models.Meme.id == models.Like.meme_id)
        .filter(models.Meme.user_id == user.id)
        .scalar()
        or 0
    )
    return schemas.UserPublic(
        id=user.id,
        username=user.username,
        bio=user.bio or "",
        created_at=user.created_at,
        meme_count=meme_count,
        like_count=like_count,
    )


def list_templates(db: Session) -> list[models.Template]:
    return db.query(models.Template).order_by(models.Template.name.asc()).all()
