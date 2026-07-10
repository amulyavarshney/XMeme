from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="XMeme",
    description="API for posting, browsing, and updating memes.",
    version="1.0.0",
    docs_url="/",
    redoc_url="/doc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/memes", tags=["Memes"], response_model=schemas.MemeId)
def create_meme(meme: schemas.MemeCreate, db: Session = Depends(get_db)):
    if crud.get_same_meme(db, name=meme.name, url=meme.url, caption=meme.caption):
        raise HTTPException(status_code=409, detail="Meme already exists")
    return crud.create_meme(db=db, meme=meme)


@app.get("/memes", tags=["Memes"], response_model=List[schemas.Meme])
def read_memes(db: Session = Depends(get_db)):
    return crud.get_memes(db)


@app.get("/memes/{meme_id}", tags=["Memes"], response_model=schemas.Meme)
def read_meme(meme_id: int, db: Session = Depends(get_db)):
    db_meme = crud.get_meme(db, meme_id=meme_id)
    if db_meme is None:
        raise HTTPException(status_code=404, detail="Meme not found")
    return db_meme


@app.patch("/memes/{meme_id}", tags=["Memes"], response_model=schemas.Meme)
def update_meme(meme_id: int, update: schemas.MemeUpdate, db: Session = Depends(get_db)):
    db_meme = crud.get_meme(db, meme_id=meme_id)
    if db_meme is None:
        raise HTTPException(status_code=404, detail="Meme not found")
    return crud.update_meme(db=db, db_meme=db_meme, update=update)
