import pytest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy_utils import create_database
from sqlalchemy_utils import database_exists

from battlechess.server import crud, models
from battlechess.server.btchApi import app, get_db
from battlechess.server.btchApiDB import Base
from battlechess.server.schemas import GameStatus
from battlechess.server.utils import get_password_hash, verify_password

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

def getToken(username):
    return crud.create_access_token(
        data={"sub": username}, expires_delta=timedelta(minutes=3000)
    )

@pytest.fixture(scope="function")
def game_setup(db):
    _, _ = addFakeUsers(db)
    jane_token = getToken("janedoe")
    john_token = getToken("johndoe")
    addFakeGames(db, fakegamesdb())
    firstgame_uuid = list(fakegamesdb().values())[0]["uuid"]
    addFakeGameSnaps(db, fakegamesnapsdb())

    return firstgame_uuid, john_token, jane_token


