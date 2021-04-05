from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Set, List

from sqlalchemy.orm import Session

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from pydantic import BaseModel

from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

from . import crud, models, schemas

from .btchApiDB import SessionLocal, engine

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password":
        "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    },
    "janedoe": {
        "username": "janedoe",
        "full_name": "Jane Doe",
        "email": "janedoe@example.com",
        "hashed_password":
        "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}

fake_games_db = {
    "lkml4a3.d3": {
        "handle": "lkml4a3.d3",
        "white": "johndoe",
        "black": "janedoe",
        "status": "started",
        "create_time": datetime(2021, 1, 1, tzinfo=timezone.utc),
    },
    "da39a3ee5e": {
        "handle": "da39a3ee5e",
        "white": "johndoe",
        "black": "janedoe",
        "status": "running",
        "create_time": datetime(2021, 3, 12, tzinfo=timezone.utc),
    },
    "d3255bfef9": {
        "handle": "d3255bfef9",
        "white": "johndoe",
        "black": None,
        "status": "open",
        "create_time": datetime(2021, 4, 5, tzinfo=timezone.utc),
    }
}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()
# allow for CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def set_fake_db(fake_db):
    global fake_users_db
    fake_users_db = fake_db.copy()


def get_fake_db():
    return fake_users_db

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# TODO I don't like this, seems error prone. SQLAlchemy will probably make it better
def setGame(gameUUID, dbgame):
    global fake_games_db
    fake_games_db[gameUUID] = dbgame


def try_set_player(gameUUID, user):
    dbgame = fake_games_db[gameUUID]
    if dbgame['white'] and dbgame['black']:
        game_exception = HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Game has no free player slots",
        )
        raise game_exception

    if not dbgame['white']:
        dbgame['white'] = user['username']
    elif not dbgame['black']:
        dbgame['black'] = user['username']

    # TODO race condition
    setGame(gameUUID, dbgame)
    return get_game(gameUUID)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = crud.get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: schemas.User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_active_game(
    gameUUID,
    current_user: schemas.User = Depends(get_current_active_user)
):
    game = get_game(gameUUID)

async def set_player(
    gameUUID, current_user: schemas.User = Depends(get_current_active_user)):
    try_set_player(gameUUID, current_user)


@app.get("/version")
async def version():
    return {'version': "1.0"}

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = crud.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(get_current_active_user)):
    return current_user


@app.get("/users/me/games/")
async def read_own_games(
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
    ):
    return [
        Game(**game)
        for gameName, game in db.items()
        if game['white'] == current_user.username
        or game['black'] == current_user.username
    ]

@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.post("/users/")
async def create_user(new_user: schemas.UserCreate, db: Session = Depends(get_db)):
    user = crud.get_user(db, new_user.username)
    user_exists_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="username taken",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if user:
        raise user_exists_exception
    else:
        db_user = crud.create_user(db, new_user)
        print(db_user)
        return crud.get_user_by_username(db, new_user.username)


@app.get("/games/")
async def get_new_game(current_user: schemas.User = Depends(get_current_active_user)):
    handle = crud.create_game()
    return {"game_handle": handle}


@app.get("/games/{gameUUID}")
async def get_game_by_handle(
    gameUUID: str,
    current_user: schemas.User = Depends(get_current_active_user)
    ):
    game = get_active_game(gameUUID, current_user)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="game not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return game

# joines an existing game. error when game already started
@app.get("/games/{gameUUID}/join")
def join_game(gameUUID: str, current_user: schemas.User = Depends(get_current_active_user)):
    game = get_active_game(gameUUID, current_user)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="game not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    set_player(game, current_user)
    return game

# either creates a new game or joins an existing unstarted random game. Random games can not be joined via "join_game".
@app.get("/games/random")
def join_random_game(current_user: schemas.User = Depends(get_current_active_user)):
    pass

# serialized board state
@app.get("/games/{gameUUID}/board")
def query_board(gameUUID: str, current_user: schemas.User = Depends(get_current_active_user)):
    pass

# who's turn is it (None means that the game is over)
@app.get("/games/{gameUUID}/turn")
def query_turn(gameUUID: str, current_user: schemas.User = Depends(get_current_active_user)):
    pass

@app.post("/games/{gameUUID}/move")
async def post_move(gameUUID: str,
                    current_user: User = Depends(get_current_active_user),
                    current_game: Game = Depends(get_active_game)):
    game = get_active_game(gameUUID, current_user)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="game not found",
            headers={"Authorization": "Bearer"},
        )
    return game
