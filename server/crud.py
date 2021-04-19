import random
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from typing import Optional, Tuple, Set
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

from . import models, schemas

from .utils import get_password_hash, verify_password, get_random_string

from .config import (
    SECRET_KEY, ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES, HANDLEBASEURL,
)

# TODO redo this. I hate myself for writing it.
def create_game_uuid(db: Session):
    uuid = get_random_string()
    print(uuid)
    # Check if it exists (and its idle?) Or we could add the id or something.
    for i in range(5):
        repeatedHandleGame = db.query(models.Game).filter(models.Game.uuid == uuid).first()
        if repeatedHandleGame is None:
            break

    if repeatedHandleGame is not None:
        return None
    return uuid

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

def create_game(db: Session, user: schemas.User, gameOptions: schemas.GameCreate):
    user = get_user_by_username(db, user.username)
    if not user:
        return False

    uuid = create_game_uuid(db)

    # TODO list status strings somewhere
    db_game = models.Game(
        owner_id=user.id,
        created_at=datetime.now(timezone.utc),
        uuid=uuid,
        status="idle",
        turn="white",
        public=gameOptions.public
    )
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game

def get_game(gameUUID):
    game_exception = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Could not find game",
    )
    if gameUUID not in fake_games_db:
        raise game_exception
    return Game(**fake_games_db[gameUUID])

def get_games_by_owner(db: Session, user: schemas.User):
    return db.query(models.Game).filter(models.Game.owner == user).all()

def get_game_by_uuid(db: Session, gameUUID):
    return db.query(models.Game).filter(models.Game.uuid == gameUUID).first()

def get_game_idle_random(db: Session, user: schemas.User):
    query = db.query(models.Game).filter(
        and_(
            models.Game.status.is_("idle"),
            models.Game.white_id.is_not(user.id),
            models.Game.black_id.is_not(user.id)
        )
    )
    numAvailableGames = query.count()
    if numAvailableGames == 0:
        return {}
    rand = random.randrange(0, numAvailableGames)
    game = query[rand]
    return game

def get_snap(db: Session, user: schemas.User, gameUUID, move_number):
    game = get_game_by_uuid(db, gameUUID)
    query = db.query(models.GameSnap).filter(
        and_(
            models.GameSnap.game_id == game.id,
            models.GameSnap.move_number == move_number
        )
    )

    if query.count() > 1:
        print("Error: snap duplicate!")

    snap = query.first()

    return snap

    # color = game.get_player_color(user.id)
    # snap.prepare_for_player(color)
