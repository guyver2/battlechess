from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy_utils import create_database, database_exists

from battlechess.server import crud, models
from battlechess.server.btchApi import app, get_db
from battlechess.server.btchApiDB import Base
from battlechess.server.schemas import GameStatus
from battlechess.server.utils import get_password_hash, verify_password


@pytest.fixture
def fakeusersdb():
    fake_users_db = {
        "johndoe": {
            "username": "johndoe",
            "full_name": "John Doe",
            "email": "johndoe@example.com",
            "hashed_password": get_password_hash("secret"),
            "disabled": False,
            "avatar": None,
            "created_at": datetime(2021, 1, 1, tzinfo=timezone.utc),
        },
        "janedoe": {
            "username": "janedoe",
            "full_name": "Jane Doe",
            "email": "janedoe@example.com",
            "hashed_password": get_password_hash("secret"),
            "disabled": False,
            "avatar": None,
            "created_at": datetime(2021, 1, 1, tzinfo=timezone.utc),
        },
    }
    return fake_users_db


@pytest.fixture(scope="function")
def janedoe():
    return {
        "avatar": None,
        "email": "janedoe@example.com",
        "full_name": "Jane Doe",
        "username": "janedoe",
    }


@pytest.fixture(scope="function")
def johndoe():
    return {
        "avatar": None,
        "email": "johndoe@example.com",
        "full_name": "John Doe",
        "username": "johndoe",
    }


@pytest.fixture
def fakegamesdb():
    fake_games_db = {
        "lkml4a3.d3": {
            "uuid": "lkml4a3.d3",
            "owner": "johndoe",
            "white": "johndoe",
            "black": "janedoe",
            "status": GameStatus.STARTED,
            "public": False,
            "turn": "black",
            "created_at": datetime(2021, 1, 1, tzinfo=timezone.utc),
        },
        "da39a3ee5e": {
            "uuid": "da39a3ee5e",
            "owner": "janedoe",
            "white": "johndoe",
            "black": "janedoe",
            "status": GameStatus.OVER,
            "public": False,
            "winner": "johndoe",
            "turn": None,
            "created_at": datetime(2021, 3, 12, tzinfo=timezone.utc),
        },
        "da40a3ee5e": {
            "uuid": "da39a3ee5e",
            "owner": "janedoe",
            "white": None,
            "black": "janedoe",
            "status": GameStatus.WAITING,
            "public": True,
            "winner": None,
            "created_at": datetime(2021, 3, 12, tzinfo=timezone.utc),
        },
        "123fr12339": {
            "uuid": "123fr12339",
            "owner": "janedoe",
            "white": "janedoe",
            "black": None,
            "status": GameStatus.WAITING,
            "public": True,
            "created_at": datetime(2021, 4, 5, tzinfo=timezone.utc),
        },
        "d3255bfef9": {
            "uuid": "d3255bfef9",
            "owner": "johndoe",
            "white": "johndoe",
            "black": None,
            "status": GameStatus.WAITING,
            "public": False,
            "created_at": datetime(2021, 4, 5, tzinfo=timezone.utc),
        },
    }
    return fake_games_db


def fakegamesnapsdb():
    fake_games_snaps = [
        {
            "game_uuid": "lkml4a3.d3",
            "move": "",
            "board": (
                "RNBQKBNR"
                "PPPPPPPP"
                "________"
                "________"
                "________"
                "________"
                "pppppppp"
                "rnbqkbnr"
            ),
            "taken": "",
            "castleable": "LKSlks",
            "move_number": 0,
            "created_at": datetime(2021, 4, 5, 0, tzinfo=timezone.utc),
        },
        {
            "game_uuid": "lkml4a3.d3",
            "move": "d2d4",
            "board": (
                "RNBQKBNR"
                "PPPPPPPP"
                "________"
                "________"
                "___p____"
                "________"
                "ppp_pppp"
                "rnbqkbnr"
            ),
            "taken": "",
            "castleable": "LKSlks",
            "move_number": 1,
            "created_at": datetime(2021, 4, 5, 10, tzinfo=timezone.utc),
        },
    ]
    return fake_games_snaps


@pytest.fixture(scope="function")
def addFakeUsers(db, fakeusersdb):
    for username, user in fakeusersdb.items():
        db_user = models.User(
            username=user["username"],
            full_name=user["full_name"],
            email=user["email"],
            hashed_password=user["hashed_password"],
        )
        db.add(db_user)
        db.commit()
    firstusername, _ = fakeusersdb.keys()
    return getToken(firstusername), firstusername


def addFakeGamesFromDict(db, gamesdb):
    for uuid, game in gamesdb.items():
        owner = (
            db.query(models.User).filter(models.User.username == game["owner"]).first()
        )
        white = (
            db.query(models.User).filter(models.User.username == game["white"]).first()
        )
        black = (
            db.query(models.User).filter(models.User.username == game["black"]).first()
        )
        db_game = models.Game(
            created_at=game["created_at"],
            uuid=game["uuid"],
            owner_id=owner.id,
            white_id=white.id if white is not None else None,
            black_id=black.id if black is not None else None,
            status=game["status"],
            last_move_time=None,
            turn=game.get("turn", None),
            public=game["public"],
        )
        print(db_game.__dict__)
        db.add(db_game)
        db.commit()
        # force None turn since db defaults to white on creation
        if "turn" in game and game["turn"] is None:
            db_game.turn = None
            db.commit()
        print(
            f"adding game between {white.id if white is not None else None} and {black.id if black is not None else None}"
        )
    return uuid


@pytest.fixture(scope="function")
def addFakeGames(db, fakegamesdb):
    gamesdb = fakegamesdb
    return addFakeGamesFromDict(db, gamesdb)


@pytest.fixture(scope="function")
def addFakeDoneGames(db, fakegamesdb):
    gamesdbmod = fakegamesdb
    gamesdbmod["123fr12339"]["status"] = "done"
    gamesdbmod["da40a3ee5e"]["status"] = "done"
    return addFakeGamesFromDict(db, gamesdbmod)


@pytest.fixture(scope="function")
def addFakeGameSnaps(db):
    # TODO get game from uuid
    for snap in fakegamesnapsdb():
        guuid = snap["game_uuid"]

        game = crud.get_game_by_uuid(db, guuid)

        db_snap = models.GameSnap(
            created_at=snap["created_at"],
            game_id=game.id,
            board=snap["board"],
            move=snap["move"],
            taken=snap["taken"],
            castleable=snap["castleable"],
            move_number=snap["move_number"],
        )
        db.add(db_snap)
        db.commit()


@pytest.fixture(scope="function")
def addFakeGameStartSnap(db):
    snap = fakegamesnapsdb()[0]
    guuid = snap["game_uuid"]

    game = crud.get_game_by_uuid(db, guuid)

    db_snap = models.GameSnap(
        created_at=snap["created_at"],
        game_id=game.id,
        board=snap["board"],
        move=snap["move"],
        taken=snap["taken"],
        castleable=snap["castleable"],
        move_number=snap["move_number"],
    )
    db.add(db_snap)
    db.commit()


@pytest.fixture(scope="function")
def addCustomGameSnap(request, db):
    boardStr, move = request.param
    guuid = "lkml4a3.d3"

    game = crud.get_game_by_uuid(db, guuid)

    db_snap = models.GameSnap(
        created_at=datetime(2021, 4, 5, 10, tzinfo=timezone.utc),
        game_id=game.id,
        board=boardStr,
        move=move,
        taken="",
        castleable="",
        move_number=2,
    )
    db.add(db_snap)
    db.commit()


def getToken(username):
    return crud.create_access_token(
        data={"sub": username}, expires_delta=timedelta(minutes=3000)
    )


@pytest.fixture(scope="function")
def classicSetup(db, addFakeUsers, addFakeGames, fakegamesdb, addFakeGameSnaps):
    token, _ = addFakeUsers
    firstgame_uuid = list(fakegamesdb.values())[0]["uuid"]

    return firstgame_uuid, token


@pytest.fixture(scope="session")
def db_engine():
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.db"

    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    if not database_exists:
        create_database(engine.url)

    Base.metadata.create_all(bind=engine)
    yield engine


@pytest.fixture(scope="function")
def db(db_engine):
    connection = db_engine.connect()

    # begin a non-ORM transaction
    transaction = connection.begin()

    # bind an individual Session to the connection
    db = Session(bind=connection)
    # db = Session(db_engine)

    yield db

    db.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db):
    app.dependency_overrides[get_db] = lambda: db

    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
async def asyncclient(db):
    app.dependency_overrides[get_db] = lambda: db

    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c


def getToken(username):
    return crud.create_access_token(
        data={"sub": username}, expires_delta=timedelta(minutes=3000)
    )


@pytest.fixture(scope="function")
def game_setup(db, addFakeUsers, addFakeGames, addFakeGameStartSnap, fakegamesdb):
    _, _ = addFakeUsers
    jane_token = getToken("janedoe")
    john_token = getToken("johndoe")
    firstgame_uuid = list(fakegamesdb.values())[0]["uuid"]

    return firstgame_uuid, john_token, jane_token
