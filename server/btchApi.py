from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Set

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    },
    "janedoe": {
        "username": "janedoe",
        "full_name": "Jane Doe",
        "email": "janedoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}

fake_games_db = {
    "lkml4a3.d3": {
        "handle": "lkml4a3.d3",
        "white": "johndoe",
        "black": "janedoe",
        "status": "idle", # idle, running, completed
        "create_time": datetime(2021,1,1,tzinfo=timezone.utc),
    }
}

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

class Game(BaseModel):
    handle: str
    white: str
    black: str
    status: str
    create_time: Optional[datetime] = None

class Move(BaseModel):
    origin: Tuple[int, int]
    destination: Tuple[int, int]
    color: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

def set_fake_db(fake_db):
    global fake_users_db
    print(fake_users_db)
    fake_users_db = fake_db.copy()
    print(fake_users_db)
    print(fake_db)

def get_fake_db():
    return fake_users_db

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def add_user(db, user: UserInDB):
    fake_users_db[user.username] = {
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "hashed_password": user.hashed_password,
        "disabled": False,
    }

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_game():
    # TODO generate links
    return "https://bt.ch/lkml4a3.d3"

def get_game(gameUUID):
    game_exception = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Could not find game",
    )
    if gameUUID not in fake_games_db:
        raise game_exception
    return Game(**fake_games_db[gameUUID])

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_active_game(gameUUID, current_user: User = Depends(get_current_active_user)):
    game = get_game(gameUUID)


@app.get("/version")
async def version():
    return {'version': "1.0"}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.get("/users/me/games/")
async def read_own_games(current_user: User = Depends(get_current_active_user)):
    return [Game(**game) for gameName, game in fake_games_db.items() if game['white'] == current_user.username or game['black'] == current_user.username]

@app.get("/users/")
async def get_users(current_user: User = Depends(get_current_active_user)):
    return list(fake_users_db.keys())

@app.post("/users/")
async def create_user(new_user: UserInDB):
    user = get_user(fake_users_db, new_user.username)
    user_exists_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="username taken",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if user:
        raise user_exists_exception
    else:
        add_user(fake_users_db, new_user)
        return get_user(fake_users_db, new_user.username)

@app.get("/games/")
async def get_new_game(current_user: User = Depends(get_current_active_user)):
    handle = create_game()
    return {"game_handle": handle}

@app.get("/games/{gameUUID}")
async def get_game_by_handle(gameUUID: str, current_user: User = Depends(get_current_active_user)):
    game = get_active_game(gameUUID, current_user)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="game not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return game
    
@app.post("/games/{gameUUID}/move")
async def post_move(gameUUID: str, current_user: User = Depends(get_current_active_user), current_game: Game = Depends(get_active_game)):
    game = get_active_game(gameUUID, current_user)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="game not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return game
    
