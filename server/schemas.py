from typing import List, Optional, Tuple
from datetime import datetime, time, timedelta
# from uuid import UUID # represented as string
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class GameSnap(BaseModel):
    time_delta: Optional[int] = None
    snap: str

class GameBase(BaseModel):
    handle: str

class GameCreate(GameBase):
    pass

class Game(GameBase):
    id: int
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
    disabled: Optional[bool] = None
    email: Optional[str] = None

class UserCreate(UserBase):
    hashed_password: str

class User(UserBase):
    id: int
    is_active: bool
    games: List[Game] = []
    whites: List[Game] = []
    blacks: List[Game] = []

    class Config:
        orm_mode = True