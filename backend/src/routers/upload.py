import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from .. import models, schemas
from ..auth import get_current_user
from ..config import get_settings
from ..rate_limit import limiter

router = APIRouter(tags=["Upload"])
settings = get_settings()

ALLOWED_TYPES = {
    "image/jpeg": (".jpg", "image"),
    "image/png": (".png", "image"),
    "image/gif": (".gif", "gif"),
    "image/webp": (".webp", "image"),
    "video/mp4": (".mp4", "video"),
    "video/webm": (".webm", "video"),
}


def sniff_media(data: bytes, claimed: str) -> str:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if len(data) > 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    if len(data) > 12 and data[4:8] == b"ftyp":
        return "video/mp4"
    if data.startswith(b"\x1aE\xdf\xa3"):
        return "video/webm"
    raise HTTPException(status_code=400, detail="File content does not match an allowed media type")


@router.post("/upload", response_model=schemas.UploadOut)
@limiter.limit(settings.upload_rate_limit)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    user: models.User = Depends(get_current_user),
):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    content_type = sniff_media(data, file.content_type or "")
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Allowed: JPEG, PNG, GIF, WebP, MP4, WebM")

    max_bytes = (
        settings.max_upload_bytes * 3
        if content_type.startswith("video/")
        else settings.max_upload_bytes
    )
    if len(data) > max_bytes:
        raise HTTPException(status_code=400, detail="File too large")

    ext, media_type = ALLOWED_TYPES[content_type]
    filename = f"{uuid.uuid4().hex}{ext}"
    dest: Path = settings.upload_path / filename
    dest.write_bytes(data)

    return schemas.UploadOut(
        url=f"{settings.api_public_url}/uploads/{filename}",
        filename=filename,
        media_type=media_type,
    )
