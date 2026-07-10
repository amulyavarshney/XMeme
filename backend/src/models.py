from sqlalchemy import Column, Integer, String

from .database import Base


class Meme(Base):
    __tablename__ = "memes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    url = Column(String, index=True)
    caption = Column(String, index=True)
