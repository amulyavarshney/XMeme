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


@router.post("/upload", response_model=schemas.UploadOut)
async def upload_image(
    file: UploadFile = File(...),
    user: models.User = Depends(get_current_user),
):
    content_type = file.content_type or ""
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Allowed: JPEG, PNG, GIF, WebP, MP4, WebM",
        )

    data = await file.read()
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
