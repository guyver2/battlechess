from sqlalchemy.orm import Session
from typing import Optional, Tuple, Set
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

from . import models, schemas

from .utils import get_password_hash, verify_password

from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(username=user.username, full_name=user.full_name, email=user.email, hashed_password=user.hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_game():
    # TODO generate links
    return "https://bt.ch/lkml4a3.d3"

def get_game(gameUUID):
    game_exception = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Could not find game",
    )
    if gameUUID not in fake_games_db:
        raise game_exception
    return Game(**fake_games_db[gameUUID])