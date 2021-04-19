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
    board: str
    taken: str
    castelable: List[str]
    move_number: int

    def prepare_for_player(self, player_color: str):
        #remove other player board
        # TODO this removes everything, but pieces next to mine should be kept
        if player_color == 'black':
            self.board = ''.join(ch if not ch.isupper() else '_' for ch in self.board)
            self.castelable = [castle for castle in self.castelable if castle.isupper()]
        elif player_color == 'white':
            self.board = ''.join(ch if not ch.islower() else '_' for ch in self.board)
            self.castelable = [castle for castle in self.castelable if castle.isupper()]

        #remove other player castelable
        self.castelable = self.castelable

    class Config:
        orm_mode = True

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
    create_time: Optional[datetime] = None
    owner_id: int
    white_id: Optional[int] = None
    black_id: Optional[int] = None
    status: str
    snaps: List[GameSnap] = []

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
    hashed_password: str

class User(UserBase):
    id: int
    status: str
    games: List[Game] = []
    whites: List[Game] = []
    blacks: List[Game] = []

    class Config:
        orm_mode = True