from datetime import datetime
from typing import Optional, Tuple

# from uuid import UUID # represented as string
from pydantic import BaseModel


class GameStatus:
    WAITING = "waiting"
    STARTED = "started"
    OVER = "over"


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class GameSnapBase(BaseModel):
    pass


class GameSnap(GameSnapBase):
    id: int
    created_at: Optional[datetime] = None
    game_id: int
    move: str
    board: str
    taken: str
    castleable: str
    move_number: int

    def extendboard(self, board):
        return (
            "_" * 10
            + "".join(["_" + board[j * 8 : (j + 1) * 8] + "_" for j in range(8)])
            + "_" * 10
        )

    def shrinkboard(self, extboard, inner=True):
        if not inner:
            return "".join(
                [extboard[j * 10 + 1 : (j + 1) * 10 - 1] for j in range(1, 9)]
            )
        else:
            return "".join([extboard[j * 10 + 1 : (j + 1) * 10 - 1] for j in range(8)])

    # i,j extended board coordinates
    def hasEnemy(self, extboard, i, j):
        c = extboard[i * 10 + j]

        # print(f"{j} {i} {c} {extboard}")
        for j2 in [j - 1, j, j + 1]:
            for i2 in [i - 1, i, i + 1]:
                c2 = extboard[i2 * 10 + j2]
                if c2 == "_":
                    continue
                elif c.isupper() and c2.islower():
                    return True
                elif c.islower() and c2.isupper():
                    return True

    def filterchar(self, color, c, extboard, i, j):
        # TODO replace Xs with _ when function has been tested enough.
        if color == "black":
            return (
                c if c == "_" or c.isupper() or self.hasEnemy(extboard, i, j) else "X"
            )
        elif color == "white":
            return (
                c if c == "_" or c.islower() or self.hasEnemy(extboard, i, j) else "x"
            )
        else:
            print(f"{color} is not a color")
            return None

    def filterBoard(self, color):
        # extend the board to skip doing bound checking
        extboard = self.extendboard(self.board)

        # [(i,j,c) for j in range(1,9) for i,c in enumerate(foo[j*10+1:j*10+9])]

        # print(''.join([
        #     self.filterchar(color, extboard[i * 10 + j], extboard, i, j)
        #     for i in range(1, 9)
        #     for j in range(1, 9)
        # ]))

        blist = [
            self.filterchar(color, extboard[i * 10 + j], extboard, i, j)
            for i in range(1, 9)
            for j in range(1, 9)
        ]

        fboard = "".join(blist)

        return fboard

    def prepare_for_player(self, player_color: str):

        # foreach enemy piece, check if theres a friendly piece around, delete if not

        # filteredSnap = self.copy() # TODO no need to copy, schema objects don't modify the db

        # remove other player board
        self.board = self.filterBoard(player_color)

        if player_color == "black":
            self.castleable = "".join(c for c in self.castleable if c.isupper())
            self.move = self.move if not self.move_number % 2 else None
        elif player_color == "white":
            self.castleable = "".join(c for c in self.castleable if c.islower())
            self.move = self.move if self.move_number % 2 else None

    class Config:
        orm_mode = True


class FilteredGameSnap(GameSnap):
    class Config:
        orm_mode = False


class GameMove(BaseModel):
    move: str


# TODO this could be refactored to a more on-pair with snap
# currently unused in favor of GameMove
class GameSnapCreate(GameSnapBase):
    game_id: int
    move: str


class GameBase(BaseModel):
    pass


class GameCreate(GameBase):
    public: bool
    color: str = ""


class Game(GameBase):
    id: int
    uuid: str
    created_at: Optional[datetime] = None
    last_move_time: Optional[datetime] = None
    owner_id: int
    white_id: Optional[int] = None
    black_id: Optional[int] = None
    status: str
    turn: Optional[str] = None
    winner: Optional[str] = None
    public: Optional[bool] = None

    class Config:
        orm_mode = True


class Move(BaseModel):
    origin: Tuple[int, int]
    destination: Tuple[int, int]
    color: str


class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None


class UserCreate(UserBase):
    plain_password: str


class User(UserBase):
    id: int
    status: str

    # games: List[Game] = []
    # whites: List[Game] = []
    # blacks: List[Game] = []

    class Config:
        orm_mode = True
