from sqlalchemy.orm import Session

from . import models, schemas


def get_meme(db: Session, meme_id: int):
    return db.query(models.Meme).filter(models.Meme.id == meme_id).first()


def get_same_meme(db: Session, name: str, url: str, caption: str):
    return (
        db.query(models.Meme)
        .filter(
            models.Meme.name == name,
            models.Meme.url == url,
            models.Meme.caption == caption,
        )
        .first()
    )


def get_memes(db: Session):
    return db.query(models.Meme).all()


def create_meme(db: Session, meme: schemas.MemeCreate):
    db_meme = models.Meme(**meme.dict())
    db.add(db_meme)
    db.commit()
    db.refresh(db_meme)
    return db_meme


def update_meme(db: Session, db_meme: models.Meme, update: schemas.MemeUpdate):
    for field, value in update.dict(exclude_unset=True).items():
        if value is not None and value != "":
            setattr(db_meme, field, value)
    db.add(db_meme)
    db.commit()
    db.refresh(db_meme)
    return db_meme
