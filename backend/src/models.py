from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    bio = Column(String(280), default="")
    is_private = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    onboarding_done = Column(Boolean, default=False, nullable=False)

    memes = relationship("Meme", back_populates="owner")
    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    reactions = relationship("Reaction", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship(
        "Notification",
        back_populates="user",
        foreign_keys="Notification.user_id",
        cascade="all, delete-orphan",
    )


class Meme(Base):
    __tablename__ = "memes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    url = Column(String, nullable=False)
    caption = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    view_count = Column(Integer, default=0, nullable=False)
    share_count = Column(Integer, default=0, nullable=False)
    download_count = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default="published", nullable=False)  # draft|published|unlisted
    visibility = Column(String(20), default="public", nullable=False)  # public|unlisted
    editor_state = Column(Text, default="")  # JSON
    media_type = Column(String(20), default="image", nullable=False)  # image|gif|video
    tags_raw = Column(String(255), default="")

    owner = relationship("User", back_populates="memes")
    likes = relationship("Like", back_populates="meme", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="meme", cascade="all, delete-orphan")
    reactions = relationship("Reaction", back_populates="meme", cascade="all, delete-orphan")
    tags = relationship("MemeTag", back_populates="meme", cascade="all, delete-orphan")


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("user_id", "meme_id", name="uq_user_meme_like"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    meme_id = Column(Integer, ForeignKey("memes.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="likes")
    meme = relationship("Meme", back_populates="likes")


class Reaction(Base):
    __tablename__ = "reactions"
    __table_args__ = (
        UniqueConstraint("user_id", "meme_id", "emoji", name="uq_user_meme_reaction"),
    )

    id = Column(Integer, primary_key=True)
    emoji = Column(String(16), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    meme_id = Column(Integer, ForeignKey("memes.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="reactions")
    meme = relationship("Meme", back_populates="reactions")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    body = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    meme_id = Column(Integer, ForeignKey("memes.id"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="comments")
    meme = relationship("Meme", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], backref="replies")


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    image_url = Column(String, nullable=False)
    description = Column(String(255), default="")
    category = Column(String(50), default="blank", index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    is_public = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class TemplateFavorite(Base):
    __tablename__ = "template_favorites"
    __table_args__ = (UniqueConstraint("user_id", "template_id", name="uq_template_fav"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, index=True, nullable=False)


class MemeTag(Base):
    __tablename__ = "meme_tags"
    __table_args__ = (UniqueConstraint("meme_id", "tag_id", name="uq_meme_tag"),)

    id = Column(Integer, primary_key=True)
    meme_id = Column(Integer, ForeignKey("memes.id"), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=False, index=True)

    meme = relationship("Meme", back_populates="tags")
    tag = relationship("Tag")


class Collection(Base):
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    slug = Column(String(80), unique=True, index=True, nullable=False)
    description = Column(String(255), default="")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class CollectionMeme(Base):
    __tablename__ = "collection_memes"
    __table_args__ = (UniqueConstraint("collection_id", "meme_id", name="uq_collection_meme"),)

    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=False, index=True)
    meme_id = Column(Integer, ForeignKey("memes.id"), nullable=False, index=True)


class Follow(Base):
    __tablename__ = "follows"
    __table_args__ = (UniqueConstraint("follower_id", "following_id", name="uq_follow"),)

    id = Column(Integer, primary_key=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    following_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    type = Column(String(40), nullable=False)
    message = Column(String(255), nullable=False)
    meme_id = Column(Integer, ForeignKey("memes.id"), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", foreign_keys=[user_id], back_populates="notifications")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    meme_id = Column(Integer, ForeignKey("memes.id"), nullable=True)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    reason = Column(String(255), nullable=False)
    status = Column(String(20), default="open", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class TemplateRecent(Base):
    __tablename__ = "template_recents"
    __table_args__ = (UniqueConstraint("user_id", "template_id", name="uq_template_recent"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False, index=True)
    used_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
