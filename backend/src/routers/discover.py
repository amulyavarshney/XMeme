from typing import Optional
from urllib.parse import quote
from urllib.request import Request, urlopen
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..auth import get_current_user, get_current_user_optional
from ..config import get_settings
from ..database import get_db
from ..models import utcnow

router = APIRouter(tags=["Discover"])
settings = get_settings()

DEFAULT_COLLECTIONS = [
    ("Wholesome", "wholesome", "Feel-good memes"),
    ("Work", "work", "Office and hustle humor"),
    ("Reaction", "reaction", "Perfect reply energy"),
]


def ensure_collections(db: Session):
    for name, slug, desc in DEFAULT_COLLECTIONS:
        if not db.query(models.Collection).filter(models.Collection.slug == slug).first():
            db.add(models.Collection(name=name, slug=slug, description=desc))
    db.commit()


@router.get("/templates", response_model=list[schemas.TemplateOut])
def templates(
    category: Optional[str] = None,
    q: Optional[str] = None,
    favorites: bool = False,
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(get_current_user_optional),
):
    return crud.list_templates(db, user, category=category, q=q, favorites_only=favorites)


@router.post("/templates", response_model=schemas.TemplateOut, status_code=201)
def create_template(
    payload: schemas.TemplateCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    row = models.Template(
        name=payload.name,
        image_url=payload.image_url,
        description=payload.description,
        category=payload.category or "custom",
        user_id=user.id,
        is_public=payload.is_public,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return schemas.TemplateOut(
        id=row.id,
        name=row.name,
        image_url=row.image_url,
        description=row.description or "",
        category=row.category,
        user_id=row.user_id,
        is_public=row.is_public,
        favorited=False,
    )


@router.get("/templates/recent", response_model=list[schemas.TemplateOut])
def recent_templates(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    rows = (
        db.query(models.TemplateRecent)
        .filter(models.TemplateRecent.user_id == user.id)
        .order_by(models.TemplateRecent.used_at.desc())
        .limit(12)
        .all()
    )
    fav_ids = {
        f.template_id
        for f in db.query(models.TemplateFavorite).filter(models.TemplateFavorite.user_id == user.id)
    }
    out = []
    for r in rows:
        t = db.query(models.Template).filter(models.Template.id == r.template_id).first()
        if not t:
            continue
        out.append(
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
        )
    return out


@router.post("/templates/{template_id}/favorite")
def favorite_template(
    template_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    tmpl = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    existing = (
        db.query(models.TemplateFavorite)
        .filter(models.TemplateFavorite.user_id == user.id, models.TemplateFavorite.template_id == template_id)
        .first()
    )
    if existing:
        db.delete(existing)
        favorited = False
    else:
        db.add(models.TemplateFavorite(user_id=user.id, template_id=template_id))
        favorited = True
    db.commit()
    return {"favorited": favorited}


@router.post("/templates/{template_id}/use")
def use_template(
    template_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    tmpl = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    recent = (
        db.query(models.TemplateRecent)
        .filter(models.TemplateRecent.user_id == user.id, models.TemplateRecent.template_id == template_id)
        .first()
    )
    if recent:
        recent.used_at = utcnow()
    else:
        db.add(models.TemplateRecent(user_id=user.id, template_id=template_id))
    db.commit()
    return {"ok": True}

@router.get("/stock/search", response_model=list[schemas.StockImage])
def stock_search(q: str = Query(..., min_length=1), limit: int = Query(12, ge=1, le=24)):
    """Search Giphy when GIPHY_API_KEY is set; otherwise return curated placeholders."""
    key = settings.giphy_api_key
    if key:
        try:
            url = f"https://api.giphy.com/v1/gifs/search?api_key={quote(key)}&q={quote(q)}&limit={limit}&rating=pg-13"
            req = Request(url, headers={"User-Agent": "XMeme/2.0"})
            with urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode())
            return [
                schemas.StockImage(
                    id=item["id"],
                    title=item.get("title") or q,
                    url=item["images"]["original"]["url"],
                    preview_url=item["images"]["fixed_height_small"]["url"],
                    source="giphy",
                )
                for item in data.get("data", [])
            ]
        except Exception:
            pass

    # Fallback curated set filtered by query
    catalog = [
        ("drake", "Drake", "https://i.imgflip.com/30b1gx.jpg"),
        ("distracted", "Distracted Boyfriend", "https://i.imgflip.com/1ur9b0.jpg"),
        ("buttons", "Two Buttons", "https://i.imgflip.com/1g8my4.jpg"),
        ("brain", "Expanding Brain", "https://i.imgflip.com/1jwhww.jpg"),
        ("cat", "Cat", "https://i.imgflip.com/1bij.jpg"),
        ("doge", "Doge", "https://i.imgflip.com/4t0m5.jpg"),
    ]
    ql = q.lower()
    matched = [c for c in catalog if ql in c[0] or ql in c[1].lower()] or catalog
    return [
        schemas.StockImage(id=c[0], title=c[1], url=c[2], preview_url=c[2], source="curated")
        for c in matched[:limit]
    ]


@router.get("/collections", response_model=list[schemas.CollectionOut])
def collections(db: Session = Depends(get_db)):
    ensure_collections(db)
    rows = db.query(models.Collection).order_by(models.Collection.name.asc()).all()
    out = []
    for c in rows:
        count = db.query(models.CollectionMeme).filter(models.CollectionMeme.collection_id == c.id).count()
        out.append(
            schemas.CollectionOut(
                id=c.id,
                name=c.name,
                slug=c.slug,
                description=c.description or "",
                meme_count=count,
            )
        )
    return out


@router.get("/collections/{slug}/memes", response_model=schemas.PaginatedMemes)
def collection_memes(
    slug: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(None),
    db: Session = Depends(get_db),
    user: Optional[models.User] = Depends(get_current_user_optional),
):
    ensure_collections(db)
    col = db.query(models.Collection).filter(models.Collection.slug == slug).first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")
    size = page_size or settings.default_page_size
    # For demo: filter by tag matching slug if present, else latest public
    return crud.list_memes(db, page=page, page_size=size, current_user=user, tag=slug)


@router.get("/notifications", response_model=list[schemas.NotificationOut])
def notifications(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    rows = (
        db.query(models.Notification)
        .filter(models.Notification.user_id == user.id)
        .order_by(models.Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return rows


@router.post("/notifications/read")
def read_notifications(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    db.query(models.Notification).filter(
        models.Notification.user_id == user.id, models.Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"ok": True}


@router.post("/reports", status_code=201)
def report(
    payload: schemas.ReportCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if not payload.meme_id and not payload.comment_id:
        raise HTTPException(status_code=400, detail="meme_id or comment_id required")
    db.add(
        models.Report(
            reporter_id=user.id,
            meme_id=payload.meme_id,
            comment_id=payload.comment_id,
            reason=payload.reason,
        )
    )
    db.commit()
    return {"ok": True}


def _require_admin(user: models.User) -> None:
    admins = get_settings().admin_username_set
    if not admins or user.username.lower() not in admins:
        raise HTTPException(status_code=403, detail="Admin access required")


@router.get("/admin/reports")
def list_reports(
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    _require_admin(user)
    query = db.query(models.Report).order_by(models.Report.created_at.desc())
    if status_filter:
        query = query.filter(models.Report.status == status_filter)
    total = query.count()
    rows = query.offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": r.id,
                "reporter_id": r.reporter_id,
                "meme_id": r.meme_id,
                "comment_id": r.comment_id,
                "reason": r.reason,
                "status": r.status,
                "created_at": r.created_at,
            }
            for r in rows
        ],
    }


@router.patch("/admin/reports/{report_id}")
def update_report(
    report_id: int,
    status: str = Query(..., pattern="^(open|reviewed|resolved|dismissed)$"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    _require_admin(user)
    report_row = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report_row:
        raise HTTPException(status_code=404, detail="Report not found")
    report_row.status = status
    db.commit()
    return {"ok": True, "id": report_id, "status": status}
