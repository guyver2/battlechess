import random
import string
import bcrypt

from battlechess.server.config import HANDLEBASEURL

def verify_password(plain_password, hashed_password):
    # hash driectly from db is bytes, but json is str
    if type(hashed_password) is str:
        hashed_password = bytes(hashed_password.encode('utf-8'))

    password_byte_enc = plain_password.encode('utf-8')
    return bcrypt.checkpw(password=password_byte_enc, hashed_password=hashed_password)


def get_password_hash(password):
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password


# TODO use Random-Word or something for more user-friendly handles
def get_random_string(length=6):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str


def handle2uuid(uuid):
    return HANDLEBASEURL + uuid


def defaultBoard():
    return (
        "RNBQKBNR"
        "PPPPPPPP"
        "________"
        "________"
        "________"
        "________"
        "pppppppp"
        "rnbqkbnr"
    )


def extij2ad(i, j):
    square = chr(j - 2 + 97) + str(8 - (i - 2))
    return square


def ad2extij(square):
    i = 8 - int(square[1]) + 2
    j = ord(square[0]) - ord("a") + 2
    return (i, j)


def ad2ij(square):
    i = 8 - int(square[1])
    j = ord(square[0]) - ord("a")
    return (i, j)
