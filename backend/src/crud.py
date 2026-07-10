import json
import re
from collections import Counter
from math import ceil
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from . import models, schemas
from .models import utcnow

TAG_RE = re.compile(r"[a-z0-9_]{2,40}")


def normalize_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []
    out = []
    for t in tags:
        name = t.strip().lower().lstrip("#")
        if TAG_RE.fullmatch(name) and name not in out:
            out.append(name)
    return out[:12]


def ensure_tags(db: Session, names: list[str]) -> list[models.Tag]:
    tags = []
    for name in names:
        tag = db.query(models.Tag).filter(models.Tag.name == name).first()
        if not tag:
            tag = models.Tag(name=name)
            db.add(tag)
            db.flush()
        tags.append(tag)
    return tags


def set_meme_tags(db: Session, meme: models.Meme, names: list[str]):
    names = normalize_tags(names)
    meme.tags_raw = ",".join(names)
    db.query(models.MemeTag).filter(models.MemeTag.meme_id == meme.id).delete()
    for tag in ensure_tags(db, names):
        db.add(models.MemeTag(meme_id=meme.id, tag_id=tag.id))


def notify(db: Session, user_id: int, actor_id: int | None, type_: str, message: str, meme_id: int | None = None):
    if user_id and actor_id and user_id == actor_id:
        return
    db.add(
        models.Notification(
            user_id=user_id,
            actor_id=actor_id,
            type=type_,
            message=message,
            meme_id=meme_id,
        )
    )


def serialize_meme(meme: models.Meme, current_user: Optional[models.User] = None) -> schemas.MemeOut:
    like_count = len(meme.likes) if meme.likes is not None else 0
    comment_count = len(meme.comments) if meme.comments is not None else 0
    liked_by_me = False
    if current_user is not None and meme.likes:
        liked_by_me = any(like.user_id == current_user.id for like in meme.likes)

    reaction_counter = Counter((r.emoji for r in (meme.reactions or [])))
    my_reactions = []
    if current_user and meme.reactions:
        my_reactions = [r.emoji for r in meme.reactions if r.user_id == current_user.id]

    tags = []
    if meme.tags:
        tags = [mt.tag.name for mt in meme.tags if mt.tag]
    elif meme.tags_raw:
        tags = [t for t in meme.tags_raw.split(",") if t]

    return schemas.MemeOut(
        id=meme.id,
        name=meme.name,
        url=meme.url,
        caption=meme.caption,
        user_id=meme.user_id,
        username=meme.owner.username if meme.owner else None,
        created_at=meme.created_at,
        updated_at=meme.updated_at,
        view_count=meme.view_count or 0,
        share_count=meme.share_count or 0,
        download_count=meme.download_count or 0,
        like_count=like_count,
        comment_count=comment_count,
        liked_by_me=liked_by_me,
        status=meme.status or "published",
        visibility=meme.visibility or "public",
        editor_state=meme.editor_state or "",
        media_type=meme.media_type or "image",
        tags=tags,
        reactions=[schemas.ReactionCount(emoji=e, count=c) for e, c in reaction_counter.items()],
        my_reactions=my_reactions,
    )


def _meme_query(db: Session):
    return db.query(models.Meme).options(
        joinedload(models.Meme.owner),
        joinedload(models.Meme.likes),
        joinedload(models.Meme.comments),
        joinedload(models.Meme.reactions),
        joinedload(models.Meme.tags).joinedload(models.MemeTag.tag),
    )


def get_meme(db: Session, meme_id: int) -> Optional[models.Meme]:
    return _meme_query(db).filter(models.Meme.id == meme_id).first()


def get_same_meme(db: Session, name: str, url: str, caption: str):
    return (
        db.query(models.Meme)
        .filter(models.Meme.name == name, models.Meme.url == url, models.Meme.caption == caption)
        .first()
    )


def visible_filter(query, current_user: Optional[models.User], include_drafts_for_owner=True):
    if current_user:
        return query.filter(
            or_(
                models.Meme.status == "published",
                models.Meme.status == "unlisted",
                (models.Meme.status == "draft") & (models.Meme.user_id == current_user.id),
            )
        )
    return query.filter(models.Meme.status.in_(["published", "unlisted"]))


def list_memes(
    db: Session,
    page: int,
    page_size: int,
    current_user: Optional[models.User] = None,
    user_id: Optional[int] = None,
    tag: Optional[str] = None,
    q: Optional[str] = None,
    status: Optional[str] = None,
    following_only: bool = False,
) -> schemas.PaginatedMemes:
    count_q = db.query(func.count(models.Meme.id))
    query = _meme_query(db)

    if following_only and current_user:
        following_ids = [
            f.following_id
            for f in db.query(models.Follow).filter(models.Follow.follower_id == current_user.id).all()
        ]
        query = query.filter(models.Meme.user_id.in_(following_ids or [-1]))
        count_q = count_q.filter(models.Meme.user_id.in_(following_ids or [-1]))

    if user_id is not None:
        query = query.filter(models.Meme.user_id == user_id)
        count_q = count_q.filter(models.Meme.user_id == user_id)
        if not current_user or current_user.id != user_id:
            query = query.filter(models.Meme.status == "published", models.Meme.visibility == "public")
            count_q = count_q.filter(models.Meme.status == "published", models.Meme.visibility == "public")
        elif status:
            query = query.filter(models.Meme.status == status)
            count_q = count_q.filter(models.Meme.status == status)
    else:
        query = visible_filter(query, current_user)
        count_q = visible_filter(count_q, current_user)
        query = query.filter(models.Meme.visibility == "public", models.Meme.status == "published")
        count_q = count_q.filter(models.Meme.visibility == "public", models.Meme.status == "published")

    if tag:
        tag_name = tag.lower().lstrip("#")
        query = query.join(models.MemeTag).join(models.Tag).filter(models.Tag.name == tag_name)
        count_q = count_q.join(models.MemeTag).join(models.Tag).filter(models.Tag.name == tag_name)

    if q:
        like = f"%{q}%"
        query = query.filter(or_(models.Meme.caption.ilike(like), models.Meme.name.ilike(like), models.Meme.tags_raw.ilike(like)))
        count_q = count_q.filter(or_(models.Meme.caption.ilike(like), models.Meme.name.ilike(like), models.Meme.tags_raw.ilike(like)))

    total = count_q.scalar() or 0
    pages = max(1, ceil(total / page_size)) if total else 0
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
    window: str = "all",
) -> schemas.PaginatedMemes:
    like_count = func.count(models.Like.id).label("like_count")
    query = (
        db.query(models.Meme, like_count)
        .outerjoin(models.Like, models.Like.meme_id == models.Meme.id)
        .filter(models.Meme.status == "published", models.Meme.visibility == "public")
        .group_by(models.Meme.id)
    )
    if window == "today":
        query = query.filter(models.Meme.created_at >= func.datetime("now", "-1 day"))
    elif window == "week":
        query = query.filter(models.Meme.created_at >= func.datetime("now", "-7 day"))

    query = query.order_by(like_count.desc(), models.Meme.view_count.desc(), models.Meme.id.desc())
    total = query.count()
    # query.count() with group_by can be weird; fallback:
    total = db.query(func.count(models.Meme.id)).filter(
        models.Meme.status == "published", models.Meme.visibility == "public"
    ).scalar() or 0
    pages = max(1, ceil(total / page_size)) if total else 0
    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    meme_ids = [row[0].id for row in rows]
    loaded = {m.id: m for m in _meme_query(db).filter(models.Meme.id.in_(meme_ids)).all()} if meme_ids else {}
    memes = [loaded[mid] for mid in meme_ids if mid in loaded]
    return schemas.PaginatedMemes(
        items=[serialize_meme(m, current_user) for m in memes],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


def random_meme(db: Session, current_user: Optional[models.User] = None) -> Optional[models.Meme]:
    return (
        _meme_query(db)
        .filter(models.Meme.status == "published", models.Meme.visibility == "public")
        .order_by(func.random())
        .first()
    )


def create_meme(db: Session, data: schemas.MemeCreate, user: Optional[models.User] = None) -> models.Meme:
    name = data.name or (user.username if user else "Anonymous")
    meme = models.Meme(
        name=name,
        url=data.url,
        caption=data.caption,
        user_id=user.id if user else None,
        created_at=utcnow(),
        updated_at=utcnow(),
        status=data.status,
        visibility=data.visibility if data.status != "draft" else "unlisted",
        editor_state=data.editor_state or "",
        media_type=data.media_type,
    )
    db.add(meme)
    db.commit()
    db.refresh(meme)
    if data.tags:
        set_meme_tags(db, meme, data.tags)
        db.commit()
    return get_meme(db, meme.id)


def update_meme(db: Session, meme: models.Meme, data: schemas.MemeUpdate) -> models.Meme:
    payload = data.model_dump(exclude_unset=True)
    tags = payload.pop("tags", None)
    for field, value in payload.items():
        if value is not None and value != "":
            setattr(meme, field, value)
    if tags is not None:
        set_meme_tags(db, meme, tags)
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


def increment_share(db: Session, meme: models.Meme) -> models.Meme:
    meme.share_count = (meme.share_count or 0) + 1
    db.add(meme)
    db.commit()
    return get_meme(db, meme.id)


def increment_download(db: Session, meme: models.Meme) -> models.Meme:
    meme.download_count = (meme.download_count or 0) + 1
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
        if meme.user_id:
            notify(db, meme.user_id, user.id, "like", f"@{user.username} liked your meme", meme.id)
    db.commit()
    count = db.query(func.count(models.Like.id)).filter(models.Like.meme_id == meme.id).scalar()
    return liked, count or 0


def toggle_reaction(db: Session, meme: models.Meme, user: models.User, emoji: str) -> dict:
    existing = (
        db.query(models.Reaction)
        .filter(
            models.Reaction.meme_id == meme.id,
            models.Reaction.user_id == user.id,
            models.Reaction.emoji == emoji,
        )
        .first()
    )
    if existing:
        db.delete(existing)
        active = False
    else:
        db.add(models.Reaction(user_id=user.id, meme_id=meme.id, emoji=emoji))
        active = True
        if meme.user_id:
            notify(db, meme.user_id, user.id, "reaction", f"@{user.username} reacted {emoji}", meme.id)
    db.commit()
    meme = get_meme(db, meme.id)
    out = serialize_meme(meme, user)
    return {"active": active, "reactions": [r.model_dump() for r in out.reactions], "my_reactions": out.my_reactions}


def add_comment(db: Session, meme: models.Meme, user: models.User, body: str, parent_id: int | None = None):
    if parent_id:
        parent = db.query(models.Comment).filter(models.Comment.id == parent_id, models.Comment.meme_id == meme.id).first()
        if not parent:
            raise ValueError("Parent comment not found")
    comment = models.Comment(body=body, user_id=user.id, meme_id=meme.id, parent_id=parent_id)
    db.add(comment)
    if meme.user_id:
        notify(db, meme.user_id, user.id, "comment", f"@{user.username} commented on your meme", meme.id)
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
    by_id = {}
    roots = []
    for c in comments:
        node = schemas.CommentOut(
            id=c.id,
            body=c.body,
            meme_id=c.meme_id,
            user_id=c.user_id,
            username=c.user.username,
            parent_id=c.parent_id,
            created_at=c.created_at,
            replies=[],
        )
        by_id[c.id] = node
    for c in comments:
        node = by_id[c.id]
        if c.parent_id and c.parent_id in by_id:
            by_id[c.parent_id].replies.append(node)
        else:
            roots.append(node)
    return roots


def get_user_profile(db: Session, username: str, current_user: Optional[models.User] = None) -> Optional[schemas.UserPublic]:
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return None
    meme_count = (
        db.query(func.count(models.Meme.id))
        .filter(models.Meme.user_id == user.id, models.Meme.status == "published")
        .scalar()
        or 0
    )
    like_count = (
        db.query(func.count(models.Like.id))
        .join(models.Meme, models.Meme.id == models.Like.meme_id)
        .filter(models.Meme.user_id == user.id)
        .scalar()
        or 0
    )
    follower_count = db.query(func.count(models.Follow.id)).filter(models.Follow.following_id == user.id).scalar() or 0
    following_count = db.query(func.count(models.Follow.id)).filter(models.Follow.follower_id == user.id).scalar() or 0
    followed_by_me = False
    if current_user:
        followed_by_me = (
            db.query(models.Follow)
            .filter(models.Follow.follower_id == current_user.id, models.Follow.following_id == user.id)
            .first()
            is not None
        )
    return schemas.UserPublic(
        id=user.id,
        username=user.username,
        bio=user.bio or "",
        is_private=bool(user.is_private),
        created_at=user.created_at,
        meme_count=meme_count,
        like_count=like_count,
        follower_count=follower_count,
        following_count=following_count,
        followed_by_me=followed_by_me,
    )


def toggle_follow(db: Session, follower: models.User, username: str) -> dict:
    target = db.query(models.User).filter(models.User.username == username).first()
    if not target:
        raise ValueError("User not found")
    if target.id == follower.id:
        raise ValueError("Cannot follow yourself")
    existing = (
        db.query(models.Follow)
        .filter(models.Follow.follower_id == follower.id, models.Follow.following_id == target.id)
        .first()
    )
    if existing:
        db.delete(existing)
        following = False
    else:
        db.add(models.Follow(follower_id=follower.id, following_id=target.id))
        following = True
        notify(db, target.id, follower.id, "follow", f"@{follower.username} followed you")
    db.commit()
    profile = get_user_profile(db, username, follower)
    return {"following": following, "profile": profile}


def list_templates(
    db: Session,
    current_user: Optional[models.User] = None,
    category: Optional[str] = None,
    q: Optional[str] = None,
    favorites_only: bool = False,
) -> list[schemas.TemplateOut]:
    query = db.query(models.Template)
    if current_user:
        query = query.filter(or_(models.Template.is_public == True, models.Template.user_id == current_user.id))
    else:
        query = query.filter(models.Template.is_public == True)
    if category and category != "all":
        query = query.filter(models.Template.category == category)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(models.Template.name.ilike(like), models.Template.description.ilike(like)))
    fav_ids = set()
    if current_user:
        fav_ids = {
            f.template_id
            for f in db.query(models.TemplateFavorite).filter(models.TemplateFavorite.user_id == current_user.id)
        }
        if favorites_only:
            query = query.filter(models.Template.id.in_(fav_ids or [-1]))
    rows = query.order_by(models.Template.name.asc()).all()
    return [
        schemas.TemplateOut(
            id=t.id,
            name=t.name,
            image_url=t.image_url,
            description=t.description or "",
            category=t.category or "blank",
            user_id=t.user_id,
            is_public=bool(t.is_public),
            favorited=t.id in fav_ids,
        )
        for t in rows
    ]


def meme_analytics(db: Session, meme: models.Meme) -> schemas.AnalyticsOut:
    likes = len(meme.likes or [])
    comments = len(meme.comments or [])
    views = meme.view_count or 0
    shares = meme.share_count or 0
    downloads = meme.download_count or 0
    ctr = round(((shares + downloads) / views) * 100, 2) if views else 0.0
    return schemas.AnalyticsOut(
        views=views,
        shares=shares,
        downloads=downloads,
        likes=likes,
        comments=comments,
        ctr=ctr,
    )
