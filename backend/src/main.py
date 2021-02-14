from typing import List, Optional
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import SessionLocal, engine
# from starlette.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware


models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="XMeme", docs_url="/", redoc_url="/doc")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/memes", tags=["Post Meme"], response_model=schemas.MemeId)
def create_meme(meme: schemas.MemeCreate, db: Session = Depends(get_db)):
    db_meme = crud.get_same_meme(db, name=meme.name, url=meme.url, caption=meme.caption)
    if db_meme:
        raise HTTPException(status_code=409, detail="Id already exists")
    return crud.create_meme(db=db, meme=meme)


# @app.get("/", tags=["Swagger UI"])
# def main():
#     return RedirectResponse(url="/docs/")


@app.get("/memes", tags=["Read Memes"], response_model=List[schemas.Meme])
# def read_memes(skip: Optional[int] = 0, limit: Optional[int] = 100, db: Session = Depends(get_db)):
#     memes = crud.get_memes(db, skip=skip, limit=limit)
def read_memes(db: Session = Depends(get_db)):
    memes = crud.get_memes(db)
    if memes:
        return memes
    else:
        return {"message": "No Memes found!"}


@app.get("/memes/{meme_id}", tags=["Read Meme"], response_model=schemas.Meme)
def read_meme(meme_id: int, db: Session = Depends(get_db)):
    db_meme = crud.get_meme(db, meme_id=meme_id)
    if db_meme is None:
        raise HTTPException(status_code=404, detail="Id doesn’t exist")
    return db_meme


@app.patch("/memes/{meme_id}", tags=["Update Meme"])
def update_meme(meme_id: int, update: schemas.MemeUpdate, db: Session = Depends(get_db)):
    # getting the existing data
    db_meme = db.query(models.Meme).filter(models.Meme.id == meme_id).one_or_none()
    if db_meme is None:
        raise HTTPException(status_code=404, detail="Id doesn’t exist")
    return crud.update_meme(db=db, db_meme=db_meme, update=update)