import unittest
import unittest.mock as mock
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from pathlib import Path

import sys
try:
    from PIL import Image
except ImportError:
    print('PIL module is not installed. Some tests will be skipped')


from jose import JWTError, jwt

from fastapi.testclient import TestClient
from fastapi import HTTPException, status

from .btchApi import app, get_db

from .btchApiDB import SessionLocal, Base, BtchDBContextManager
from . import crud, models
from .schemas import GameStatus
from .utils import get_password_hash, verify_password

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

# uncomment this to debug SQL
# import logging
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


class Test_Api(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

        cls.engine = create_engine(
            SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    @classmethod
    def override_get_db(cls):
        try:
            db = cls.TestingSessionLocal()
            yield db
        finally:
            db.close()

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

    def testDataDir(self):
        return Path(__file__).parent.parent / "data" / "avatars"

    def fakeusersdb(self):
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
            }
        }
        return fake_users_db

    def fakegamesdb(self):
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
            }
        }
        return fake_games_db

    def fakegamesnapsdb(self):
        fake_games_snaps = [{
            "game_uuid": "lkml4a3.d3",
            "move": "",
            "board": ('RNBQKBNR'
                      'PPPPPPPP'
                      '________'
                      '________'
                      '________'
                      '________'
                      'pppppppp'
                      'rnbqkbnr'),
            "taken": "",
            "castleable": "",
            "move_number": 0,
            "created_at": datetime(2021, 4, 5, 0, tzinfo=timezone.utc),
        }, {
            "game_uuid": "lkml4a3.d3",
            "move": "d2d4",
            "board": ('RNBQKBNR'
                      'PPPPPPPP'
                      '________'
                      '________'
                      '___p____'
                      '________'
                      'ppp_pppp'
                      'rnbqkbnr'),
            "taken": "",
            "castleable": "",
            "move_number": 1,
            "created_at": datetime(2021, 4, 5, 10, tzinfo=timezone.utc),
        }]
        return fake_games_snaps

    def addFakeUsers(self, db):
        for username, user in self.fakeusersdb().items():
            db_user = models.User(
                username=user["username"],
                full_name=user["full_name"],
                email=user["email"],
                hashed_password=user["hashed_password"])
            db.add(db_user)
            db.commit()
        firstusername, _ = self.fakeusersdb().keys()
        return self.getToken(firstusername), firstusername

    def addFakeGames(self, db, fakegamesdb):
        for uuid, game in fakegamesdb.items():
            owner = db.query(models.User).filter(models.User.username == game['owner']).first()
            white = db.query(models.User).filter(models.User.username == game['white']).first()
            black = db.query(models.User).filter(models.User.username == game['black']).first()
            db_game = models.Game(
                created_at=game["created_at"],
                uuid=game["uuid"],
                owner_id=owner.id,
                white_id=white.id if white is not None else None,
                black_id=black.id if black is not None else None,
                status=game["status"],
                last_move_time=None,
                turn=game.get("turn", None),
                public=game["public"])
            print(db_game.__dict__)
            db.add(db_game)
            db.commit()
            # force None turn since db defaults to white on creation
            if "turn" in game and game["turn"] == None:
                db_game.turn = None
                db.commit()
            print(
                f"adding game between {white.id if white is not None else None} and {black.id if black is not None else None}"
            )
        return uuid

    def addFakeGameSnaps(self, db, fakegamesnaps):
        # TODO get game from uuid
        for snap in fakegamesnaps:
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

    def addCustomGameSnap(self, db, boardStr, move):
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

    def getToken(self, username):
        return crud.create_access_token(
            data={"sub": username}, expires_delta=timedelta(minutes=3000))

    def classicSetup(self):
        token, _ = self.addFakeUsers(self.db)
        self.addFakeGames(self.db, self.fakegamesdb())
        firstgame_uuid = list(self.fakegamesdb().values())[0]["uuid"]
        self.addFakeGameSnaps(self.db, self.fakegamesnapsdb())

        return firstgame_uuid, token

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
                "plain_password": "secret"
            },
        )

        print(response.json())

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json())
        response_dict = response.json()
        self.assertTrue(verify_password("secret", response_dict["hashed_password"]))
        response_dict.pop("hashed_password", None)
        self.assertDictEqual(
            response_dict, {
                "username": "alice",
                "created_at": mock.ANY,
                "full_name": "Alice la Suisse",
                "email": "alice@lasuisse.ch",
                "id": 1,
                "avatar": None,
                "status": "active",
            })

    def test__create_user__with_avatar(self):
        hashed_password = get_password_hash("secret")
        new_avatar = "images/avatar001.jpeg"
        response = self.client.post(
            "/users/",
            json={
                "username": "alice",
                "full_name": "Alice la Suisse",
                "email": "alice@lasuisse.ch",
                "avatar": new_avatar,
                "plain_password": "secret"
            },
        )

        print(response.json())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['avatar'], new_avatar)

    # TODO fix the put method for user
    def _test__update_user__full_name(self):
        token, _ = self.addFakeUsers(self.db)

        oneUser = self.db.query(models.User)[1]

        new_full_name = "Alicia la catalana"

        response = self.client.put(
            f'/users/update',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
            json={
                "username": oneUser.username,
                "full_name": new_full_name,
                "email": oneUser.email,
                "avatar": oneUser.avatar
            })

        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(), {
                "username": "alice",
                "full_name": "Alice la Suisse",
                "email": "alice@lasuisse.ch",
                "avatar": new_full_name,
                "plain_password": "secret"
            })

    @unittest.skipIf('PIL' not in sys.modules, reason="PIL module is not installed")
    def test__upload_user__avatarImage(self):
        token, _ = self.addFakeUsers(self.db)

        oneUser = self.db.query(models.User)[1]
        filename = self.testDataDir() / "test_avatar.jpeg"
        with open(filename, 'rb') as f:
            img = Image.open(f)
            try:
                img.verify()
            except (IOError, SyntaxError) as e:
                print('Bad file:', filename)

        # TODO reset cursor instead of reopening
        with open(filename, 'rb') as f:
            response = self.client.put(
                f'/users/u/{oneUser.id}/avatar',
                headers={'Authorization': 'Bearer ' + token},
                files={'file': f})

        print(response.json())
        self.assertEqual(response.status_code, 200)

        expected_avatar_dir = Path(__file__).parent.parent / "data" / "avatars"
        expected_avatar_filepath = expected_avatar_dir / f"1_avatar.jpeg"
        expected_avatar_file = Path(expected_avatar_filepath)

        # remove the test file from the config directory
        expected_avatar_file.unlink()

    @unittest.skipIf('PIL' not in sys.modules, reason="PIL module is not installed")
    def test__upload_user__avatarImage__file_too_big(self):
        token, _ = self.addFakeUsers(self.db)

        oneUser = self.db.query(models.User)[1]

        img = Image.new(mode='RGB', size=(1000, 1000), color = 'red')
        response = self.client.put(
            f'/users/u/{oneUser.id}/avatar',
            headers={'Authorization': 'Bearer ' + token},
            files={'file': img.tobytes()})

        print(response.json())
        self.assertEqual(response.status_code, 422)

    def test__getUsers__unauthorized(self):
        response = self.client.get("/users/")
        self.assertEqual(response.status_code, 401)

    def test__authenticate(self):

        # add a user
        response = self.client.post(
            "/users/",
            json={
                "username": "alice",
                "full_name": "Alice la Suisse",
                "email": "alice@lasuisse.ch",
                "plain_password": "secret",
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
        response = self.client.post(
            "/users/",
            json={
                "username": "alice",
                "full_name": "Alice la Suisse",
                "email": "alice@lasuisse.ch",
                "plain_password": "secret"
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
        token, _ = self.addFakeUsers(self.db)

        users = self.db.query(models.User).all()

        response = self.client.get(
            "/users/usernames",
            headers={"Authorization": "Bearer " + token},
        )

        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.json(), ["johndoe", "janedoe"])

    def test__getUserById(self):
        token, _ = self.addFakeUsers(self.db)

        response = self.client.get(
            "/users/u/1",
            headers={"Authorization": "Bearer " + token},
        )

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(), {
                'username': 'johndoe',
                'full_name': 'John Doe',
                'email': 'johndoe@example.com',
                'avatar': None,
                'id': 1,
                'status': 'active',
            })

    def test__getUserById__malformedId(self):
        token, _ = self.addFakeUsers(self.db)

        response = self.client.get(
            "/users/u/abcd",
            headers={"Authorization": "Bearer " + token},
        )

        self.assertEqual(response.status_code, 422)
        print(response.json())
        self.assertEqual(response.json()['detail'][0]['type'], 'type_error.integer')

    def test__db_cleanup(self):

        users = self.db.query(models.User).all()

        self.assertListEqual(users, [])

    def test__createGame(self):
        token, _ = self.addFakeUsers(self.db)

        response = self.client.post(
            '/games/',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
            json={
                'public': False,
                'color': 'white'
            },
        )

        print(response.json())
        self.assertEqual(response.status_code, 200)

        self.assertDictEqual(
            response.json(), {
                'black_id': None,
                'created_at': mock.ANY,
                'uuid': mock.ANY,
                'id': 1,
                'last_move_time': None,
                'owner_id': 1,
                'public': False,
                'status': GameStatus.WAITING,
                'turn': 'white',
                'white_id': response.json()["owner_id"],
                'winner': None,
            })

    def test__get_game_by_uuid(self):
        token, _ = self.addFakeUsers(self.db)
        uuid = self.addFakeGames(self.db, self.fakegamesdb())

        response = self.client.get(
            f'/games/{uuid}',
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
        self.assertDictEqual(
            response.json(), {
                'black_id': None,
                'created_at': mock.ANY,
                'uuid': mock.ANY,
                'id': 5,
                'owner_id': 1,
                'last_move_time': None,
                'public': False,
                'status': GameStatus.WAITING,
                'turn': 'white',
                'white_id': 1,
                'winner': None,
            })

    def test__get_me_games(self):
        token, _ = self.addFakeUsers(self.db)
        uuid = self.addFakeGames(self.db, self.fakegamesdb())

        response = self.client.get(
            f'/users/me/games/',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)
        self.assertDictEqual(
            response.json()[0], {
                'black_id': 2,
                'created_at': mock.ANY,
                'uuid': mock.ANY,
                'id': 1,
                'last_move_time': None,
                'owner_id': 1,
                'public': False,
                'last_move_time': None,
                'status': 'started',
                'turn': 'black',
                'white_id': 1,
                'winner': None,
            })

    def test__getGames__finishedGame(self):
        _, _ = self.addFakeUsers(self.db)
        #change to second player
        jane_token = self.getToken("janedoe")
        john_token = self.getToken("johndoe")
        self.addFakeGames(self.db, self.fakegamesdb())
        self.addFakeGameSnaps(self.db, self.fakegamesnapsdb())

        response = self.client.get(
            '/users/me/games',
            headers={
                'Authorization': 'Bearer ' + jane_token,
                'Content-Type': 'application/json',
            },
        )
        print(response.json())
        self.assertEqual(response.status_code, 200)
        games = response.json()
        self.assertEqual(len(games), 4)
        finishedgame = [g for g in games if g['status'] == GameStatus.OVER][0]
        self.assertIsNone(finishedgame['turn'])

    # TODO test list random games before setting my player
    def test__joinRandomGame(self):
        token, _ = self.addFakeUsers(self.db)
        uuid = self.addFakeGames(self.db, self.fakegamesdb())

        oneUser = self.db.query(models.User)[1]

        response = self.client.patch(
            '/games',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        # TODO join game (client chooses one)

        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json(), {})
        self.assertTrue(response.json()['white_id'] == oneUser.id or
                        response.json()['black_id'] == oneUser.id)
        self.assertDictEqual(
            response.json(), {
                'black_id': mock.ANY,
                'created_at': mock.ANY,
                'uuid': mock.ANY,
                'last_move_time': None,
                'id': mock.ANY,
                'owner_id': mock.ANY,
                'public': True,
                'status': 'started',
                'turn': 'white',
                'white_id': mock.ANY,
                'winner': None,
            })
        self.assertTrue(response.json()['black_id'] == oneUser.id or
                        response.json()['white_id'] == oneUser.id)

    # TODO deprecated, client chooses game and joins a random one
    def test__joinRandomGame__noneAvailable(self):
        token, _ = self.addFakeUsers(self.db)
        gamesdbmod = self.fakegamesdb()
        gamesdbmod['123fr12339']['status'] = 'done'
        gamesdbmod['da40a3ee5e']['status'] = 'done'
        uuid = self.addFakeGames(self.db, gamesdbmod)

        response = self.client.patch(
            '/games',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {})

    def test__listAvailableGames(self):
        token, _ = self.addFakeUsers(self.db)
        uuid = self.addFakeGames(self.db, self.fakegamesdb())

        response = self.client.get(
            '/games',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.maxDiff = None
        self.assertListEqual(response.json(), [{
            'id': 3,
            'uuid': mock.ANY,
            'created_at': mock.ANY,
            'owner_id': 2,
            'last_move_time': None,
            'public': True,
            'white_id': None,
            'black_id': 2,
            'status': GameStatus.WAITING,
            'turn': 'white',
            'winner': None,
        }, {
            'black_id': None,
            'created_at': mock.ANY,
            'uuid': mock.ANY,
            'id': 4,
            'last_move_time': None,
            'owner_id': 2,
            'public': True,
            'status': GameStatus.WAITING,
            'turn': 'white',
            'white_id': 2,
            'winner': None,
        }])

    def test__joinGame__playerAlreadyInGame(self):
        token, username = self.addFakeUsers(self.db)
        self.addFakeGames(self.db, self.fakegamesdb())

        uuid = self.fakegamesdb['123fr12339']

        user = crud.get_user_by_username(self.db, username)

        game_before = self.db.query(models.Game).filter(models.Game.uuid == uuid).first()

        response = self.client.get(
            f'/games/{uuid}/join',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        game = self.db.query(models.Game).filter(models.Game.uuid == uuid).first()

        print(response.json())
        self.assertEqual(response.status_code, 200)
        if not game_before.black_id:
            self.assertEqual(game.black_id, user.id)
        if not game_before.white_id:
            self.assertEqual(game.white_id, user.id)
        self.assertDictEqual(
            response.json(), {
                'black_id': game.black_id,
                'created_at': mock.ANY,
                'uuid': game.uuid,
                'id': game.id,
                'last_move_time': None,
                'owner_id': game.owner_id,
                'public': False,
                'status': GameStatus.WAITING,
                'turn': 'white',
                'white_id': game.white_id,
            })

    def test__joinGame__playerAlreadyInGame(self):
        token, username = self.addFakeUsers(self.db)
        uuid = self.addFakeGames(self.db, self.fakegamesdb())

        user = crud.get_user_by_username(self.db, username)

        game_before = self.db.query(models.Game).filter(models.Game.uuid == uuid).first()

        response = self.client.get(
            f'/games/{uuid}/join',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertDictEqual(response.json(), {'detail': 'Player is already in this game'})

    def test__getsnap__byNum(self):
        firstgame_uuid, token = self.classicSetup()
        firstgame_white_player = list(self.fakegamesdb().values())[0]["white"]
        token = self.getToken(firstgame_white_player)
        self.addFakeGameSnaps(self.db, self.fakegamesnapsdb())

        response = self.client.get(
            f'/games/{firstgame_uuid}/snap/0',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        print(response.json())
        self.assertEqual(response.status_code, 200)
        #yapf: disable
        self.assertDictEqual(
            response.json(), {
                'game_id': 1,
                'created_at': mock.ANY,
                'id': 1,
                'move': None,
                'taken': '',
                'castleable': '',
                'move_number': 0,
                'board': ('xxxxxxxx'
                          'xxxxxxxx'
                          '________'
                          '________'
                          '________'
                          '________'
                          'pppppppp'
                          'rnbqkbnr'),
            })
        #yapf: enable

    def test__getsnaps(self):
        self.maxDiff = None
        firstgame_uuid, token = self.classicSetup()

        response = self.client.get(
            f'/games/{firstgame_uuid}/snaps',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        print(response.json())
        self.assertEqual(response.status_code, 200)
        #yapf: disable
        self.assertListEqual(response.json(), [{
            'game_id': 1,
            'created_at': mock.ANY,
            'id': 1,
            'move': None,
            'taken': '',
            'castleable': '',
            'move_number': 0,
            'board': ('xxxxxxxx'
                      'xxxxxxxx'
                      '________'
                      '________'
                      '________'
                      '________'
                      'pppppppp'
                      'rnbqkbnr'),
        }, {
            'game_id': 1,
            'created_at': mock.ANY,
            'id': 2,
            'move': 'd2d4',
            'taken': '',
            'castleable': '',
            'move_number': 1,
            'board': ('xxxxxxxx'
                      'xxxxxxxx'
                      '________'
                      '________'
                      '___p____'
                      '________'
                      'ppp_pppp'
                      'rnbqkbnr'),
        }])
        #yapf: enable

    def test__getsnap__latest(self):
        firstgame_uuid, token = self.classicSetup()

        response = self.client.get(
            f'/games/{firstgame_uuid}/snap',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        print(response.json())
        self.assertEqual(response.status_code, 200)
        #yapf: disable
        self.assertDictEqual(
            response.json(), {
                'game_id': 1,
                'created_at': mock.ANY,
                'id': 2,
                'move': 'd2d4',
                'taken': '',
                'castleable': '',
                'move_number': 1,
                'board': ('xxxxxxxx'
                          'xxxxxxxx'
                          '________'
                          '________'
                          '___p____'
                          '________'
                          'ppp_pppp'
                          'rnbqkbnr')
            })
        #yapf: enable

    def test__getTurn(self):
        firstgame_uuid, token = self.classicSetup()

        response = self.client.get(
            f'/games/{firstgame_uuid}/turn',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'black')

    def test__move(self):
        firstgame_uuid, token = self.classicSetup()

        # get previous game/board

        game_before = self.db.query(models.Game).filter(models.Game.uuid == firstgame_uuid).first()

        response = self.client.post(
            f'/games/{firstgame_uuid}/move',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
            json={
                "move": "d7d5",
            },
        )

        # get after game/board

        game_after = self.db.query(models.Game).filter(models.Game.uuid == firstgame_uuid).first()

        # test board is the expected one
        print([snap.__dict__ for snap in game_after.snaps])

        print(response.json())
        self.assertEqual(response.status_code, 200)
        # self.assertDictEqual(response.json(), '')

        self.assertEqual(
            game_before.get_latest_snap().board,
            ('RNBQKBNR'
             'PPP_PPPP'
             '________'
             '___P____'
             '___p____'
             '________'
             'ppp_pppp'
             'rnbqkbnr'),
        )

    def test__move__filtered(self):
        firstgame_uuid, _ = self.classicSetup()
        #change to second player
        token = self.getToken("janedoe")

        response = self.client.post(
            f'/games/{firstgame_uuid}/move',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
            json={
                "move": "d7d5",
            },
        )

        print(response.json())
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json()['board'],
            ('RNBQKBNR'
             'PPP_PPPP'
             '________'
             '___P____'
             '___p____'
             '________'
             'XXX_XXXX'
             'XXXXXXXX'),
        )

    def test__possibleMoves__pawnMove(self):
        firstgame_uuid, _ = self.classicSetup()
        #change to second player
        token = self.getToken("janedoe")

        square = 'd7'

        response = self.client.get(
            f'/games/{firstgame_uuid}/moves/{square}',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        print("response: {}".format(response.json()))
        self.assertEqual(response.status_code, 200)

        self.assertListEqual(
            response.json(),
            ['d6', 'd5'],
        )

    def test__possibleMoves__king(self):
        firstgame_uuid, token = self.classicSetup()

        move = 'g3f3'
        boardStr = ('____K___'
                    '________'
                    '________'
                    '__p_____'
                    '________'
                    '____pk__'
                    '___P_pp_'
                    '________')

        self.addCustomGameSnap(self.db, boardStr, move)

        square = 'f3'

        response = self.client.get(
            f'/games/{firstgame_uuid}/moves/{square}',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        print("response: {}".format(response.json()))
        self.assertEqual(response.status_code, 200)

        self.assertListEqual(
            response.json(),
            ['e4', 'f4', 'g4', 'g3', 'e2'],
        )

    def test__possibleMoves__pawn_enpassant_black(self):
        firstgame_uuid, _ = self.classicSetup()

        token = self.getToken("janedoe")

        move = 'c2c4'
        boardStr = ('____K___'
                    '________'
                    '________'
                    '________'
                    '__pP____'
                    '____pk__'
                    '_____pp_'
                    '________')

        self.addCustomGameSnap(self.db, boardStr, move)

        square = 'd4'

        response = self.client.get(
            f'/games/{firstgame_uuid}/moves/{square}',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        print("response: {}".format(response.json()))
        self.assertEqual(response.status_code, 200)

        self.assertListEqual(
            response.json(),
            ['c3', 'd3', 'e3'],
        )

    def test__possibleMoves__pawn_enpassant_white(self):
        firstgame_uuid, token = self.classicSetup()

        move = 'd7d5'
        boardStr = ('____K___'
                    '________'
                    '________'
                    '__pP____'
                    '________'
                    '____pk__'
                    '_____pp_'
                    '________')

        self.addCustomGameSnap(self.db, boardStr, move)

        square = 'c5'

        response = self.client.get(
            f'/games/{firstgame_uuid}/moves/{square}',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        print("response: {}".format(response.json()))
        self.assertEqual(response.status_code, 200)

        self.assertListEqual(
            response.json(),
            ['c6', 'd6'],
        )

    def test__possibleMoves__pawn_impossible_enpassant_black(self):
        firstgame_uuid, _ = self.classicSetup()

        token = self.getToken("janedoe")

        move = 'c7c5'
        boardStr = ('____K___'
                    '________'
                    '________'
                    '__pP____'
                    '________'
                    '____pk__'
                    '_____pp_'
                    '________')

        self.addCustomGameSnap(self.db, boardStr, move)

        square = 'd5'

        response = self.client.get(
            f'/games/{firstgame_uuid}/moves/{square}',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        print("response: {}".format(response.json()))
        self.assertEqual(response.status_code, 200)

        self.assertListEqual(
            response.json(),
            ['d4'],
        )

    def test__possibleMoves__pawn_take(self):
        firstgame_uuid, token = self.classicSetup()

        move = 'f5f6'
        boardStr = ('____K___'
                    '_____PP_'
                    '_____p__'
                    '________'
                    '________'
                    '_____k__'
                    '_____pp_'
                    '________')

        self.addCustomGameSnap(self.db, boardStr, move)

        square = 'f6'

        response = self.client.get(
            f'/games/{firstgame_uuid}/moves/{square}',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        print("response: {}".format(response.json()))
        self.assertEqual(response.status_code, 200)

        self.assertListEqual(
            response.json(),
            ['g7'],
        )

    def send_move(self, game_uuid, move, token):
        response = self.client.post(
            f'/games/{game_uuid}/move',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
            json={
                "move": move,
            },
        )
        return response

    def prettyBoard(self, boardStr):
        print('    abcdefgh')
        print('    01234567')
        for i in range(8):
            print('{} - {} - {}'.format(i, boardStr[8 * i:8 * i + 8], 8 - i))

    def test__move__filtered_pawn(self):
        _, _ = self.addFakeUsers(self.db)
        #change to second player
        jane_token = self.getToken("janedoe")
        john_token = self.getToken("johndoe")
        self.addFakeGames(self.db, self.fakegamesdb())
        firstgame_uuid = list(self.fakegamesdb().values())[0]["uuid"]
        self.addFakeGameSnaps(self.db, self.fakegamesnapsdb())

        tokens = [jane_token, john_token]
        moves = ['e7e5', 'd4e5', 'h7h6', 'e5e6']

        response = self.send_move(firstgame_uuid, moves[0], tokens[0 % 2])
        print(response.json())
        self.prettyBoard(response.json()['board'])
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json()['board'],
            ('RNBQKBNR'
             'PPPP_PPP'
             '________'
             '____P___'
             '___p____'
             '________'
             'XXX_XXXX'
             'XXXXXXXX'),
        )

        response = self.send_move(firstgame_uuid, moves[1], tokens[1 % 2])
        print(response.json())
        self.prettyBoard(response.json()['board'])
        self.assertEqual(response.status_code, 200)

        response = self.send_move(firstgame_uuid, moves[2], tokens[2 % 2])
        print(response.json())
        self.prettyBoard(response.json()['board'])
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json()['board'],
            ('RNBQKBNR'
             'PPPP_PP_'
             '_______P'
             '____X___'
             '________'
             '________'
             'XXX_XXXX'
             'XXXXXXXX'),
        )

    # use this method as reference to reproduce any game moves
    # TODO use a virgin game instead of the firstgame_uuid
    def test__move__fogTest(self):
        _, _ = self.addFakeUsers(self.db)
        #change to second player
        jane_token = self.getToken("janedoe")
        john_token = self.getToken("johndoe")
        self.addFakeGames(self.db, self.fakegamesdb())
        firstgame_uuid = list(self.fakegamesdb().values())[0]["uuid"]
        self.addFakeGameSnaps(self.db, self.fakegamesnapsdb())

        tokens = [jane_token, john_token]
        moves = ['e7e6', 'g2g4', 'd8h4', 'f2f4', 'a7a6']

        print(tokens)

        for i, move in enumerate(moves):
            print("move {} for {}".format(move, tokens[i % 2]))
            response = self.send_move(firstgame_uuid, move, tokens[i % 2])
            print(response.json())
            self.assertEqual(response.status_code, 200)
            self.prettyBoard(response.json()['board'])

        self.assertEqual(
            response.json()['board'],
            ('RNB_KBNR'
             '_PPP_PPP'
             'P___P___'
             '________'
             '___X_XpQ'
             '________'
             'XXX_X__X'
             'XXXXXXXX'),
        )

    def test__integrationTest__foolscheckmate(self):

        # create johndoe
        # create janedoe

        response = self.client.post(
            "/users/",
            json={
                "username": "johndoe",
                "full_name": "John Le Dow",
                "email": "john@doe.cat",
                "plain_password": "secret"
            },
        )

        john_id = response.json()['id']

        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/users/",
            json={
                "username": "janedoe",
                "full_name": "Jane Le Dow",
                "email": "jane@doe.cat",
                "plain_password": "secret"
            },
        )

        jane_id = response.json()['id']

        self.assertEqual(response.status_code, 200)

        # authenticate
        response = self.client.post(
            "/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "username": "johndoe",
                "password": "secret",
            },
        )

        self.assertEqual(response.status_code, 200)
        john_token = response.json()['access_token']

        response = self.client.post(
            "/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "username": "janedoe",
                "password": "secret",
            },
        )

        self.assertEqual(response.status_code, 200)
        jane_token = response.json()['access_token']

        # john create game

        response = self.client.post(
            '/games/',
            headers={
                'Authorization': 'Bearer ' + john_token,
                'Content-Type': 'application/json',
            },
            json={
                'public': False,
                'color': 'white',
            },
        )

        self.assertEqual(response.status_code, 200)

        game_uuid = response.json()['uuid']

        # john already joined and jane joins game

        # check if game started
        response = self.client.get(
            f'/games/{game_uuid}',
            headers={
                'Authorization': 'Bearer ' + jane_token,
                'Content-Type': 'application/json',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], GameStatus.WAITING)

        white_id = response.json()['white_id']
        black_id = response.json()['black_id']
        jane_color = None if not white_id else 'white' if white_id == jane_id else 'black'
        john_color = None if not white_id else 'white' if response.json(
        )['white_id'] == john_id else 'black'

        print(f'jane color is {jane_color}')

        response = self.client.get(
            f'/games/{game_uuid}/join',
            headers={
                'Authorization': 'Bearer ' + jane_token,
                'Content-Type': 'application/json',
            },
        )

        self.assertEqual(response.status_code, 200)

        print(response.json())

        # john send move
        # jane send move

        moves = ['f2f3', 'e7e5', 'g2g4', 'd8h4', 'f3f4', 'h4e1']

        boards = [
            ('xxxxxxxxxxxxxxxx_____________________________p__ppppp_pprnbqkbnr',
             'RNBQKBNRPPPPPPPP_____________________________X__XXXXX_XXXXXXXXXX'),
            ('xxxxxxxxxxxx_xxx____________x________________p__ppppp_pprnbqkbnr',
             'RNBQKBNRPPPP_PPP____________P________________X__XXXXX_XXXXXXXXXX'),
            ('xxxxxxxxxxxx_xxx____________x_________p______p__ppppp__prnbqkbnr',
             'RNBQKBNRPPPP_PPP____________P_________X______X__XXXXX__XXXXXXXXX'),
            ('xxx_xxxxxxxx_xxx____________x_________pQ_____p__ppppp__prnbqkbnr',
             'RNB_KBNRPPPP_PPP____________P_________pQ_____X__XXXXX__XXXXXXXXX'),
            ('xxx_xxxxxxxx_xxx____________P________ppQ________ppppp__prnbqkbnr',
             'RNB_KBNRPPPP_PPP____________P________ppQ________XXXXX__XXXXXXXXX'),
            ('xxx_xxxxxxxx_xxx____________P________ppQ_____p__ppppp__prnbqkbnr',
             'RNB_KBNRPPPP_PPP____________P________pX______X__pppXX__XXXXqQbXX'),
        ]

        tokens = [john_token, jane_token]

        for i, move in enumerate(moves):
            response = self.send_move(game_uuid, move, tokens[i % 2])
            print(f'ran move {move} by {jane_color if jane_token == tokens[i%2] else john_color}')
            self.assertEqual(response.status_code, 200)

            # they ask for game and turn

            response = self.client.get(
                f'/games/{game_uuid}/turn',
                headers={
                    'Authorization': 'Bearer ' + jane_token,
                    'Content-Type': 'application/json',
                },
            )

            self.assertEqual(response.status_code, 200)
            jane_turn = response.json()
            response = self.client.get(
                f'/games/{game_uuid}/turn',
                headers={
                    'Authorization': 'Bearer ' + john_token,
                    'Content-Type': 'application/json',
                },
            )

            self.assertEqual(response.status_code, 200)
            john_turn = response.json()

            # TODO what happens after checkmate?
            self.assertEqual(jane_turn, john_turn)

            response = self.client.get(
                f'/games/{game_uuid}/snap',
                headers={
                    'Authorization': 'Bearer ' + jane_token,
                    'Content-Type': 'application/json',
                },
            )

            print(self.prettyBoard(response.json()['board']))

            # no winner
            if john_turn or jane_turn:
                #TODO note that this assert will fail if an enemy piece is seen
                if jane_color == 'white':
                    self.assertEqual(response.json()['board'], boards[i][0])
                else:
                    self.assertEqual(response.json()['board'], boards[i][1])

            response = self.client.get(
                f'/games/{game_uuid}/snap',
                headers={
                    'Authorization': 'Bearer ' + john_token,
                    'Content-Type': 'application/json',
                },
            )

            if john_turn or jane_turn:
                if john_color == 'white':
                    self.assertEqual(response.json()['board'], boards[i][0])
                else:
                    self.assertEqual(response.json()['board'], boards[i][1])

        # checkmate

        response = self.client.get(
            f'/games/{game_uuid}',
            headers={
                'Authorization': 'Bearer ' + jane_token,
                'Content-Type': 'application/json',
            },
        )

        print("{} with {} won the game".format(
            "janedoe" if jane_color == response.json()['winner'] else "johndoe", jane_color))

        self.assertEqual(response.json()['winner'], 'black')
