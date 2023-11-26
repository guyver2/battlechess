# to get a string like this run:
# openssl rand -hex 32

from decouple import config

SECRET_KEY = config("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 3000
HANDLEBASEURL = "https://bt.ch/"
