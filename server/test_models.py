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
            "castelable": "",
            "move_number": 0,
            "created_at": datetime(2021, 4, 5, 0, tzinfo=timezone.utc),
        }
        return snap

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
            "##kb_kw_rqb_rkb_rqw_rkw#-1#n"
            )
        )

    def test__Board__move(self):

        self.maxDiff=None
        board = Board()
        board.reset()
        status, accepted_move = board.move(1,4,3,4)
        print(f"new board {status} - {accepted_move}")
        print(board.toString())
        self.assertTrue(status)
        self.assertEqual(board.toString(), (
            "rb_nb_bb_qb_kb_bb_nb_rb_"
            "pb_pb_pb_pb__pb_pb_pb_"
            "________"
            "____pb____"
            "________"
            "________"
            "pw_pw_pw_pw_pw_pw_pw_pw_"
            "rw_nw_bw_qw_kw_bw_nw_rw"
            "##kb_kw_rqb_rkb_rqw_rkw#4#n"
            )
        )