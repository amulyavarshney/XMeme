from typing import Optional

from pydantic import BaseModel


class MemeBase(BaseModel):
    name: str
    url: str
    caption: str


class MemeCreate(MemeBase):
    pass


class Meme(MemeBase):
    id: int

    class Config:
        orm_mode = True


class MemeId(BaseModel):
    id: int

    class Config:
        orm_mode = True


class MemeUpdate(BaseModel):
    url: Optional[str] = None
    caption: Optional[str] = None

    class Config:
        orm_mode = True
