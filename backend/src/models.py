from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
# from sqlalchemy.types import Date

from .database import Base


class Meme(Base):
    __tablename__ = "memes"

    id = Column(Integer, primary_key=True, index=True)
    # date = Column(Date, default=datetime.now().strftime("%Y-%m-%d" "%H:%M:%S"))
    name = Column(String, index=True)
    url = Column(String, index=True)
    caption = Column(String, index=True)
