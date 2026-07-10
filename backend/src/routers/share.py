from html import escape

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from .. import crud
from ..config import get_settings
from ..database import get_db

router = APIRouter(tags=["Share"])
settings = get_settings()


@router.get("/share/{meme_id}", response_class=HTMLResponse)
def share_page(meme_id: int, request: Request, db: Session = Depends(get_db)):
    meme = crud.get_meme(db, meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail="Meme not found")

    title = f"{meme.caption} · XMeme"
    description = f"Posted by {meme.name} on XMeme"
    image = meme.url
    if image.startswith("/"):
        image = f"{settings.api_public_url}{image}"
    page_url = f"{settings.frontend_url}/#/meme/{meme.id}"
    share_url = str(request.url)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description)}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{escape(title)}">
  <meta property="og:description" content="{escape(description)}">
  <meta property="og:image" content="{escape(image)}">
  <meta property="og:url" content="{escape(share_url)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{escape(title)}">
  <meta name="twitter:description" content="{escape(description)}">
  <meta name="twitter:image" content="{escape(image)}">
  <meta http-equiv="refresh" content="0;url={escape(page_url)}">
  <link rel="canonical" href="{escape(page_url)}">
</head>
<body>
  <p>Redirecting to <a href="{escape(page_url)}">meme</a>…</p>
</body>
</html>"""
