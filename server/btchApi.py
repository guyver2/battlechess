from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Set, List

from sqlalchemy.orm import Session

from fastapi import Depends, FastAPI, HTTPException, status, Body
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

async def get_game(
    gameUUID,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # TODO check if public and owner/player
    game = crud.get_game_by_uuid(db, gameUUID)
    return game

async def set_player(
    game: models.Game,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    game.set_player(current_user)

    # if all players are there, start
    if game.is_full():
        crud.create_default_snap(db, current_user, game)
        game.start_game()

    # if this is not here start_game doesn't change the state of the game
    db.commit()

    return game


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
async def read_users_me(
    current_user: schemas.User = Depends(get_current_active_user)
):
    return current_user


@app.get("/users/me/games/")
async def read_own_games(
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
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    users = crud.get_users(db, skip=skip, limit=limit)
    return [user.username for user in users]

# we might be playing more than one game, we no longer can use this as-is
# @app.get("/users/active_game")
# def read_users(db: Session = Depends(get_db)):
#     game = get_game(gameUUID, current_user, db)
#     if not game:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="game not found",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     return game

@app.post("/users/")
def create_user(
    new_user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
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
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return crud.create_game(db, current_user, new_game)

@app.get("/games/{gameUUID}")
def get_game_by_uuid(
    gameUUID: str,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return crud.get_game_by_uuid(db, gameUUID)

# lists available games
@app.get("/games", response_model=List[schemas.Game])
async def list_available_games(
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    games = crud.get_public_game_by_status(db, current_user, "waiting")
    if not games:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no public games were found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return games

#TODO should be patch
# joines an existing game. error when game already started
@app.get("/games/{gameUUID}/join")
async def join_game(
    gameUUID: str,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    game = await get_game(gameUUID, current_user, db)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="game not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    game = await set_player(game, current_user, db)

    return game

# TODO set player ready (maybe not necessary since we're not timing)
# @app.get("/games/{gameUUID}/join")
# async def join_game(
#     gameUUID: str,
#     current_user: schemas.User = Depends(get_current_active_user),
#     db: Session = Depends(get_db)
# ):
#     game = await get_game(gameUUID, current_user, db)
#     if not game:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="game not found",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     game.set_player(current_user)
#     return game

# either creates a new game or joins an existing unstarted random game. Random games can not be joined via "join_game".
@app.patch("/games")
async def join_random_game(
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    game = crud.get_random_public_game_waiting(db, current_user)
    if not game:
        return {}

    game = await set_player(game, current_user, db)

    db.refresh(game)

    return game

# serialized board state
@app.get("/games/{gameUUID}/board")
async def query_board(
    gameUUID: str,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    pass

# who's turn is it (None means that the game is over)
@app.get("/games/{gameUUID}/turn")
async def query_turn(
    gameUUID: str,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    game = await get_game(gameUUID, current_user, db)
    return game.turn


@app.post("/games/{gameUUID}/move")
async def post_move(
    gameUUID: str,
    #move: dict = Body(...), # or pydantic or query parameter? Probably pydantic to make clear what a move is
    gameMove: schemas.GameMove,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    game = await get_game(gameUUID, current_user, db)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="game not found",
            headers={"Authorization": "Bearer"},
        )

    if game.status != "started":
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="game is not started",
            headers={"Authorization": "Bearer"},
        )

    # snap = game.move(gameMove.move)
    # deprecated in favor of creating the snap directly in the model
    # crud.create_snap_by_dict()

    # It looks like modifying the pydantic model does not change the db model
    snap = crud.create_snap_by_move(db, current_user, game, gameMove)
    schemasnap = schemas.GameSnap.from_orm(snap)
    filteredsnap = schemasnap.prepare_for_player(game.get_player_color(current_user.id))
    return filteredsnap



@app.get("/games/{gameUUID}/snap")
async def get_snap(
    gameUUID: str,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    game = await get_game(gameUUID, current_user, db)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="game not found",
            headers={"Authorization": "Bearer"},
        )
    snap = game.snaps[-1]
    if not snap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="snap not found",
            headers={"Authorization": "Bearer"},
        )
    return snap

@app.get("/games/{gameUUID}/snap/{moveNum}")
async def get_snap(
    gameUUID: str,
    moveNum: int,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    game = await get_game(gameUUID, current_user, db)
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
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    game = await get_game(gameUUID, current_user, db)
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