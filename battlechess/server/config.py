# to get a string like this run:
# openssl rand -hex 32

from decouple import config

SECRET_KEY = config("SECRET_KEY", default="e909bb995546a0378161ed18d4e44ab4525d735e07a52cec2eb9b3a86d39ee61")
ALGORITHM = config("ALGORITHM", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=3000, cast=int)
HANDLEBASEURL = config("HANDLEBASEURL", default="https://bt.ch/")
SQLALCHEMY_DATABASE_URL = config("SQLALCHEMY_DATABASE_URL", default="sqlite:///./btchdb.sqlite")

