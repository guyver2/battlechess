import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from jose import JWTError, jwt

from .btchApi import app, get_db

from .btchApiDB import SessionLocal, Base
from . import crud, models
from .utils import get_password_hash

from fastapi.testclient import TestClient


class Test_Api(unittest.TestCase):

    def override_get_db(self):
        try:
            db = self.TestingSessionLocal()
            yield db
        finally:
            db.close()


    def fakedb(self):        
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
        return fake_users_db

    def setUp(self):
        # create db, users, games...
        # set_fake_db(self.fakedb())
        
        SQLALCHEMY_DATABASE_URL = 'sqlite:///:memory:'
        # SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

        engine = create_engine(
            SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
        )
        self.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        Base.metadata.create_all(bind=engine)

        app.dependency_overrides[get_db] = self.override_get_db
        
        self.client = TestClient(app)
    
    def tearDown(self):
        # delete db
        # set_fake_db(self.fakedb())
        pass

    def test__version(self):
        response = self.client.get("/version")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"version": "1.0"})

    def test__createUser(self):
        hashed_password = get_password_hash("secret")
        response = self.client.post(
            "/users/",
            json={
                "username": "alice", 
                "full_name": "Alice la Suisse",
                "email": "alice@lasuisse.ch", 
                "hashed_password": hashed_password
            },
        )

        print(response.json())

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json())
        self.assertDictEqual(response.json(), {
            "username": "alice",
            "full_name": "Alice la Suisse",
            "email": "alice@lasuisse.ch",
            "id": 1,
            "hashed_password": hashed_password,
            "is_active": True
        })

    def test__getUsers__unauthorized(self):
        response = self.client.get("/users/")
        self.assertEqual(response.status_code, 401)

    def test__authenticate(self):
        hashed_password = get_password_hash("secret")
        response = self.client.post(
            "/users/",
            json={
                "username": "alice", 
                "full_name": "Alice la Suisse", 
                "email": "alice@lasuisse.ch", 
                "hashed_password": hashed_password,
            },
        )

        response = self.client.post(
            "/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "username": "alice", 
                "password": "secret",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertListEqual(list(response.json().keys()), ['access_token', 'token_type'])

    def test__createUser__persistence(self):
        hashed_password = crud.get_password_hash("secret")
        response = self.client.post(
            "/users/",
            json={
                "username": "alice", 
                "full_name": "Alice la Suisse", 
                "email": "alice@lasuisse.ch", 
                "hashed_password": hashed_password
            },
        )

        response = self.client.post(
            "/token",
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={
                "username": "alice", 
                "password": "secret",
            },
        )

        self.assertIsNotNone(response.json())
        print(response.json())
        self.assertIn('access_token', response.json())
        token = response.json()['access_token']

        response = self.client.get(
            "/users/",
            headers={"Authorization": "Bearer " + token},
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.json(), ["johndoe", "janedoe", "alice"])


    def test__joinGame(self):
        pass
