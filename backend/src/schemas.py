from typing import List, Optional
# from datetime import datetime
from pydantic import BaseModel

#comman attributes
class MemeBase(BaseModel):
    name: str
    url: str
    caption: str

# additional attributes while posting a meme
class MemeCreate(MemeBase):
    pass

# additional attributes in the database
class Meme(MemeBase):
    id: str
    # created: datetime = datetime.now()

    class Config:
        orm_mode = True

# to return after posting a meme
class MemeId(BaseModel):
    id: str

    class Config:
        orm_mode = True

# to update either the url or caption or both
class MemeUpdate(BaseModel):
    url: Optional[str]
    caption: Optional[str]

    class Config:
        orm_mode = True