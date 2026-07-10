from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    bio: Optional[str] = Field(default=None, max_length=280)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    bio: str = ""
    created_at: datetime
    meme_count: int = 0
    like_count: int = 0


class UserMe(UserPublic):
    email: EmailStr


class MemeCreate(BaseModel):
    caption: str = Field(min_length=1, max_length=280)
    url: str = Field(min_length=1)
    name: Optional[str] = Field(default=None, max_length=100)


class MemeUpdate(BaseModel):
    caption: Optional[str] = Field(default=None, max_length=280)
    url: Optional[str] = None


class MemeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    caption: str
    user_id: Optional[int] = None
    username: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    liked_by_me: bool = False


class MemeId(BaseModel):
    id: int


class PaginatedMemes(BaseModel):
    items: list[MemeOut]
    total: int
    page: int
    page_size: int
    pages: int


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=500)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    body: str
    meme_id: int
    user_id: int
    username: str
    created_at: datetime


class TemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    image_url: str
    description: str = ""


class UploadOut(BaseModel):
    url: str
    filename: str
