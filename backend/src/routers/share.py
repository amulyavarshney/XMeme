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
    if not meme or meme.status == "draft":
        raise HTTPException(status_code=404, detail="Meme not found")

    title = f"{meme.caption} · XMeme"
    description = f"Posted by {meme.name} on XMeme"
    image = meme.url
    if image.startswith("/"):
        image = f"{settings.api_public_url}{image}"
    page_url = f"{settings.frontend_url}/#/meme/{meme.id}"
    share_url = str(request.url)
    embed = f'<blockquote class="xmeme-embed"><a href="{escape(page_url)}">{escape(meme.caption)}</a></blockquote><script async src="{escape(settings.frontend_url)}/embed.js"></script>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description)}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="XMeme">
  <meta property="og:title" content="{escape(title)}">
  <meta property="og:description" content="{escape(description)}">
  <meta property="og:image" content="{escape(image)}">
  <meta property="og:url" content="{escape(share_url)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{escape(title)}">
  <meta name="twitter:description" content="{escape(description)}">
  <meta name="twitter:image" content="{escape(image)}">
  <link rel="canonical" href="{escape(page_url)}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Bungee&family=Outfit:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{ --ink:#12141a; --teal:#0f9f8a; --paper:#f3f6f9; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:Outfit,system-ui,sans-serif; background:
      radial-gradient(ellipse 80% 50% at 10% -10%, rgba(15,159,138,.18), transparent 55%),
      linear-gradient(180deg,#eaf1f6,var(--paper)); color:var(--ink); min-height:100vh; }}
    .wrap {{ max-width:720px; margin:0 auto; padding:2rem 1.25rem 3rem; }}
    .brand {{ font-family:Bungee,sans-serif; font-size:1.5rem; color:var(--teal); text-decoration:none; }}
    .card {{ margin-top:1.25rem; background:#fff; border:1px solid #d5dde8; border-radius:16px; overflow:hidden; box-shadow:0 12px 40px rgba(18,20,26,.08); }}
    img, video {{ width:100%; display:block; background:#e8eef3; }}
    .body {{ padding:1.25rem 1.35rem 1.5rem; }}
    h1 {{ margin:0 0 .5rem; font-size:1.4rem; }}
    .meta {{ color:#3a4050; margin:0 0 1rem; }}
    .actions {{ display:flex; flex-wrap:wrap; gap:.6rem; }}
    a.btn, button.btn {{ appearance:none; border:none; border-radius:10px; padding:.7rem 1rem; font:inherit; font-weight:600; cursor:pointer; text-decoration:none; display:inline-flex; }}
    .primary {{ background:var(--teal); color:#fff; }}
    .ghost {{ background:transparent; border:1px solid #d5dde8; color:#3a4050; }}
    code {{ display:block; margin-top:.75rem; padding:.75rem; background:#fafcfd; border:1px solid #d5dde8; border-radius:10px; font-size:.8rem; word-break:break-all; }}
  </style>
</head>
<body>
  <div class="wrap">
    <a class="brand" href="{escape(settings.frontend_url)}">XMeme</a>
    <article class="card">
      {"<video controls src='" + escape(image) + "'></video>" if (meme.media_type == "video") else f"<img src='{escape(image)}' alt='{escape(meme.caption)}'>"}
      <div class="body">
        <h1>{escape(meme.caption)}</h1>
        <p class="meta">by {escape(meme.name)} · {meme.view_count or 0} views · {meme.share_count or 0} shares</p>
        <div class="actions">
          <a class="btn primary" href="{escape(page_url)}">Open in XMeme</a>
          <a class="btn ghost" href="https://twitter.com/intent/tweet?text={escape(meme.caption)}&url={escape(share_url)}" target="_blank" rel="noopener">Share on X</a>
          <a class="btn ghost" download href="{escape(image)}">Download</a>
        </div>
        <p class="meta" style="margin-top:1rem">Embed code</p>
        <code>{escape(embed)}</code>
      </div>
    </article>
  </div>
</body>
</html>"""
