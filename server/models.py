from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship

from .btchApiDB import Base

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
    status = Column(String, default="waiting")
    turn = Column(String, default="white")
    last_move_time = Column(DateTime)
    public = Column(Boolean, default=True)

    owner = relationship("User", backref="games", foreign_keys=[owner_id])
    white = relationship("User", backref="whites", foreign_keys=[white_id])
    black = relationship("User", backref="blacks", foreign_keys=[black_id])

    # owner = relationship("User", foreign_keys=[owner_id], back_populates="games")
    # white = relationship("User", back_populates="whites", foreign_keys=[white_id])
    # black = relationship("User", back_populates="blacks", foreign_keys=[black_id])
    snaps = relationship("GameSnap", back_populates="game")

    def set_player(self, user: User):

        if not self.white_id and not self.black_id:
            # TODO random
            self.white_id = user.id
        elif not self.white_id:
            self.white_id = user.id
        elif not self.black_id:
            self.black_id = user.id
        else:
            #error player already set
            raise


class GameSnap(Base):

    __tablename__ = "gamesnaps"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime)
    serializedGame = Column(String)
    game_id = Column(Integer, ForeignKey("game.id"))
    move = Column(String)
    taken = Column(String)
    castelable = Column(String)
    move_number = Column(Integer)

    game = relationship("Game", back_populates="snaps")
