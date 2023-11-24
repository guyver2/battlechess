from fastapi import HTTPException, status
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from battlechess.core.Board import Board
from battlechess.core.btchBoard import BtchBoard

from .btchApiDB import Base
from .schemas import GameStatus
from .utils import ad2extij, ad2ij, extij2ad


class User(Base):

    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    avatar = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    status = Column(String, default="active")
    created_at = Column(DateTime)

    # games = relationship("Game", back_populates="owner", foreign_keys='Game.owner_id')
    # whites = relationship("Game", back_populates="white")
    # blacks = relationship("Game", back_populates="black")

    def is_active(self):
        return self.status == "active"


class Game(Base):

    __tablename__ = "game"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime)
    uuid = Column(String)
    owner_id = Column(Integer, ForeignKey("user.id"))
    white_id = Column(Integer, ForeignKey("user.id"))
    black_id = Column(Integer, ForeignKey("user.id"))
    status = Column(String, default=GameStatus.WAITING)
    turn = Column(String, default="white")
    last_move_time = Column(DateTime)
    public = Column(Boolean, default=True)
    winner = Column(String, default=None)

    owner = relationship("User", backref="games", foreign_keys=[owner_id])
    white = relationship("User", backref="whites", foreign_keys=[white_id])
    black = relationship("User", backref="blacks", foreign_keys=[black_id])

    # owner = relationship("User", foreign_keys=[owner_id], back_populates="games")
    # white = relationship("User", back_populates="whites", foreign_keys=[white_id])
    # black = relationship("User", back_populates="blacks", foreign_keys=[black_id])
    snaps = relationship("GameSnap", back_populates="game")

    def reset(self):
        self.turn = "white"
        self.winner = None
        firstsnap = self.snaps[0]
        self.snaps[:] = [firstsnap]

    def set_player(self, user: User):

        if self.white_id == user.id or self.black_id == user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Player is already in this game",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not self.white_id and not self.black_id:
            # TODO random
            self.white_id = user.id
        elif not self.white_id:
            self.white_id = user.id
        elif not self.black_id:
            self.black_id = user.id
        else:
            # error player already set
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Game is full",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def is_full(self):
        return self.white_id and self.black_id

    def get_player_color(self, user_id):
        if user_id == self.white_id:
            return "white"
        if user_id == self.black_id:
            return "black"
        return None

    def is_finished(self):
        return self.status == GameStatus.OVER

    def is_running(self):
        return self.status == GameStatus.STARTED

    def get_latest_snap(self):
        if not self.snaps:
            return None
        return self.snaps[-1]

    def start_game(self):
        self.status = GameStatus.STARTED

    def refresh_turn(self):
        if not self.snaps:
            print("[warning] game had no snaps. turn is white.")
            self.turn = "white"
        self.turn = self.snaps[-1].getNextTurn()

    # TODO ensure that the turn color is guaranteed to be correct to the caller user's color
    # TODO should we create the snap here instead of returning
    # the snap options and delegating to the client?
    def moveGame(self, move):
        current_snap = self.get_latest_snap()
        new_snap_options = current_snap.moveSnap(move)
        return new_snap_options


class GameSnap(Base):

    __tablename__ = "gamesnap"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime)
    game_id = Column(Integer, ForeignKey("game.id"))
    board = Column(String)
    move = Column(String)
    taken = Column(String)
    castleable = Column(String)
    move_number = Column(Integer)

    game = relationship("Game", back_populates="snaps")

    def getNextTurn(self):
        if not self.game.is_running():
            return None
        colors = ["white", "black"]
        return colors[self.move_number % 2]

    # TODO we need forfeit as an option
    # TODO does draw exist in battlechess?
    def winner(self):
        if "K" in self.taken:
            return "white"
        if "k" in self.taken:
            return "black"
        return None

    def snapOptionsFromBoard(self, board: Board, accepted_move):
        snapOptions = board.toElements()
        snapOptions["move"] = accepted_move
        return snapOptions

    # TODO handle errors
    # TODO could be static method, utils ...
    def coordListToMove(self, coords):
        abc = "abcdefgh"
        dig = "87654321"
        return abc[coords[1]] + dig[coords[0]] + abc[coords[3]] + dig[coords[2]]

    # TODO handle errors
    def moveToCoordList(self, move):
        dig = [None, 7, 6, 5, 4, 3, 2, 1, 0]
        i = dig[int(move[1])]
        j = ord(move[0]) - 97
        ii = dig[int(move[3])]
        jj = ord(move[2]) - 97
        return [i, j, ii, jj]

    def moveSnap(self, move):
        # TODO sync with board
        color = self.getNextTurn()

        snapOptions = None
        # build board from model
        coordlist = self.moveToCoordList(move)
        board = self.toBoard()
        # run move
        result, accepted_move_list, msg = board.move(
            coordlist[0],
            coordlist[1],
            coordlist[2],
            coordlist[3],
            color[0],
        )
        if not result:
            # TODO better reason
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Movement invalid because {msg}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        accepted_move = self.coordListToMove(accepted_move_list)

        return self.snapOptionsFromBoard(board, accepted_move)

    # TODO build a Board class from an instance
    def toBoard(self):
        board = Board()
        board.reset()
        enpassantColumn = self.enpassantColumn()
        enpassant = (
            chr(enpassantColumn + ord("a")) if enpassantColumn is not None else None
        )
        winner = None  # TODO better way to get for unit testing self.game.winner
        board.updateFromElements(
            self.board, self.taken, self.castleable, enpassant, winner
        )
        return board

    def toBtchBoard(self) -> BtchBoard:
        enpassantColumn = self.enpassantColumn()
        enpassant = enpassantColumn + 2 if enpassantColumn is not None else None
        return BtchBoard.factoryFromElements(
            self.board, self.taken, self.castleable, enpassant
        )

    def enpassantColumn(self):
        if not self.move:
            return None

        i, j = ad2ij(self.move[0:2])
        ii, jj = ad2ij(self.move[2:4])
        piece = self.board[ii * 8 + jj]

        if piece in ["p", "P"]:
            return j if i in [1, 6] and ii in [3, 4] else None

        return None

    # unused
    def filtered(self, color=None):
        board = self.toBoard()
        elements = board.toElements(color)
        return elements

    def getPossibleMoves(self, square, color):
        board = self.toBtchBoard()
        board.filter(color)

        # btchboard coordinates are extended [0,12]
        i, j = ad2extij(square)
        ijmoves = board.possibleMoves(color, i, j)
        return [extij2ad(i, j) for i, j in ijmoves]
