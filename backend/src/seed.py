"""Seed default meme templates, caching remote images locally when possible."""

from pathlib import Path
from urllib.request import Request, urlopen

from . import models
from .config import get_settings
from .database import SessionLocal

settings = get_settings()

DEFAULT_TEMPLATES = [
    {
        "name": "Blank Canvas",
        "slug": "blank",
        "category": "blank",
        "remote": None,
        "description": "Start from a clean slate",
    },
    {
        "name": "Drake",
        "slug": "drake",
        "category": "reaction",
        "remote": "https://i.imgflip.com/30b1gx.jpg",
        "description": "Classic reject / approve format",
    },
    {
        "name": "Distracted Boyfriend",
        "slug": "distracted",
        "category": "reaction",
        "remote": "https://i.imgflip.com/1ur9b0.jpg",
        "description": "Looking at something new",
    },
    {
        "name": "Two Buttons",
        "slug": "buttons",
        "category": "workplace",
        "remote": "https://i.imgflip.com/1g8my4.jpg",
        "description": "Hard choices",
    },
    {
        "name": "Change My Mind",
        "slug": "change-my-mind",
        "category": "politics",
        "remote": "https://i.imgflip.com/24y43o.jpg",
        "description": "Hot take table",
    },
    {
        "name": "Expanding Brain",
        "slug": "brain",
        "category": "reaction",
        "remote": "https://i.imgflip.com/1jwhww.jpg",
        "description": "Ascending enlightenment",
    },
]


def _ensure_blank(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800">'
            '<rect width="100%" height="100%" fill="#1a1f2b"/>'
            '<text x="50%" y="50%" fill="#6b7280" font-family="sans-serif" font-size="32" '
            'text-anchor="middle" dominant-baseline="middle">Blank Canvas</text></svg>'
        )


def _cache_remote(slug: str, remote: str) -> str:
    dest = settings.upload_path / "templates" / f"{slug}.jpg"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        try:
            req = Request(remote, headers={"User-Agent": "XMeme/2.0"})
            with urlopen(req, timeout=15) as resp:
                dest.write_bytes(resp.read())
        except Exception:
            return remote
    return f"{settings.api_public_url}/uploads/templates/{slug}.jpg"


def seed_templates():
    blank = settings.upload_path / "templates" / "blank.svg"
    _ensure_blank(blank)

    db = SessionLocal()
    try:
        existing = {t.name: t for t in db.query(models.Template).all()}
        for item in DEFAULT_TEMPLATES:
            if item["slug"] == "blank":
                image_url = f"{settings.api_public_url}/uploads/templates/blank.svg"
            else:
                image_url = _cache_remote(item["slug"], item["remote"])

            if item["name"] in existing:
                row = existing[item["name"]]
                row.image_url = image_url
                row.description = item["description"]
                row.category = item.get("category", "blank")
                db.add(row)
            else:
                db.add(
                    models.Template(
                        name=item["name"],
                        image_url=image_url,
                        description=item["description"],
                        category=item.get("category", "blank"),
                        is_public=True,
                    )
                )
        db.commit()
    finally:
        db.close()
