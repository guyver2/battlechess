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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

models.Base.metadata.create_all(bind=engine)

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

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
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
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: schemas.User = Depends(get_current_user)):
    if not current_user.is_active():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

async def get_active_game(
    gameUUID,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # TODO check if public and owner/player
    game = crud.get_game_by_uuid(db, gameUUID)
    return game

async def set_player(
    gameUUID,
    current_user: schemas.User = Depends(get_current_active_user)
):
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
def read_users_me(current_user: schemas.User = Depends(get_current_active_user)):
    return current_user


@app.get("/users/me/games/")
def read_own_games(
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    games = crud.get_games_by_owner(db, current_user)
    # TODO refactor this for db query result from .all()
    return [
        Game(**game)
        for gameName, game in games
        if game['white'] == current_user.username
        or game['black'] == current_user.username
    ]

@app.get("/users/",  response_model=List[schemas.User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.get("/users/usernames", response_model=List[str])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return [user.username for user in users]

@app.get("/users/active_game")
def read_users(db: Session = Depends(get_db)):
    game = get_active_game(gameUUID, current_user)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="game not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return game

@app.post("/users/")
def create_user(new_user: schemas.UserCreate, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, new_user.username)
    user_exists_exception = HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="username taken",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if user:
        raise user_exists_exception
    else:
        db_user = crud.create_user(db, new_user)
        return crud.get_user_by_username(db, new_user.username)

@app.post("/games/")
def post_new_game(
    new_game: schemas.GameCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    return crud.create_game(db, current_user, new_game)


@app.get("/games/{gameUUID}")
def get_game_by_uuid(
    gameUUID: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    return crud.get_game_by_uuid(db, gameUUID)

# lists available games
@app.get("/games/{gameUUID}/list", response_model=List[schemas.Game])
def join_game(
    gameUUID: str,
    current_user: schemas.User = Depends(get_current_active_user)
):
    games = get_available_games(current_user)
    if not games:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="game not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return games

# joines an existing game. error when game already started
@app.get("/games/{gameUUID}/join")
def join_game(
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
    set_player(game, current_user)
    return game

# either creates a new game or joins an existing unstarted random game. Random games can not be joined via "join_game".
@app.patch("/games/random")
def join_random_game(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    game = crud.get_game_idle_random(db, current_user)
    if not game:
        return {}
    game.set_player(current_user)
    return game

# serialized board state
@app.get("/games/{gameUUID}/board")
def query_board(
    gameUUID: str,
    current_user: schemas.User = Depends(get_current_active_user)
):
    pass

# who's turn is it (None means that the game is over)
@app.get("/games/{gameUUID}/turn")
def query_turn(
    gameUUID: str,
    current_user: schemas.User = Depends(get_current_active_user)
):
    pass

@app.post("/games/{gameUUID}/move")
def post_move(
    gameUUID: str,
    current_user: schemas.User = Depends(get_current_active_user),
    current_game: schemas.Game = Depends(get_active_game)
):
    game = get_active_game(gameUUID, current_user)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="game not found",
            headers={"Authorization": "Bearer"},
        )
    return game

@app.get("/games/{gameUUID}/snap/{moveNum}")
def get_snap(
    gameUUID: str,
    moveNum: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    game = get_active_game(gameUUID, current_user)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="game not found",
            headers={"Authorization": "Bearer"},
        )
    snap = crud.get_snap(db, current_user, gameUUID, moveNum)
    if not snap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="snap not found",
            headers={"Authorization": "Bearer"},
        )
    return snap

@app.get("/games/{gameUUID}/snaps")
async def get_snaps(
    gameUUID: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    game = await get_active_game(gameUUID, current_user, db)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="game not found",
            headers={"Authorization": "Bearer"},
        )

    # print(game.__dict__)
    # for snap in db.query(models.GameSnap).all():
    #     print(snap.__dict__)
    return game.snaps