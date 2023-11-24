import json
import unittest
import unittest.mock as mock
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from battlechess.server import crud, models
from battlechess.server.btchApi import app, get_db
from battlechess.server.btchApiDB import Base
from battlechess.server.schemas import GameStatus
from battlechess.server.utils import get_password_hash


class Test_Api_Autoplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

        cls.engine = create_engine(
            SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
        )

        cls.TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=cls.engine
        )

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
            },
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
            }
        }
        return fake_games_db

    def fakegamesnapsdb(self):
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
            }
        ]
        return fake_games_snaps

    def addFakeUsers(self, db):
        for username, user in self.fakeusersdb().items():
            db_user = models.User(
                username=user["username"],
                full_name=user["full_name"],
                email=user["email"],
                hashed_password=user["hashed_password"],
            )
            db.add(db_user)
            db.commit()
        firstusername, _ = self.fakeusersdb().keys()
        return self.getToken(firstusername), firstusername

    def addFakeGames(self, db, fakegamesdb):
        for uuid, game in fakegamesdb.items():
            owner = (
                db.query(models.User)
                .filter(models.User.username == game["owner"])
                .first()
            )
            white = (
                db.query(models.User)
                .filter(models.User.username == game["white"])
                .first()
            )
            black = (
                db.query(models.User)
                .filter(models.User.username == game["black"])
                .first()
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

    def getToken(self, username):
        return crud.create_access_token(
            data={"sub": username}, expires_delta=timedelta(minutes=3000)
        )

    def test__version(self):
        response = self.client.get("/version")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"version": "1.0"})

    def send_move(self, game_uuid, move, token):
        response = self.client.post(
            f"/games/{game_uuid}/move",
            headers={
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json",
            },
            json={
                "move": move,
            },
        )
        return response

    def prettyBoard(self, boardStr):
        print("    abcdefgh")
        print("    01234567")
        for i in range(8):
            print("{} - {} - {}".format(i, boardStr[8 * i : 8 * i + 8], 8 - i))

    def resetGame(self, db, uuid):
        game = db.query(models.Game).filter(models.Game.uuid == uuid).first()
        game.reset()
        db.commit()

    def test__move__MrExonGame__OneGame__EnPassant(self):
        _, _ = self.addFakeUsers(self.db)
        jane_token = self.getToken("janedoe")
        john_token = self.getToken("johndoe")
        self.addFakeGames(self.db, self.fakegamesdb())
        firstgame_uuid = list(self.fakegamesdb().values())[0]["uuid"]
        self.addFakeGameSnaps(self.db, self.fakegamesnapsdb())

        tokens = [jane_token, john_token]

        # read games
        # for game in games:
        # for moves in game['moves']
        with open("ia/algebraic2icu/icu/mrexongames.txt") as json_file:
            data = json.load(json_file)
            moves = data["https://lichess.org/auXLYNj1"]
            for i, move in enumerate(moves):
                response = self.send_move(firstgame_uuid, move, tokens[i % 2])

                if response.status_code == 200:
                    self.prettyBoard(response.json()["board"])
                else:
                    print(response.json())
                self.assertEqual(response.status_code, 200)

    def test__move__MrExonGame__Enpassant2(self):
        _, _ = self.addFakeUsers(self.db)
        jane_token = self.getToken("janedoe")
        john_token = self.getToken("johndoe")
        self.addFakeGames(self.db, self.fakegamesdb())
        firstgame_uuid = list(self.fakegamesdb().values())[0]["uuid"]
        self.addFakeGameSnaps(self.db, self.fakegamesnapsdb())

        tokens = [jane_token, john_token]

        # read games
        # for game in games:
        # for moves in game['moves']
        with open("ia/algebraic2icu/icu/mrexongames.txt") as json_file:
            data = json.load(json_file)
            moves = data["https://lichess.org/X1Nk72xr"]
            for i, move in enumerate(moves):
                response = self.send_move(firstgame_uuid, move, tokens[i % 2])

                if response.status_code == 200:
                    self.prettyBoard(response.json()["board"])
                else:
                    print(response.json())
                self.assertEqual(response.status_code, 200)

    @unittest.skip("Extremely slow test. Run with -s option.")
    def test__move__MrExonGames(self):
        _, _ = self.addFakeUsers(self.db)
        jane_token = self.getToken("janedoe")
        john_token = self.getToken("johndoe")
        self.addFakeGames(self.db, self.fakegamesdb())
        firstgame_uuid = list(self.fakegamesdb().values())[0]["uuid"]
        self.addFakeGameSnaps(self.db, self.fakegamesnapsdb())

        tokens = [jane_token, john_token]

        # read games
        # for game in games:
        # for moves in game['moves']
        with open("ia/algebraic2icu/icu/mrexongames.txt") as json_file:
            data = json.load(json_file)
            for game, moves in data.items():
                print("Game: {} moves {}".format(game, moves))
                for move in moves:
                    response = self.send_move(firstgame_uuid, move, tokens[0 % 2])

                    if response.status_code == 200:
                        self.prettyBoard(response.json()["board"])
                    else:
                        print(response.json())
                    self.assertEqual(response.status_code, 200)

                self.resetGame(self.db, firstgame_uuid)
