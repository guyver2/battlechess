import random
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from typing import Optional, Tuple, Set
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

from . import models, schemas

from .utils import (get_password_hash, verify_password, get_random_string,
                    defaultBoard)

from .config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    HANDLEBASEURL,
)


# TODO redo this. I hate myself for writing it.
def create_game_uuid(db: Session):
    uuid = get_random_string()
    # Check if it exists (and its idle?) Or we could add the id or something.
    for i in range(5):
        repeatedHandleGame = db.query(
            models.Game).filter(models.Game.uuid == uuid).first()
        if repeatedHandleGame is None:
            break

    if repeatedHandleGame is not None:
        return None
    return uuid


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_id(db: Session, userid: int):
    return db.query(
        models.User).filter(models.User.id == userid).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_username(db: Session, username: str):
    return db.query(
        models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.plain_password)
    db_user = models.User(username=user.username,
                          full_name=user.full_name,
                          email=user.email,
                          hashed_password=hashed_password)
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


def create_game(db: Session, user: schemas.User,
                gameOptions: schemas.GameCreate):
    user = get_user_by_username(db, user.username)
    if not user:
        return False

    uuid = create_game_uuid(db)
    owner_color = random.choice(["white", "black"])
    if gameOptions.color in ["white", "black"]:
        owner_color = gameOptions.color
    black_id = None
    white_id = None
    if owner_color == "white":
        white_id = user.id
    else:
        black_id = user.id

    # TODO list status strings somewhere
    db_game = models.Game(owner_id=user.id,
                          created_at=datetime.now(timezone.utc),
                          uuid=uuid,
                          status="waiting",
                          turn="white",
                          white_id=white_id,
                          black_id=black_id,
                          public=gameOptions.public)
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game


def get_games_by_owner(db: Session, user: schemas.User):
    return db.query(models.Game).filter(models.Game.owner == user).all()


def get_games_by_player(db: Session, user: schemas.User):
    return db.query(models.Game).filter(
        or_(models.Game.black == user, models.Game.white == user)).all()


def get_game_by_uuid(db: Session, gameUUID):
    return db.query(models.Game).filter(models.Game.uuid == gameUUID).first()


def get_public_game_by_status(db: Session, user: schemas.User, status):
    games = db.query(models.Game).filter(
        and_(models.Game.status == status,
             models.Game.white_id.is_not(user.id),
             models.Game.black_id.is_not(user.id),
             models.Game.public == True)).all()
    print(games)
    return games


def get_random_public_game_waiting(db: Session, user: schemas.User):
    public_games = get_public_game_by_status(db, user, "waiting")
    numAvailableGames = len(public_games)
    if numAvailableGames == 0:
        return {}
    rand = random.randrange(0, numAvailableGames)
    game = public_games[rand]
    return game


def get_snap(db: Session, user: schemas.User, gameUUID, move_number):
    game = get_game_by_uuid(db, gameUUID)
    query = db.query(models.GameSnap).filter(
        and_(models.GameSnap.game_id == game.id,
             models.GameSnap.move_number == move_number))

    if query.count() > 1:
        print("Error: snap duplicate!")

    snap = query.first()

    return snap

    # color = game.get_player_color(user.id)
    # snap.prepare_for_player(color)


def create_snap_by_move(db: Session, user: schemas.User, game: schemas.Game,
                        gameMove: schemas.GameMove):
    game = get_game_by_uuid(db, game.uuid)

    snapOptions = game.moveGame(gameMove.move)

    snap = game.get_latest_snap()
    # TODO list status strings somewhere
    db_snap = models.GameSnap(
        created_at=datetime.now(timezone.utc),
        game_id=game.id,
        move=gameMove.move,
        board=snapOptions['board'],
        taken=snapOptions['taken'],
        castleable=snapOptions['castleable'],
        move_number=snap.move_number + 1)
    db.add(db_snap)
    db.commit()
    db.refresh(db_snap)

    # update turn
    winner = db_snap.winner()
    if winner:
        game.winner = winner
        game.status = 'finished'
        print(
            f'Game {game.uuid} {game.white_id} vs {game.black_id} won by {game.winner}'
        )

    game.refresh_turn()

    color = None
    if game.black_id == user.id:
        color = 'b'
    if game.white_id == user.id:
        color = 'w'

    # deprecated in favor of pydantic prepare_for_player TODO pydantic elements
    # elements = db_snap.filtered(color)

    db.commit()
    return db_snap


# TODO test
def create_snap_by_dict(db: Session, user: schemas.User, gameUUID: str, board: str, move: str,
                        taken: str, castleable: str):
    game = get_game_by_uuid(db, gameUUID)

    last_snap = game.get_latest_snap()
    move_number = last_snap.move_number + 1

    db_snap = models.GameSnap(
        game_id=game.id,
        created_at=datetime.now(timezone.utc),
        board=board,
        move=move,
        taken=taken,
        castleable=castleable,
        move_number=move_number)
    db.add(db_snap)
    db.commit()
    db.refresh(db_snap)
    return db_snap


def create_default_snap(db: Session, user: schemas.User, game: models.Game):
    db_snap = models.GameSnap(
        game_id=game.id,
        created_at=datetime.now(timezone.utc),
        board=defaultBoard(),
        move="",
        taken="",
        castleable=''.join(sorted("LKSlks")),
        move_number=0)
    db.add(db_snap)
    db.commit()
    db.refresh(db_snap)
    return db_snap
