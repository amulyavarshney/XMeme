from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserUpdate(BaseModel):
    bio: Optional[str] = Field(default=None, max_length=280)
    is_private: Optional[bool] = None
    onboarding_done: Optional[bool] = None


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    bio: str = ""
    is_private: bool = False
    created_at: datetime
    meme_count: int = 0
    like_count: int = 0
    follower_count: int = 0
    following_count: int = 0
    followed_by_me: bool = False


class UserMe(UserPublic):
    email: EmailStr
    onboarding_done: bool = False


class MemeCreate(BaseModel):
    caption: str = Field(min_length=1, max_length=280)
    url: str = Field(min_length=1)
    name: Optional[str] = Field(default=None, max_length=100)
    status: str = Field(default="published", pattern=r"^(draft|published|unlisted)$")
    visibility: str = Field(default="public", pattern=r"^(public|unlisted)$")
    editor_state: Optional[str] = None
    media_type: str = Field(default="image", pattern=r"^(image|gif|video)$")
    tags: list[str] = Field(default_factory=list)


class MemeUpdate(BaseModel):
    caption: Optional[str] = Field(default=None, max_length=280)
    url: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern=r"^(draft|published|unlisted)$")
    visibility: Optional[str] = Field(default=None, pattern=r"^(public|unlisted)$")
    editor_state: Optional[str] = None
    media_type: Optional[str] = Field(default=None, pattern=r"^(image|gif|video)$")
    tags: Optional[list[str]] = None


class ReactionCount(BaseModel):
    emoji: str
    count: int


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
    share_count: int = 0
    download_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    liked_by_me: bool = False
    status: str = "published"
    visibility: str = "public"
    editor_state: str = ""
    media_type: str = "image"
    tags: list[str] = Field(default_factory=list)
    reactions: list[ReactionCount] = Field(default_factory=list)
    my_reactions: list[str] = Field(default_factory=list)


class PaginatedMemes(BaseModel):
    items: list[MemeOut]
    total: int
    page: int
    page_size: int
    pages: int


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=500)
    parent_id: Optional[int] = None


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    body: str
    meme_id: int
    user_id: int
    username: str
    parent_id: Optional[int] = None
    created_at: datetime
    replies: list["CommentOut"] = Field(default_factory=list)


CommentOut.model_rebuild()


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    image_url: str
    description: str = ""
    category: str = "custom"
    is_public: bool = True


class TemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    image_url: str
    description: str = ""
    category: str = "blank"
    user_id: Optional[int] = None
    is_public: bool = True
    favorited: bool = False


class UploadOut(BaseModel):
    url: str
    filename: str
    media_type: str = "image"


class CollectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str = ""
    meme_count: int = 0


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    message: str
    meme_id: Optional[int] = None
    is_read: bool
    created_at: datetime


class ReportCreate(BaseModel):
    reason: str = Field(min_length=3, max_length=255)
    meme_id: Optional[int] = None
    comment_id: Optional[int] = None


class StockImage(BaseModel):
    id: str
    title: str
    url: str
    preview_url: str
    source: str


class AnalyticsOut(BaseModel):
    views: int
    shares: int
    downloads: int
    likes: int
    comments: int
    ctr: float
