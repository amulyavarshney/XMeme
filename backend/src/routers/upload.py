import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from .. import models, schemas
from ..auth import get_current_user
from ..config import get_settings

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

MAGIC = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"RIFF": "image/webp",  # need WEBP check
    b"\x00\x00\x00": "video/mp4",  # ftyp often at 4
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
        return "video/mp4" if claimed.startswith("video/") else "video/mp4"
    if data.startswith(b"\x1aE\xdf\xa3"):
        return "video/webm"
    raise HTTPException(status_code=400, detail="File content does not match an allowed media type")


@router.post("/upload", response_model=schemas.UploadOut)
async def upload_image(
    file: UploadFile = File(...),
    user: models.User = Depends(get_current_user),
):
    claimed = file.content_type or ""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    sniffed = sniff_media(data, claimed)
    if sniffed not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Allowed: JPEG, PNG, GIF, WebP, MP4, WebM")
    # Allow claimed mismatch only when sniffed is trustworthy
    content_type = sniffed

    max_bytes = settings.max_upload_bytes * 3 if content_type.startswith("video/") else settings.max_upload_bytes
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
