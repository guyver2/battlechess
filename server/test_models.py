import unittest

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from datetime import datetime, timedelta, timezone

from . import models
from .btchApiDB import SessionLocal, Base, BtchDBContextManager
from core.Board import Board

class Test_Models(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

        cls.engine = create_engine(
            SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
        )

        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)


    def setUp(self):
        # TODO setUp correctly with begin-rollback instead of create-drop
        # create db, users, games...

        # Base = declarative_base()

        Base.metadata.create_all(bind=self.engine)

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
                "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
                "disabled": False,
                "avatar": None,
                "created_at":  datetime(2021, 1, 1, tzinfo=timezone.utc),
            },
            "janedoe": {
                "username": "janedoe",
                "full_name": "Jane Doe",
                "email": "janedoe@example.com",
                "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
                "disabled": False,
                "avatar": None,
                "created_at":  datetime(2021, 1, 1, tzinfo=timezone.utc),
            }
        }
        return fake_users_db

    def fakesnap(self):
        snap = {
            "game_uuid": "lkml4a3.d3",
            "move": "",
            "board": (
                'RNBQKBNR'
                'PPPPPPPP'
                '________'
                '________'
                '________'
                '________'
                'pppppppp'
                'rnbqkbnr'
            ),
            "taken": "",
            "castelable": sorted("LSKlsk"),
            "move_number": 0,
            "created_at": datetime(2021, 4, 5, 0, tzinfo=timezone.utc),
        }
        return snap

    def fakegame(self):
        fake_game_db = {
            "uuid": "lkml4a3.d3",
            "owner": "johndoe",
            "white": "johndoe",
            "black": "janedoe",
            "status": "started",
            "public": False,
            "turn": "black",
            "created_at": datetime(2021, 1, 1, tzinfo=timezone.utc),
        }
        return fake_game_db

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
        return db.query(models.User).all()

    def test__toBoard(self):

        self.maxDiff=None
        snap = self.fakesnap()
        db_snap = models.GameSnap(
            created_at=snap["created_at"],
            game_id=None,
            board=snap["board"],
            move=snap["move"],
            taken=snap["taken"],
            castelable=snap["castelable"],
            move_number=snap["move_number"],
        )

        board = db_snap.toBoard()

        self.assertEqual(board.toString(), (
            "rb_nb_bb_qb_kb_bb_nb_rb_"
            "pb_pb_pb_pb_pb_pb_pb_pb_"
            "________"
            "________"
            "________"
            "________"
            "pw_pw_pw_pw_pw_pw_pw_pw_"
            "rw_nw_bw_qw_kw_bw_nw_rw"
            "##kb_kw_rkb_rkw_rqb_rqw#-1#n"
            )
        )

    def test__Board__move(self):

        self.maxDiff=None
        board = Board()
        board.reset()
        status, accepted_move_list, msg = board.move(6,4,4,4)
        print(f"new board {status} - {accepted_move_list} - {msg}")
        print(board.toString())
        self.assertTrue(status)
        self.assertListEqual(accepted_move_list, [6,4,4,4])
        self.assertEqual(board.toString(), (
            "rb_nb_bb_qb_kb_bb_nb_rb_"
            "pb_pb_pb_pb_pb_pb_pb_pb_"
            "________"
            "________"
            "____pw____"
            "________"
            "pw_pw_pw_pw__pw_pw_pw_"
            "rw_nw_bw_qw_kw_bw_nw_rw"
            "##kb_kw_rkb_rkw_rqb_rqw#4#n"
            )
        )

    def test__GameSnap__coordListToMove(self):

        fakesnap = self.fakesnap()
        snap = models.GameSnap(
            created_at=fakesnap["created_at"],
            game_id=None,
            board=fakesnap["board"],
            move=fakesnap["move"],
            taken=fakesnap["taken"],
            castelable=fakesnap["castelable"],
            move_number=fakesnap["move_number"],
        )

        move = snap.coordListToMove([6,3,4,3])
        print(f'move {move}')
        self.assertEqual(move,"d2d4")

    def test__GameSnap__moveToCoordList(self):

        fakesnap = self.fakesnap()
        snap = models.GameSnap(
            created_at=fakesnap["created_at"],
            game_id=None,
            board=fakesnap["board"],
            move=fakesnap["move"],
            taken=fakesnap["taken"],
            castelable=fakesnap["castelable"],
            move_number=fakesnap["move_number"],
        )

        move = snap.moveToCoordList("d2d4")

        self.assertEqual(move,[6,3,4,3])

    # deprecated: default snap is created via api set_player
    def _test__Game__startGameCreatesSnapIfEmpty(self):
        users = self.addFakeUsers(self.db)
        johndoe = users[0]
        janedoe = users[1]
        game = self.fakegame()
        db_game = models.Game(
                created_at=game["created_at"],
                uuid=game["uuid"],
                owner_id=johndoe.id,
                white_id=johndoe.id,
                black_id=janedoe.id,
                status=game["status"],
                last_move_time=None,
                turn=game.get("turn", "white"),
                public=game["public"]
        )
        self.db.add(db_game)
        self.db.commit()
        self.db.refresh(db_game)

        db_game.start_game()

        snaps = db_game.snaps
        self.assertTrue(len(snaps) > 0)