from typing import List, Optional, Tuple
from datetime import datetime, time, timedelta
# from uuid import UUID # represented as string
from pydantic import BaseModel


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
    castelable: str
    move_number: int

    def extendboard(self, board):
        return "_"*10 + "".join(["_" + board[j*8:(j+1)*8] + "_" for j in range(8)]) + "_"*10

    def shrinkboard(self, extboard, inner=True):
        if not inner:
            return "".join([extboard[j*10+1:(j+1)*10-1] for j in range(1,9)])
        else:
            return "".join([extboard[j*10+1:(j+1)*10-1] for j in range(8)])


    def hasEnemy(self, extboard, j, i):
        # i+1 because coordinates are board coordinates not extended board coords
        # hence, start after the first '_' of each row
        i = i+1
        c = extboard[j*10+i]
        # print(f"{j} {i} {c} {extboard}")
        for j2 in [j-1, j, j+1]:
            for i2 in [i-1, i, i+1]:
                c2 = extboard[j2*10+i2]
                if c2 == '_':
                    continue
                elif c.isupper() and c2.islower():
                    return True
                elif c.islower() and c2.isupper():
                    return True

    def filterchar(self, color, c, extboard, j, i):
        if color == 'black':
            return c if c == '_' or c.isupper() or self.hasEnemy(extboard, j, i) else 'X'
        elif color == 'white':
            return c if c == '_' or c.islower() or self.hasEnemy(extboard, j, i) else 'x'
        else:
            print(f"{color} is not a color")
            return None

    def filterBoard(self, color):
        # extend the board to skip doing bound checking
        extboard = self.extendboard(self.board)

        #[(i,j,c) for j in range(1,9) for i,c in enumerate(foo[j*10+1:j*10+9])]

        blist = [ self.filterchar(color, c, extboard, j, i) for j in range(8) for i,c in enumerate(extboard[(j+1)*10+1:(j+1)*10+9])]

        fboard = "".join(blist)

        return fboard

    def prepare_for_player(self, player_color: str):

        #foreach enemy piece, check if theres a friendly piece around, delete if not

        # filteredSnap = self.copy() # TODO no need to copy, schema objects don't modify the db

        #remove other player board
        self.board = self.filterBoard(player_color)
        print(f"filtered board is {self.board}")

        if player_color == 'black':
            self.castelable = ''.join(c for c in self.castelable if c.isupper())
            self.move = self.move if not self.move_number%2 else None
        elif player_color == 'white':
            self.castelable = ''.join(c for c in self.castelable if c.islower())
            self.move = self.move if self.move_number%2 else None


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


class Game(GameBase):
    id: int
    uuid: str
    created_at: Optional[datetime] = None
    last_move_time: Optional[datetime] = None
    owner_id: int
    white_id: Optional[int] = None
    black_id: Optional[int] = None
    status: str
    turn: str
    snaps: List[GameSnap] = []
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


class UserCreate(UserBase):
    plain_password: str


class User(UserBase):
    id: int
    status: str
    games: List[Game] = []
    whites: List[Game] = []
    blacks: List[Game] = []

    class Config:
        orm_mode = True