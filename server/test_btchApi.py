import unittest

from jose import JWTError, jwt

from .btchApi import app

from fastapi.testclient import TestClient

class Test_Api(unittest.TestCase):

    def setUp(self):
        # create db, users, games...
        self.client = TestClient(app)
    
    def tearDown(self):
        # delete db
        pass

    def test__version(self):
        response = self.client.get("/version")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"version": "1.0"})

    def test__createUser(self):
        pass

    def test__login(self):
        pass