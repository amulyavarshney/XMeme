import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..auth import get_current_user
from ..config import get_settings
from .. import models, schemas

router = APIRouter(tags=["Upload"])
settings = get_settings()

ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}


@router.post("/upload", response_model=schemas.UploadOut)
async def upload_image(
    file: UploadFile = File(...),
    user: models.User = Depends(get_current_user),
):
    content_type = file.content_type or ""
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, GIF, or WebP images are allowed")

    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=400, detail="File too large (max 8MB)")

    ext = ALLOWED_TYPES[content_type]
    filename = f"{uuid.uuid4().hex}{ext}"
    dest: Path = settings.upload_path / filename
    dest.write_bytes(data)

    return schemas.UploadOut(
        url=f"{settings.api_public_url}/uploads/{filename}",
        filename=filename,
    )
