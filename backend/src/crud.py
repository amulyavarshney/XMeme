from sqlalchemy.orm import Session
from typing import Optional
from . import models, schemas

# to get meme by id...
def get_meme(db: Session, meme_id: int):
    return db.query(models.Meme).filter(models.Meme.id == meme_id).first()

# to check if the same post exist in the database
def get_same_meme(db: Session, name: str, url: str, caption: str):
    return db.query(models.Meme).filter(models.Meme.name == name, models.Meme.url == url, models.Meme.caption == caption).first()

# to get all the memes...
# def get_memes(db: Session, skip: Optional[int] = 0, limit: Optional[int] = 100):
def get_memes(db: Session):
    # return db.query(models.Meme).offset(skip).limit(limit).all()
    return db.query(models.Meme).all()

# to post a meme...
def create_meme(db: Session, meme: schemas.MemeCreate):
    db_meme = models.Meme(**meme.dict())
    db.add(db_meme)
    db.commit()
    db.refresh(db_meme)
    return db_meme

# to update either url or caption or both...
def update_meme(db: Session, db_meme, update: schemas.MemeUpdate):
    # Update model class variable from requested fields 
    for var, value in vars(update).items():
        setattr(db_meme, var, value) if value else None
    db.add(db_meme)
    db.commit()
    db.refresh(db_meme)
    # return db_meme