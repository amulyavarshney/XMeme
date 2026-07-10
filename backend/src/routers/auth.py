from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..auth import (
    create_access_token,
    get_current_user,
    get_user_by_email,
    get_user_by_username,
    hash_password,
    verify_password,
)
from ..database import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])


def _me_payload(db: Session, user: models.User) -> schemas.UserMe:
    profile = crud.get_user_profile(db, user.username, user)
    return schemas.UserMe(
        **profile.model_dump(),
        email=user.email,
        onboarding_done=bool(user.onboarding_done),
    )


@router.post("/register", response_model=schemas.UserMe, status_code=201)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if get_user_by_username(db, payload.username):
        raise HTTPException(status_code=409, detail="Username already taken")
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="Email already registered")

    user = models.User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        bio="",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _me_payload(db, user)


@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return schemas.Token(access_token=create_access_token(user.username))


@router.get("/me", response_model=schemas.UserMe)
def me(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _me_payload(db, user)


@router.patch("/me", response_model=schemas.UserMe)
def update_me(
    payload: schemas.UserUpdate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(user, key, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return _me_payload(db, user)
