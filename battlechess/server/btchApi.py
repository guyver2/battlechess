from datetime import timedelta
from typing import List, Union

from fastapi import (
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing_extensions import Annotated

from battlechess.server import crud, models, schemas
from battlechess.server.btchApiDB import SessionLocal, engine
from battlechess.server.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from battlechess.server.schemas import GameStatus

PASSWORD_MIN_LENGTH = 3
AVATAR_MAX_SIZE = 100000

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


def valid_content_length(content_length: int = Header(..., lt=AVATAR_MAX_SIZE)):
    return content_length


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
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


def get_current_active_user(current_user: schemas.User = Depends(get_current_user)):
    if not current_user.is_active():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


def get_game(
    gameUUID,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # TODO check if public and owner/player
    game = crud.get_game_by_uuid(db, gameUUID)
    return game


def set_player(
    game: models.Game,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    game.set_player(current_user)

    # if all players are there and game is waiting, start
    if game.is_waiting() and game.is_full():
        crud.create_default_snap(db, current_user, game)
        game.start_game()

    # if this is not here start_game doesn't change the state of the game
    db.commit()

    return game


@app.get("/version")
def version():
    return {"version": "1.0"}


@app.post("/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
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


@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: schemas.User = Depends(get_current_active_user)):
    return current_user


@app.get("/users/me/games", response_model=List[schemas.Game])
def read_own_games(
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    print("read own games")
    games = crud.get_games_by_player(db, current_user)
    return games


@app.get("/users", response_model=List[schemas.User])
def read_users_all(
    skip: int = 0,
    limit: int = 100,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/usernames", response_model=List[str])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return [user.username for user in users]


@app.get("/users/u/{userID}", response_model=schemas.User)
def read__single_user(
    userID: int,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_id(db, userID)
    return user


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


@app.post("/users")
def create_user(new_user: schemas.UserCreate, db: Session = Depends(get_db)):
    if not (
        3 <= len(new_user.username) <= 15
        and len(new_user.plain_password) >= PASSWORD_MIN_LENGTH
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"username should be of lenght (3-15) and password at least {PASSWORD_MIN_LENGTH} chars.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if new_user.email is None:
        new_user.email = ""

    if crud.get_user_by_username(db, new_user.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="username taken",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif crud.get_user_by_email(db, new_user.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="an account with this email already exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        _ = crud.create_user(db, new_user)
        return crud.get_user_by_username(db, new_user.username)


# TODO fix the put method for user
@app.put("/users/update")
def update_user(
    updated_user: schemas.User,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if updated_user.email is None:
        updated_user.email = ""

    db_user = crud.update_user(db, current_user, updated_user)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"user {current_user} not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return db_user


# first a default avatar is created, so the avatar is always updated
@app.put("/users/u/{userID}/avatar", dependencies=[Depends(valid_content_length)])
def update_avatar_file(
    file: UploadFile = File(...),
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    # TODO check that file is sane before saving

    # img = Image.open(file)
    # try:
    #     img.verify()
    # except (IOError, SyntaxError) as e:
    #     raise HTTPException(
    #         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    #         detail=f"file failed image verification",
    #         headers={"WWW-Authenticate": "Bearer"})

    try:
        output = crud.create_avatar_file(db, current_user, file)
    except Exception as err:
        raise HTTPException(
            detail=f"{err} encountered while uploading {file.filename}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    finally:
        file.file.close()

    return {"filename": output}


@app.post("/games")
def post_new_game(
    new_game: schemas.GameCreate,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    game = crud.create_game(db, current_user, new_game)
    return game


@app.get("/games/{gameUUID}", response_model=schemas.Game)
def get_game_by_uuid(
    gameUUID: str,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    game =  crud.get_game_by_uuid(db, gameUUID)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"game {gameUUID} not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return game

# TODO test and should it be a pydantic GameStatus?
@app.get("/games/{gameUUID}/status", response_model=str)
def get_game_status_by_uuid(
    gameUUID: str,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    game = crud.get_game_by_uuid(db, gameUUID)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"game {gameUUID} not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return game.status


# lists available games
@app.get("/games", response_model=List[schemas.Game])
def get_available_games(
    status: Annotated[Union[List[str], None], Query()] = None,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    games = crud.get_games_by_status(db, current_user, status)
    return games


# TODO should be patch
# joines an existing game. error when game already started
@app.get("/games/{gameUUID}/join", response_model=schemas.Game)
def join_game(
    gameUUID: str,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    game = get_game(gameUUID, current_user, db)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="game not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    game = set_player(game, current_user, db)

    return game


# TODO set player ready (maybe not necessary since we're not timing)
# @app.get("/games/{gameUUID}/join")
# def join_game(
#     gameUUID: str,
#     current_user: schemas.User = Depends(get_current_active_user),
#     db: Session = Depends(get_db)
# ):
#     game = get_game(gameUUID, current_user, db)
#     if not game:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="game not found",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     game.set_player(current_user)
#     return game


# either creates a new game or joins an existing unstarted random game. Random games can not be joined via "join_game".
@app.patch("/games", response_model=schemas.Game)
def join_random_game(
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    game = crud.get_random_public_game_waiting(db, current_user)
    if not game:
        print("random game not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="available random game not found",
            headers={"Authorization": "Bearer"},
        )

    game = set_player(game, current_user, db)

    db.refresh(game)
    print(game.owner)
    return game


# serialized board state
@app.get("/games/{gameUUID}/board")
def query_board(
    gameUUID: str,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    pass


# who's turn is it (None means that the game is over)
@app.get("/games/{gameUUID}/turn")
def query_turn(
    gameUUID: str,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    game = get_game(gameUUID, current_user, db)
    return game.turn


@app.post("/games/{gameUUID}/move", response_model=schemas.GameSnap)
def post_move(
    gameUUID: str,
    # move: dict = Body(...), # or pydantic or query parameter? Probably pydantic to make clear what a move is
    gameMove: schemas.GameMove,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    game = get_game(gameUUID, current_user, db)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="game not found",
            headers={"Authorization": "Bearer"},
        )

    if game.status != GameStatus.STARTED:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="game is not started",
            headers={"Authorization": "Bearer"},
        )

    # It looks like modifying the pydantic model does not change the db model
    snap = crud.create_snap_by_move(db, current_user, game, gameMove)
    snap4player = schemas.GameSnap.model_validate(snap)
    snap4player.prepare_for_player(game.get_player_color(current_user.id))
    return snap4player


# TODO List[str] might throw ValidationError: <unprintable ValidationError object>
# due to
@app.get("/games/{gameUUID}/moves/{square}", response_model=List[str])
def get_moves(
    gameUUID: str,
    square: str,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    game = get_game(gameUUID, current_user, db)
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

    # TODO pydantic square validation possible?
    if len(square) != 2 or square < "a1" or "h8" < square:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="square is not of format ['a1', 'h8'] ",
            headers={"Authorization": "Bearer"},
        )

    snap = game.snaps[-1]
    color = game.get_player_color(current_user.id)
    moves = snap.getPossibleMoves(square, color)

    # TODO remove this if we're happy with a weird validation error message
    if moves:
        assert type(moves[0]) == str
    return moves


@app.get("/games/{gameUUID}/snap", response_model=schemas.GameSnap)
def get_snap(
    gameUUID: str,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    game = get_game(gameUUID, current_user, db)
    # user not allowed to query that game snap for now
    if (game.status != GameStatus.OVER) and (
        current_user.id not in [game.white_id, game.black_id]
    ):
        game = None
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="game not found",
            headers={"Authorization": "Bearer"},
        )

    if game.is_waiting():
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="a waiting game has no snaps",
            headers={"Authorization": "Bearer"},
        )

    if len(game.snaps) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="snap not found",
            headers={"Authorization": "Bearer"},
        )

    snap = game.snaps[-1]

    if not snap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="snap not found",
            headers={"Authorization": "Bearer"},
        )

    if game.status != GameStatus.STARTED or not game.black_id or not game.white_id:
        return snap

    player_color = "black" if current_user.id == game.black_id else "white"
    snap4player = schemas.GameSnap.model_validate(snap)
    if game.status != GameStatus.OVER:
        print(f"preparing board for {current_user.username} {player_color}")
        snap4player.prepare_for_player(player_color)

    return snap4player


@app.get("/games/{gameUUID}/snap/{moveNum}", response_model=schemas.GameSnap)
def get_snap_by_move(
    gameUUID: str,
    moveNum: int,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    game = get_game(gameUUID, current_user, db)
    # user not allowed to query that game snap for now
    if (game.status != GameStatus.OVER) and (
        current_user.id not in [game.white_id, game.black_id]
    ):
        game = None
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

    print(f"check if we need to prepare snap {game.status}")

    snap4player = schemas.GameSnap.model_validate(snap)
    if game.status != GameStatus.OVER:
        player_color = "black" if current_user.id == game.black_id else "white"
        snap4player.prepare_for_player(player_color)
    else:
        print("game is over and snap is",snap4player)
    return snap4player


@app.get("/games/{gameUUID}/snaps", response_model=List[schemas.GameSnap])
def get_snaps(
    gameUUID: str,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    game = get_game(gameUUID, current_user, db)
    # user not allowed to query that game snap for now
    if (game.status != GameStatus.OVER) and (
        current_user.id not in [game.white_id, game.black_id]
    ):
        game = None
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="game not found",
            headers={"Authorization": "Bearer"},
        )

    player_color = "black" if current_user.id == game.black_id else "white"
    result = []
    for snap in game.snaps:

        snap4player = schemas.GameSnap.model_validate(snap)
        if game.status != GameStatus.OVER:
            snap4player.prepare_for_player(player_color)
        result.append(snap4player)
    return result
