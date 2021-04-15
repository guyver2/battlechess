import unittest
import unittest.mock as mock
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from jose import JWTError, jwt

from .btchApi import app, get_db

from .btchApiDB import SessionLocal, Base, BtchDBContextManager
from . import crud, models
from .utils import get_password_hash

from fastapi.testclient import TestClient

# TODO we might want to use a Test db context manager with
# all the setUpClass code in it to handle the db session
# and then rollback at the end of the test instead of dropping tables
# something like:
#  class TestBtchDBContextManager:
#      def __init__(self):
#         SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

#         engine = create_engine(
#             SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
#         )

#         TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

#         self.db = TestingSessionLocal()

#     def __enter__(self):
#         return self.db

#     def __exit__(self, exc_type, exc_value, traceback):
#         self.db.close()


class Test_Api(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

        cls.engine = create_engine(
            SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
        )

        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    @classmethod
    def override_get_db(cls):
        try:
            db = cls.TestingSessionLocal()
            yield db
        finally:
            db.close()

    def fakeusersdb(self):
        fake_users_db = {
            "johndoe": {
                "username": "johndoe",
                "full_name": "John Doe",
                "email": "johndoe@example.com",
                "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
                "disabled": False,
            },
            "janedoe": {
                "username": "janedoe",
                "full_name": "Jane Doe",
                "email": "janedoe@example.com",
                "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
                "disabled": False,
            }
        }
        return fake_users_db

    def fakegamesdb(self):
        fake_games_db = {
            "lkml4a3.d3": {
                "handle": "lkml4a3.d3",
                "owner": "johndoe",
                "white": "johndoe",
                "black": "janedoe",
                "status": "started",
                "turn": "johndoe",
                "create_time": datetime(2021, 1, 1, tzinfo=timezone.utc),
            },
            "da39a3ee5e": {
                "handle": "da39a3ee5e",
                "owner": "janedoe",
                "white": "johndoe",
                "black": "janedoe",
                "status": "done",
                "winner": "johndoe",
                "create_time": datetime(2021, 3, 12, tzinfo=timezone.utc),
            },
            "d3255bfef9": {
                "handle": "d3255bfef9",
                "owner": "johndoe",
                "white": "johndoe",
                "black": None,
                "status": "idle",
                "create_time": datetime(2021, 4, 5, tzinfo=timezone.utc),
            }
        }
        return fake_games_db

    def addFakeUsers(self, db):
        for username, user in self.fakeusersdb().items():
            db_user = models.User(
                username=user["username"],
                full_name=user["full_name"],
                email=user["email"],
                hashed_password=user["hashed_password"]
            )
            db.add(db_user)
            db.commit()
        firstusername,_ = self.fakeusersdb().keys()
        return self.getToken(firstusername)

    def addFakeGames(self, db):
        for handle, game in self.fakegamesdb().items():
            owner = db.query(models.User).filter(models.User.username == game['owner']).first()
            white = db.query(models.User).filter(models.User.username == game['white']).first()
            black = db.query(models.User).filter(models.User.username == game['black']).first()
            db_game = models.Game(
                create_time=game["create_time"],
                handle=game["handle"],
                owner_id=owner.id,
                white_id=white.id if white is not None else None,
                black_id=black.id if black is not None else None,
                status=game["status"],
                turn=game.get("turn", "white"),
                random=game.get("random", False),
            )
            db.add(db_game)
            db.commit()
        return handle

    def getToken(self, username):
        return crud.create_access_token(
            data={"sub": username}, expires_delta=timedelta(minutes=3000)
        )

    def setUp(self):
        # TODO setUp correctly with begin-rollback instead of create-drop
        # create db, users, games...

        # Base = declarative_base()

        Base.metadata.create_all(bind=self.engine)

        app.dependency_overrides[get_db] = self.override_get_db

        self.client = TestClient(app)

        self.db = self.TestingSessionLocal()

    def tearDown(self):
        # delete db
        self.db.close()
        Base.metadata.drop_all(self.engine)
        pass

    def test__version(self):
        response = self.client.get("/version")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"version": "1.0"})

    def test__createUser(self):
        hashed_password = get_password_hash("secret")
        response = self.client.post(
            "/users/",
            json={
                "username": "alice",
                "full_name": "Alice la Suisse",
                "email": "alice@lasuisse.ch",
                "hashed_password": hashed_password
            },
        )

        print(response.json())

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json())
        self.assertDictEqual(response.json(), {
            "username": "alice",
            "full_name": "Alice la Suisse",
            "email": "alice@lasuisse.ch",
            "id": 1,
            "hashed_password": hashed_password,
            "is_active": True
        })

    def test__getUsers__unauthorized(self):
        response = self.client.get("/users/")
        self.assertEqual(response.status_code, 401)

    def test__authenticate(self):

        # add a user
        hashed_password = get_password_hash("secret")
        response = self.client.post(
            "/users/",
            json={
                "username": "alice",
                "full_name": "Alice la Suisse",
                "email": "alice@lasuisse.ch",
                "hashed_password": hashed_password,
            },
        )

        # test auth
        response = self.client.post(
            "/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "username": "alice",
                "password": "secret",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertListEqual(list(response.json().keys()), ['access_token', 'token_type'])

    def test__createUser__persistence(self):
        hashed_password = crud.get_password_hash("secret")
        response = self.client.post(
            "/users/",
            json={
                "username": "alice",
                "full_name": "Alice la Suisse",
                "email": "alice@lasuisse.ch",
                "hashed_password": hashed_password
            },
        )

        response = self.client.post(
            "/token",
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={
                "username": "alice",
                "password": "secret",
            },
        )

        self.assertIsNotNone(response.json())
        print(response.json())
        self.assertIn('access_token', response.json())
        token = response.json()['access_token']

        response = self.client.get(
            "/users/usernames",
            headers={"Authorization": "Bearer " + token},
        )

        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.json(), ["alice"])

    def test__addFakeUsers(self):
        self.addFakeUsers(self.db)

    def test__getUsernames(self):
        token = self.addFakeUsers(self.db)

        users = self.db.query(models.User).all()

        response = self.client.get(
            "/users/usernames",
            headers={"Authorization": "Bearer " + token},
        )

        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.json(), ["johndoe", "janedoe"])

    def test__db_cleanup(self):

        users = self.db.query(models.User).all()

        self.assertListEqual(users, [])

    def test__createGame(self):
        token = self.addFakeUsers(self.db)

        response = self.client.post(
            '/games/',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
            json={
                'random': False,
            },
        )

        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {
            'black_id': None,
            'create_time': mock.ANY,
            'handle': mock.ANY,
            'id': 1,
            'owner_id': 1,
            'random': False,
            'status': 'idle',
            'turn': 'white',
            'white_id': None
        })

    def test__get_game_by_handle(self):
        token = self.addFakeUsers(self.db)
        handle = self.addFakeGames(self.db)

        response = self.client.get(
            f'/games/{handle}',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
            json={
                'random': False,
            },
        )

        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {
            'black_id': None,
            'create_time': mock.ANY,
            'handle': mock.ANY,
            'id': 3,
            'owner_id': 1,
            'random': False,
            'status': 'idle',
            'turn': 'white',
            'white_id': 1,
        })

    # TODO
    def test__joinRandomGame(self):
        token = self.addFakeUsers(self.db)
        handle = self.addFakeGames(self.db)

        response = self.client.get(
            f'/games/random',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {
            'black_id': None,
            'create_time': mock.ANY,
            'handle': mock.ANY,
            'id': 3,
            'owner_id': 1,
            'random': False,
            'status': 'idle',
            'turn': 'white',
            'white_id': 1,
        })

    def _test__findGame(self):
        token = self.addFakeUsers(self.db)
        handle = self.addFakeGames(self.db)

        response = self.client.get(
            f'/games/{handle}/join',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
            json={
                'random': False,
            },
        )

        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {
            'black_id': None,
            'create_time': mock.ANY,
            'handle': mock.ANY,
            'id': 3,
            'owner_id': 1,
            'random': False,
            'status': 'idle',
            'turn': 'white',
            'white_id': 1,
        })


    def _test__joinGame(self):
        token = self.addFakeUsers(self.db)
        handle = self.addFakeGames(self.db)

        response = self.client.get(
            f'/games/{handle}/join',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
            json={
                'random': False,
            },
        )

        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {
            'black_id': None,
            'create_time': mock.ANY,
            'handle': mock.ANY,
            'id': 3,
            'owner_id': 1,
            'random': False,
            'status': 'idle',
            'turn': 'white',
            'white_id': 1,
        })
