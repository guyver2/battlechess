from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from battlechess.server.config import SQLALCHEMY_DATABASE_URL

# SQLALCHEMY_DATABASE_URL = "sqlite:///./btchdb.sqlite"
# SQLALCHEMY_DATABASE_URL = 'sqlite:///:memory:' # doesn't work
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, echo=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# db session to use outside of endpoints (e.g. with BtchDBContextManager as db:)
# see https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/#using-context-managers-in-dependencies-with-yield
class BtchDBContextManager:
    def __init__(self):
        self.db = SessionLocal()

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close()
