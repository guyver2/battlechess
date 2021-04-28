import unittest
import unittest.mock as mock
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from jose import JWTError, jwt

from fastapi.testclient import TestClient
from fastapi import HTTPException, status

from .btchApi import app, get_db

from .btchApiDB import SessionLocal, Base, BtchDBContextManager
from . import crud, models
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

        cls.engine = create_engine(SQLALCHEMY_DATABASE_URL,
                                   connect_args={"check_same_thread": False})

        cls.TestingSessionLocal = sessionmaker(autocommit=False,
                                               autoflush=False,
                                               bind=cls.engine)

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
                "status": "started",
                "public": False,
                "turn": "black",
                "created_at": datetime(2021, 1, 1, tzinfo=timezone.utc),
            },
            "da39a3ee5e": {
                "uuid": "da39a3ee5e",
                "owner": "janedoe",
                "white": "johndoe",
                "black": "janedoe",
                "status": "ended",
                "public": False,
                "winner": "johndoe",
                "created_at": datetime(2021, 3, 12, tzinfo=timezone.utc),
            },
            "da40a3ee5e": {
                "uuid": "da39a3ee5e",
                "owner": "janedoe",
                "white": None,
                "black": "janedoe",
                "status": "waiting",
                "public": True,
                "winner": None,
                "created_at": datetime(2021, 3, 12, tzinfo=timezone.utc),
            },
            "123fr12339": {
                "uuid": "123fr12339",
                "owner": "janedoe",
                "white": "janedoe",
                "black": None,
                "status": "waiting",
                "public": True,
                "created_at": datetime(2021, 4, 5, tzinfo=timezone.utc),
            },
            "d3255bfef9": {
                "uuid": "d3255bfef9",
                "owner": "johndoe",
                "white": "johndoe",
                "black": None,
                "status": "waiting",
                "public": False,
                "created_at": datetime(2021, 4, 5, tzinfo=timezone.utc),
            }
        }
        return fake_games_db

    def fakegamesnapsdb(self):
        fake_games_snaps = [
            {
                "game_uuid":
                "lkml4a3.d3",
                "move":
                "",
                "board": ('RNBQKBNR'
                          'PPPPPPPP'
                          '________'
                          '________'
                          '________'
                          '________'
                          'pppppppp'
                          'rnbqkbnr'),
                "taken":
                "",
                "castelable":
                "",
                "move_number":
                0,
                "created_at":
                datetime(2021, 4, 5, 0, tzinfo=timezone.utc),
            },
            {
                "game_uuid":
                "lkml4a3.d3",
                "move":
                "d2d4",
                "board": ('RNBQKBNR'
                          'PPPPPPPP'
                          '________'
                          '________'
                          '___p____'
                          '________'
                          'ppp_pppp'
                          'rnbqkbnr'),
                "taken":
                "",
                "castelable":
                "",
                "move_number":
                1,
                "created_at":
                datetime(2021, 4, 5, 10, tzinfo=timezone.utc),
            },
        ]
        return fake_games_snaps

    def addFakeUsers(self, db):
        for username, user in self.fakeusersdb().items():
            db_user = models.User(username=user["username"],
                                  full_name=user["full_name"],
                                  email=user["email"],
                                  hashed_password=user["hashed_password"])
            db.add(db_user)
            db.commit()
        firstusername, _ = self.fakeusersdb().keys()
        return self.getToken(firstusername), firstusername

    def addFakeGames(self, db, fakegamesdb):
        for uuid, game in fakegamesdb.items():
            owner = db.query(models.User).filter(
                models.User.username == game['owner']).first()
            white = db.query(models.User).filter(
                models.User.username == game['white']).first()
            black = db.query(models.User).filter(
                models.User.username == game['black']).first()
            db_game = models.Game(
                created_at=game["created_at"],
                uuid=game["uuid"],
                owner_id=owner.id,
                white_id=white.id if white is not None else None,
                black_id=black.id if black is not None else None,
                status=game["status"],
                last_move_time=None,
                turn=game.get("turn", "white"),
                public=game["public"])
            db.add(db_game)
            db.commit()
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
                castelable=snap["castelable"],
                move_number=snap["move_number"],
            )
            db.add(db_snap)
            db.commit()

    def getToken(self, username):
        return crud.create_access_token(data={"sub": username},
                                        expires_delta=timedelta(minutes=3000))

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
        self.assertTrue(
            verify_password("secret", response_dict["hashed_password"]))
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
        self.assertListEqual(list(response.json().keys()),
                             ['access_token', 'token_type'])

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
                'status': 'idle',
                'turn': 'white',
                'white_id': None,
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
                'status': 'waiting',
                'turn': 'white',
                'white_id': 1,
                'winner': None,
            })

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
        self.assertTrue(response.json()['white_id'] == oneUser.id
                        or response.json()['black_id'] == oneUser.id)
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
        self.assertTrue(response.json()['black_id'] == oneUser.id
                        or response.json()['white_id'] == oneUser.id)

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
            'create_time': mock.ANY,
            'owner_id': 2,
            'white_id': None,
            'black_id': 2,
            'status': 'waiting',
            'turn': 'white',
            'snaps': [],
        }, {
            'black_id': None,
            'create_time': mock.ANY,
            'uuid': mock.ANY,
            'id': 4,
            'owner_id': 2,
            'status': 'waiting',
            'turn': 'white',
            'white_id': 2,
            'snaps': [],
        }])

    def test__joinGame__playerAlreadyInGame(self):
        token, username = self.addFakeUsers(self.db)
        self.addFakeGames(self.db, self.fakegamesdb())

        uuid = self.fakegamesdb['123fr12339']

        user = crud.get_user_by_username(self.db, username)

        game_before = self.db.query(
            models.Game).filter(models.Game.uuid == uuid).first()

        response = self.client.get(
            f'/games/{uuid}/join',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        game = self.db.query(
            models.Game).filter(models.Game.uuid == uuid).first()

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
                'status': 'waiting',
                'turn': 'white',
                'white_id': game.white_id,
            })

    def test__joinGame__playerAlreadyInGame(self):
        token, username = self.addFakeUsers(self.db)
        uuid = self.addFakeGames(self.db, self.fakegamesdb())

        user = crud.get_user_by_username(self.db, username)

        game_before = self.db.query(
            models.Game).filter(models.Game.uuid == uuid).first()

        response = self.client.get(
            f'/games/{uuid}/join',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertDictEqual(response.json(),
                             {'detail': 'Player is already in this game'})

    def test__getsnap__byNum(self):
        token, _ = self.addFakeUsers(self.db)
        self.addFakeGames(self.db, self.fakegamesdb())
        firstgame_uuid = list(self.fakegamesdb().values())[0]["uuid"]
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
        self.assertDictEqual(
            response.json(), {
                'game_id':
                1,
                'created_at':
                mock.ANY,
                'id':
                1,
                'move':
                '',
                'taken':
                '',
                'castelable':
                '',
                'move_number':
                0,
                'board': ('RNBQKBNR'
                          'PPPPPPPP'
                          '________'
                          '________'
                          '________'
                          '________'
                          'pppppppp'
                          'rnbqkbnr'),
            })

    def test__getsnaps(self):
        self.maxDiff = None
        token, _ = self.addFakeUsers(self.db)
        self.addFakeGames(self.db, self.fakegamesdb())
        firstgame_uuid = list(self.fakegamesdb().values())[0]["uuid"]
        self.addFakeGameSnaps(self.db, self.fakegamesnapsdb())

        response = self.client.get(
            f'/games/{firstgame_uuid}/snaps',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.json(), [{
            'game_id':
            1,
            'created_at':
            mock.ANY,
            'id':
            1,
            'move':
            '',
            'taken':
            '',
            'castelable':
            '',
            'move_number':
            0,
            'board': ('RNBQKBNR'
                      'PPPPPPPP'
                      '________'
                      '________'
                      '________'
                      '________'
                      'pppppppp'
                      'rnbqkbnr'),
        }, {
            'game_id':
            1,
            'created_at':
            mock.ANY,
            'id':
            2,
            'move':
            'd2d4',
            'taken':
            '',
            'castelable':
            '',
            'move_number':
            1,
            'board': ('RNBQKBNR'
                      'PPPPPPPP'
                      '________'
                      '________'
                      '___p____'
                      '________'
                      'ppp_pppp'
                      'rnbqkbnr'),
        }])

    def test__getsnap__latest(self):
        token, _ = self.addFakeUsers(self.db)
        self.addFakeGames(self.db, self.fakegamesdb())
        firstgame_uuid = list(self.fakegamesdb().values())[0]["uuid"]
        self.addFakeGameSnaps(self.db, self.fakegamesnapsdb())

        response = self.client.get(
            f'/games/{firstgame_uuid}/snap',
            headers={
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
        )

        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(), {
                'game_id':
                1,
                'created_at':
                mock.ANY,
                'id':
                2,
                'move':
                'd2d4',
                'taken':
                '',
                'castelable':
                '',
                'move_number':
                1,
                'board': ('RNBQKBNR'
                          'PPPPPPPP'
                          '________'
                          '________'
                          '___p____'
                          '________'
                          'ppp_pppp'
                          'rnbqkbnr'),
            })

    def test_getTurn(self):
        token, _ = self.addFakeUsers(self.db)
        self.addFakeGames(self.db, self.fakegamesdb())
        firstgame_uuid = list(self.fakegamesdb().values())[0]["uuid"]
        self.addFakeGameSnaps(self.db, self.fakegamesnapsdb())

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

    def test_move(self):
        token, _ = self.addFakeUsers(self.db)
        self.addFakeGames(self.db, self.fakegamesdb())
        firstgame_uuid = list(self.fakegamesdb().values())[0]["uuid"]
        self.addFakeGameSnaps(self.db, self.fakegamesnapsdb())

        # get previous game/board

        game_before = self.db.query(
            models.Game).filter(models.Game.uuid == firstgame_uuid).first()

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

        game_after = self.db.query(
            models.Game).filter(models.Game.uuid == firstgame_uuid).first()

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
            },
        )

        self.assertEqual(response.status_code, 200)

        game_uuid = response.json()['uuid']

        # jane join game

        response = self.client.get(
            f'/games/{game_uuid}/join',
            headers={
                'Authorization': 'Bearer ' + john_token,
                'Content-Type': 'application/json',
            },
        )

        self.assertEqual(response.status_code, 200)

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

        tokens = [john_token, jane_token]

        for i, move in enumerate(moves):
            response = self.send_move(game_uuid, move, tokens[i % 2])
            print(f'running move {move} response {response.json()}')
            self.assertEqual(response.status_code, 200)

        # checkmate

        response = self.client.get(
            f'/games/{game_uuid}',
            headers={
                'Authorization': 'Bearer ' + jane_token,
                'Content-Type': 'application/json',
            },
        )

        self.assertEqual(response.json()['winner'], 'black')
