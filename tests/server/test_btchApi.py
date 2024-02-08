import sys
import time
import asyncio
import pytest
import unittest.mock as mock
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    from PIL import Image
except ImportError:
    print("PIL module is not installed. Some tests will be skipped")

from fastapi.testclient import TestClient

from battlechess.server import crud, models
from battlechess.server.btchApi import app, get_db
from battlechess.server.btchApiDB import Base
from battlechess.server.schemas import GameStatus
from battlechess.server.utils import get_password_hash, verify_password


def testDataDir():
    return Path(__file__).parent.parent / "data" / "avatars"

def getToken(username):
    return crud.create_access_token(
        data={"sub": username}, expires_delta=timedelta(minutes=3000)
    )

def test__version(client):
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == {"version": "1.0"}


def test__createUser(client):
    get_password_hash("secret")
    response = client.post(
        "/users/",
        json={
            "username": "alice",
            "full_name": "Alice la Suisse",
            "email": "alice@lasuisse.ch",
            "plain_password": "secret",
        },
    )

    print(response.json())

    assert response.status_code == 200
    assert response.json() is not None
    response_dict = response.json()
    assert verify_password("secret", response_dict["hashed_password"])
                           
    response_dict.pop("hashed_password", None)
    assert response_dict == {
        "username": "alice",
        "created_at": mock.ANY,
        "full_name": "Alice la Suisse",
        "email": "alice@lasuisse.ch",
        "id": 1,
        "avatar": None,
        "status": "active",
    }

def test__create_user__with_avatar(client):
    get_password_hash("secret")
    new_avatar = "images/avatar001.jpeg"
    response = client.post(
        "/users/",
        json={
            "username": "alice",
            "full_name": "Alice la Suisse",
            "email": "alice@lasuisse.ch",
            "avatar": new_avatar,
            "plain_password": "secret",
        },
    )

    print(response.json())

    assert response.status_code == 200
    assert response.json()["avatar"] == new_avatar


# TODO fix the put method for user
def _test__update_user__full_name(db, client, addFakeUsers):
    token, _ = addFakeUsers

    oneUser = db.query(models.User)[1]

    new_full_name = "Alicia la catalana"

    response = client.put(
        "/users/update",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
        json={
            "username": oneUser.username,
            "full_name": new_full_name,
            "email": oneUser.email,
            "avatar": oneUser.avatar,
        },
    )

    print(response.json())
    assert response.status_code == 200
    assert response.json() == {
        "username": "alice",
        "full_name": "Alice la Suisse",
        "email": "alice@lasuisse.ch",
        "avatar": new_full_name,
        "plain_password": "secret",
    }

@pytest.mark.skipif("PIL" not in sys.modules, reason="PIL module is not installed")
def test__upload_user__avatarImage(db, client, addFakeUsers):
    token, _ = addFakeUsers

    oneUser = db.query(models.User)[1]
    filename = testDataDir() / "test_avatar.jpeg"
    with open(filename, "rb") as f:
        img = Image.open(f)
        try:
            img.verify()
        except (IOError, SyntaxError):
            print("Bad file:", filename)

    # TODO reset cursor instead of reopening
    with open(filename, "rb") as f:
        response = client.put(
            f"/users/u/{oneUser.id}/avatar",
            headers={"Authorization": "Bearer " + token},
            files={"file": f},
        )

    print(response.json())
    assert response.status_code == 200

    expected_avatar_dir = Path(__file__).parent.parent / "data" / "avatars"
    expected_avatar_filepath = expected_avatar_dir / "1_avatar.jpeg"
    expected_avatar_file = Path(expected_avatar_filepath)

    # remove the test file from the config directory
    expected_avatar_file.unlink()

@pytest.mark.skipif("PIL" not in sys.modules, reason="PIL module is not installed")
def test__upload_user__avatarImage__file_too_big(db, client, addFakeUsers):
    token, _ = addFakeUsers

    oneUser = db.query(models.User)[1]

    img = Image.new(mode="RGB", size=(1000, 1000), color="red")
    response = client.put(
        f"/users/u/{oneUser.id}/avatar",
        headers={"Authorization": "Bearer " + token},
        files={"file": img.tobytes()},
    )

    print(response.json())
    assert response.status_code == 422

def test__getUsers__unauthorized(client):
    response = client.get("/users/")
    assert response.status_code == 401

def test__authenticate(client):

    # add a user
    response = client.post(
        "/users/",
        json={
            "username": "alice",
            "full_name": "Alice la Suisse",
            "email": "alice@lasuisse.ch",
            "plain_password": "secret",
        },
    )

    # test auth
    response = client.post(
        "/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "username": "alice",
            "password": "secret",
        },
    )

    assert response.status_code == 200
    assert list(response.json().keys()) == ["access_token", "token_type"]

def test__createUser__persistence(client):
    response = client.post(
        "/users/",
        json={
            "username": "alice",
            "full_name": "Alice la Suisse",
            "email": "alice@lasuisse.ch",
            "plain_password": "secret",
        },
    )

    response = client.post(
        "/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "username": "alice",
            "password": "secret",
        },
    )

    assert response.json() is not None
    print(response.json())
    assert "access_token" in response.json()
    token = response.json()["access_token"]

    response = client.get(
        "/users/usernames",
        headers={"Authorization": "Bearer " + token},
    )

    assert response.status_code == 200
    assert response.json() == ["alice"]

def test__addFakeUsers(db, addFakeUsers):
    pass

def test__getUsernames(db, client, addFakeUsers):
    token, _ = addFakeUsers

    db.query(models.User).all()

    response = client.get(
        "/users/usernames",
        headers={"Authorization": "Bearer " + token},
    )

    assert response.status_code == 200
    assert response.json() == ["johndoe", "janedoe"]

def test__getUserById(db, client, addFakeUsers):
    token, _ = addFakeUsers

    response = client.get(
        "/users/u/1",
        headers={"Authorization": "Bearer " + token},
    )

    assert response.status_code == 200
    assert response.json() == {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "avatar": None,
        "id": 1,
        "status": "active",
    }

def test__getUserById__malformedId(db, client, addFakeUsers):
    token, _ = addFakeUsers

    response = client.get(
        "/users/u/abcd",
        headers={"Authorization": "Bearer " + token},
    )

    assert response.status_code == 422
    print(response.json())
    assert response.json()["detail"][0]["type"] == "int_parsing"

def test__db_cleanup(db):

    users = db.query(models.User).all()

    assert users == []

def test__createGame(db, client, addFakeUsers):
    token, _ = addFakeUsers

    response = client.post(
        "/games/",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
        json={"public": False, "color": "white"},
    )

    print(response.json())
    assert response.status_code == 200

    assert response.json() == {
        "black_id": None,
        "created_at": mock.ANY,
        "uuid": mock.ANY,
        "id": 1,
        "last_move_time": None,
        "owner_id": 1,
        "public": False,
        "status": GameStatus.WAITING,
        "turn": "white",
        "white_id": response.json()["owner_id"],
        "winner": None,
    }

def test__get_game_by_uuid(db, client, addFakeUsers, addFakeGames, johndoe):
    token, _ = addFakeUsers
    uuid = addFakeGames

    response = client.get(
        f"/games/{uuid}",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
        params={
            "random": False,
        },
    )

    print(response.json())
    assert response.status_code == 200
    assert response.json() == {
        "black": None,
        "created_at": mock.ANY,
        "uuid": mock.ANY,
        "id": 5,
        "owner": johndoe,
        "last_move_time": None,
        "public": False,
        "status": GameStatus.WAITING,
        "turn": "white",
        "white": johndoe,
        "winner": None,
    }

def test__get_me_games(db, client, addFakeUsers, addFakeGames, johndoe, janedoe):
    token, _ = addFakeUsers

    response = client.get(
        "/users/me/games/",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )

    print(response.json())
    assert response.status_code == 200
    assert len(response.json()) == 3
    assert response.json()[0] == {
        "black": janedoe,
        "created_at": mock.ANY,
        "uuid": mock.ANY,
        "id": 1,
        "last_move_time": None,
        "owner": johndoe,
        "public": False,
        "status": "started",
        "turn": "black",
        "white": johndoe,
        "winner": None,
    }    

def test__getGames__finishedGame(db, client, addFakeUsers, addFakeGames, addFakeGameSnaps, johndoe, janedoe):
    # change to second player
    jane_token = getToken("janedoe")
    _ = getToken("johndoe")

    response = client.get(
        "/users/me/games",
        headers={
            "Authorization": "Bearer " + jane_token,
            "Content-Type": "application/json",
        },
    )
    print(response.json())
    assert response.status_code == 200
    games = response.json()
    assert len(games) == 4
    finishedgame = [g for g in games if g["status"] == GameStatus.OVER][0]
    assert finishedgame["turn"] is None

# TODO test list random games before setting my player
def test__joinRandomGame(db, client, addFakeUsers, addFakeGames):
    token, _ = addFakeUsers

    oneUser = db.query(models.User)[1]

    response = client.patch(
        "/games",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )

    # TODO join game (client chooses one)
    game_dict = response.json()
    print(game_dict)
    assert response.status_code == 200
    assert game_dict != {}
    assert (
        game_dict["white"]["username"] == oneUser.username
        or game_dict["black"]["username"] == oneUser.username
    )
    assert game_dict == {
        "black": mock.ANY,
        "created_at": mock.ANY,
        "uuid": mock.ANY,
        "last_move_time": None,
        "id": mock.ANY,
        "owner": mock.ANY,
        "public": True,
        "status": "started",
        "turn": "white",
        "white": mock.ANY,
        "winner": None,
    }

# TODO deprecated, client chooses game and joins a random one
def test__joinRandomGame__noneAvailable(db, client, addFakeUsers, addFakeDoneGames):
    token, _ = addFakeUsers

    response = client.patch(
        "/games",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )

    print(response.json())
    assert response.status_code == 404
    assert response.json() == {"detail": "available random game not found"}

def test__get_available_games__all(db, client, addFakeUsers, addFakeGames):
    token, _ = addFakeUsers

    response = client.get(
        "/games",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )

    print(response.json())
    assert response.status_code == 200
    game_ids = [game["id"] for game in response.json()]
    assert game_ids == [1, 2, 3, 4, 5]

def test__get_available_games__waiting(db, client, addFakeUsers, addFakeGames):
    token, _ = addFakeUsers

    response = client.get(
        "/games",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
        params={"status": ["waiting"]},
    )

    print(response.json())
    assert response.status_code == 200
    game_ids = [(game["id"], game["status"]) for game in response.json()]
    assert game_ids == [
        (3, GameStatus.WAITING), (4, GameStatus.WAITING), (5, GameStatus.WAITING)
    ]

# TODO this test was deactivated by mistake
def _test__joinGame__playerAlreadyInGame(db, client, addFakeUsers, addFakeGames):
    token, username = addFakeUsers

    uuid = "123fr12339"

    user = crud.get_user_by_username(db, username)

    game_before = (
        db.query(models.Game).filter(models.Game.uuid == uuid).first()
    )

    response = client.get(
        f"/games/{uuid}/join",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )

    game = db.query(models.Game).filter(models.Game.uuid == uuid).first()

    print(response.json())
    assert response.status_code == 200
    if not game_before.black_id:
        assert game.black_id == user.id
    if not game_before.white_id:
        assert game.white_id == user.id
    assert response.json() == {
        "black_id": game.black_id,
        "created_at": mock.ANY,
        "uuid": game.uuid,
        "id": game.id,
        "last_move_time": None,
        "owner_id": game.owner_id,
        "public": False,
        "status": GameStatus.WAITING,
        "turn": "white",
        "white_id": game.white_id,
    }

def test__joinGame__playerAlreadyInGame__simple(db, client, addFakeUsers, addFakeGames):
    token, username = addFakeUsers
    uuid = addFakeGames

    crud.get_user_by_username(db, username)

    db.query(models.Game).filter(models.Game.uuid == uuid).first()

    response = client.get(
        f"/games/{uuid}/join",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 200

def test__getsnap__byNum(db, client, classicSetup, fakegamesdb, addFakeGameSnaps):
    firstgame_uuid, token = classicSetup
    firstgame_white_player = list(fakegamesdb.values())[0]["white"]
    token = getToken(firstgame_white_player)

    response = client.get(
        f"/games/{firstgame_uuid}/snap/0",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )

    print(response.json())
    assert response.status_code == 200
    # yapf: disable
    assert response.json() == {
        'game_id': 1,
        'created_at': mock.ANY,
        'id': 1,
        'move': None,
        'taken': '',
        'castleable': '',
        'move_number': 0,
        'board': ('xxxxxxxx'
                  'xxxxxxxx'
                  '________'
                  '________'
                  '________'
                  '________'
                  'pppppppp'
                  'rnbqkbnr'),
    }
    # yapf: enable

def test__getsnaps(db, client, classicSetup):
    firstgame_uuid, token = classicSetup

    response = client.get(
        f"/games/{firstgame_uuid}/snaps",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )

    print(response.json())
    assert response.status_code == 200
    # yapf: disable
    assert response.json() == [{
        'game_id': 1,
        'created_at': mock.ANY,
        'id': 1,
        'move': None,
        'taken': '',
        'castleable': '',
        'move_number': 0,
        'board': ('xxxxxxxx'
                    'xxxxxxxx'
                    '________'
                    '________'
                    '________'
                    '________'
                    'pppppppp'
                    'rnbqkbnr'),
    }, {
        'game_id': 1,
        'created_at': mock.ANY,
        'id': 2,
        'move': 'd2d4',
        'taken': '',
        'castleable': '',
        'move_number': 1,
        'board': ('xxxxxxxx'
                    'xxxxxxxx'
                    '________'
                    '________'
                    '___p____'
                    '________'
                    'ppp_pppp'
                    'rnbqkbnr'),
    }]
    # yapf: enable

def test__getsnap__latest(db, client, classicSetup):
    firstgame_uuid, token = classicSetup

    response = client.get(
        f"/games/{firstgame_uuid}/snap",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )

    print(response.json())
    assert response.status_code == 200
    # yapf: disable
    assert response.json() == {
        'game_id': 1,
        'created_at': mock.ANY,
        'id': 2,
        'move': 'd2d4',
        'taken': '',
        'castleable': '',
        'move_number': 1,
        'board': ('xxxxxxxx'
                  'xxxxxxxx'
                  '________'
                  '________'
                  '___p____'
                  '________'
                  'ppp_pppp'
                  'rnbqkbnr')
    }
    # yapf: enable

def test__getTurn(db, client, classicSetup):
    firstgame_uuid, token = classicSetup

    response = client.get(
        f"/games/{firstgame_uuid}/turn",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )

    print(response.json())
    assert response.status_code == 200
    assert response.json() == "black"

@pytest.mark.skip(reason="slow test")
def test__getTurn__long_polling(client, classicSetup):
    firstgame_uuid, _ = classicSetup
    token = getToken("janedoe")

    start = time.time()
    response = client.get(
        f"/games/{firstgame_uuid}/turn",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
        params={
            "long_polling": True
        }
    )

    elapsed = time.time() - start
    assert elapsed > 5


def test__move(db, client, classicSetup):
    firstgame_uuid, token = classicSetup

    # get previous game/board

    game_before = (
        db.query(models.Game)
        .filter(models.Game.uuid == firstgame_uuid)
        .first()
    )

    response = client.post(
        f"/games/{firstgame_uuid}/move",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
        json={
            "move": "d7d5",
        },
    )

    # get after game/board

    game_after = (
        db.query(models.Game)
        .filter(models.Game.uuid == firstgame_uuid)
        .first()
    )

    # test board is the expected one
    print([snap.__dict__ for snap in game_after.snaps])

    print(response.json())
    assert response.status_code == 200
    # assert DictEqual(response.json(), '')

    assert game_before.get_latest_snap().board == (
        "RNBQKBNR"
        "PPP_PPPP"
        "________"
        "___P____"
        "___p____"
        "________"
        "ppp_pppp"
        "rnbqkbnr"
    )

def test__move__filtered(db, client, classicSetup):
    firstgame_uuid, _ = classicSetup
    # change to second player
    token = getToken("janedoe")

    response = client.post(
        f"/games/{firstgame_uuid}/move",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
        json={
            "move": "d7d5",
        },
    )

    print(response.json())
    assert response.status_code == 200

    assert response.json()["board"] == (
        "RNBQKBNR"
        "PPP_PPPP"
        "________"
        "___P____"
        "___p____"
        "________"
        "XXX_XXXX"
        "XXXXXXXX"
    )

def test__possibleMoves__pawnMove(db, client, classicSetup):
    firstgame_uuid, _ = classicSetup
    # change to second player
    token = getToken("janedoe")

    square = "d7"

    response = client.get(
        f"/games/{firstgame_uuid}/moves/{square}",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )

    print("response: {}".format(response.json()))
    assert response.status_code == 200

    assert response.json() == ["d6", "d5"]

@pytest.mark.parametrize(
        "addCustomGameSnap",
        [((
        "____K___"
        "________"
        "________"
        "__p_____"
        "________"
        "____pk__"
        "___P_pp_"
        "________"
        ), "g3f3")],
        indirect=True
)
def test__possibleMoves__king(db, client, classicSetup, addCustomGameSnap):
    firstgame_uuid, token = classicSetup

    square = "f3"

    response = client.get(
        f"/games/{firstgame_uuid}/moves/{square}",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )

    print("response: {}".format(response.json()))
    assert response.status_code == 200

    assert response.json() == ["e4", "f4", "g4", "g3", "e2"]


@pytest.mark.parametrize(
        "addCustomGameSnap",
        [((
        "____K___"
        "________"
        "________"
        "________"
        "__pP____"
        "____pk__"
        "_____pp_"
        "________"
    ), "c2c4")],
        indirect=True
)
def test__possibleMoves__pawn_enpassant_black(db, client, classicSetup, addCustomGameSnap):
    firstgame_uuid, _ = classicSetup

    token = getToken("janedoe")

    square = "d4"

    response = client.get(
        f"/games/{firstgame_uuid}/moves/{square}",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )

    print("response: {}".format(response.json()))
    assert response.status_code == 200

    assert response.json() == ["c3", "d3", "e3"]

@pytest.mark.parametrize(
        "addCustomGameSnap",
        [((
        "____K___"
        "________"
        "________"
        "__pP____"
        "________"
        "____pk__"
        "_____pp_"
        "________"
    ), "d7d5")],
        indirect=True
)
def test__possibleMoves__pawn_enpassant_white(db, client, classicSetup, addCustomGameSnap):
    firstgame_uuid, token = classicSetup

    square = "c5"

    response = client.get(
        f"/games/{firstgame_uuid}/moves/{square}",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )

    print("response: {}".format(response.json()))
    assert response.status_code == 200

    assert response.json() == ["c6", "d6"]


@pytest.mark.parametrize(
        "addCustomGameSnap",
        [((
        "____K___"
        "________"
        "________"
        "__pP____"
        "________"
        "____pk__"
        "_____pp_"
        "________"
    ), "c7c5")],
        indirect=True
)
def test__possibleMoves__pawn_impossible_enpassant_black(db, client, classicSetup, addCustomGameSnap):
    firstgame_uuid, _ = classicSetup

    token = getToken("janedoe")

    square = "d5"

    response = client.get(
        f"/games/{firstgame_uuid}/moves/{square}",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )

    print("response: {}".format(response.json()))
    assert response.status_code == 200

    assert response.json() == ["d4"]


@pytest.mark.parametrize(
        "addCustomGameSnap",
        [((
        "____K___"
        "_____PP_"
        "_____p__"
        "________"
        "________"
        "_____k__"
        "_____pp_"
        "________"
    ), "f5f6")],
        indirect=True
)
def test__possibleMoves__pawn_take(db, client, classicSetup, addCustomGameSnap):
    firstgame_uuid, token = classicSetup

    square = "f6"

    response = client.get(
        f"/games/{firstgame_uuid}/moves/{square}",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )

    print("response: {}".format(response.json()))
    assert response.status_code == 200

    assert response.json() == ["g7"]

def send_move(client, game_uuid, move, token):
    response = client.post(
        f"/games/{game_uuid}/move",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
        json={
            "move": move,
        },
    )
    return response

def prettyBoard(boardStr):
    print("    abcdefgh")
    print("    01234567")
    for i in range(8):
        print("{} - {} - {}".format(i, boardStr[8 * i : 8 * i + 8], 8 - i))

def test__move__filtered_pawn(db, client, game_setup, addFakeGameSnaps):

    firstgame_uuid, john_token, jane_token = game_setup

    tokens = [jane_token, john_token]
    moves = ["e7e5", "d4e5", "h7h6", "e5e6"]

    response = send_move(client, firstgame_uuid, moves[0], tokens[0 % 2])
    print(response.json())
    prettyBoard(response.json()["board"])
    assert response.status_code == 200

    assert response.json()["board"] == (
        "RNBQKBNR"
        "PPPP_PPP"
        "________"
        "____P___"
        "___p____"
        "________"
        "XXX_XXXX"
        "XXXXXXXX"
    )

    response = send_move(client, firstgame_uuid, moves[1], tokens[1 % 2])
    print(response.json())
    prettyBoard(response.json()["board"])
    assert response.status_code == 200

    response = send_move(client, firstgame_uuid, moves[2], tokens[2 % 2])
    print(response.json())
    prettyBoard(response.json()["board"])
    assert response.status_code == 200

    assert response.json()["board"] == (
        "RNBQKBNR"
        "PPPP_PP_"
        "_______P"
        "____X___"
        "________"
        "________"
        "XXX_XXXX"
        "XXXXXXXX"
    )

# use this method as reference to reproduce any game moves
# TODO use a virgin game instead of the firstgame_uuid
def test__move__fogTest(db, client, game_setup, addFakeGameSnaps):

    firstgame_uuid, john_token, jane_token = game_setup

    tokens = [jane_token, john_token]
    moves = ["e7e6", "g2g4", "d8h4", "f2f4", "a7a6"]

    print(tokens)

    for i, move in enumerate(moves):
        print("move {} for {}".format(move, tokens[i % 2]))
        response = send_move(client, firstgame_uuid, move, tokens[i % 2])
        print(response.json())
        assert response.status_code == 200
        prettyBoard(response.json()["board"])

    assert response.json()["board"] == (
        "RNB_KBNR"
        "_PPP_PPP"
        "P___P___"
        "________"
        "___X_XpQ"
        "________"
        "XXX_X__X"
        "XXXXXXXX"
    )

def test__integrationTest__foolscheckmate(client):

    # create johndoe
    # create janedoe

    response = client.post(
        "/users/",
        json={
            "username": "johndoe",
            "full_name": "John Le Dow",
            "email": "john@doe.cat",
            "plain_password": "secret",
        },
    )

    john_username = response.json()["username"]

    assert response.status_code == 200

    response = client.post(
        "/users/",
        json={
            "username": "janedoe",
            "full_name": "Jane Le Dow",
            "email": "jane@doe.cat",
            "plain_password": "secret",
        },
    )

    jane_username = response.json()["username"]

    assert response.status_code == 200

    # authenticate
    response = client.post(
        "/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "username": "johndoe",
            "password": "secret",
        },
    )

    assert response.status_code == 200
    john_token = response.json()["access_token"]

    response = client.post(
        "/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "username": "janedoe",
            "password": "secret",
        },
    )

    assert response.status_code == 200
    jane_token = response.json()["access_token"]

    # john create game

    response = client.post(
        "/games/",
        headers={
            "Authorization": "Bearer " + john_token,
            "Content-Type": "application/json",
        },
        json={
            "public": False,
            "color": "white",
        },
    )

    assert response.status_code == 200

    game_uuid = response.json()["uuid"]

    # john already joined and jane joins game

    # check if game started
    response = client.get(
        f"/games/{game_uuid}",
        headers={
            "Authorization": "Bearer " + jane_token,
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == GameStatus.WAITING

    white = response.json()["white"]
    response.json()["black"]
    jane_color = (
        None if not white else "white" if white["username"] == jane_username else "black"
    )
    john_color = (
        None
        if not white
        else "white"
        if white['username'] == john_username
        else "black"
    )

    print(f"jane color is {jane_color}")

    response = client.get(
        f"/games/{game_uuid}/join",
        headers={
            "Authorization": "Bearer " + jane_token,
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 200

    print(response.json())

    # john send move
    # jane send move

    moves = ["f2f3", "e7e5", "g2g4", "d8h4", "f3f4", "h4e1"]

    boards = [
        (
            "xxxxxxxxxxxxxxxx_____________________________p__ppppp_pprnbqkbnr",
            "RNBQKBNRPPPPPPPP_____________________________X__XXXXX_XXXXXXXXXX",
        ),
        (
            "xxxxxxxxxxxx_xxx____________x________________p__ppppp_pprnbqkbnr",
            "RNBQKBNRPPPP_PPP____________P________________X__XXXXX_XXXXXXXXXX",
        ),
        (
            "xxxxxxxxxxxx_xxx____________x_________p______p__ppppp__prnbqkbnr",
            "RNBQKBNRPPPP_PPP____________P_________X______X__XXXXX__XXXXXXXXX",
        ),
        (
            "xxx_xxxxxxxx_xxx____________x_________pQ_____p__ppppp__prnbqkbnr",
            "RNB_KBNRPPPP_PPP____________P_________pQ_____X__XXXXX__XXXXXXXXX",
        ),
        (
            "xxx_xxxxxxxx_xxx____________P________ppQ________ppppp__prnbqkbnr",
            "RNB_KBNRPPPP_PPP____________P________ppQ________XXXXX__XXXXXXXXX",
        ),
        (
            "xxx_xxxxxxxx_xxx____________P________ppQ_____p__ppppp__prnbqkbnr",
            "RNB_KBNRPPPP_PPP____________P________pX______X__pppXX__XXXXqQbXX",
        ),
    ]

    tokens = [john_token, jane_token]

    for i, move in enumerate(moves):
        response = send_move(client, game_uuid, move, tokens[i % 2])
        print(
            f"ran move {move} by {jane_color if jane_token == tokens[i%2] else john_color}"
        )
        assert response.status_code == 200

        # they ask for game and turn

        response = client.get(
            f"/games/{game_uuid}/turn",
            headers={
                "Authorization": "Bearer " + jane_token,
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 200
        jane_turn = response.json()
        response = client.get(
            f"/games/{game_uuid}/turn",
            headers={
                "Authorization": "Bearer " + john_token,
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 200
        john_turn = response.json()

        # TODO what happens after checkmate?
        assert jane_turn == john_turn

        response = client.get(
            f"/games/{game_uuid}/snap",
            headers={
                "Authorization": "Bearer " + jane_token,
                "Content-Type": "application/json",
            },
        )

        print(prettyBoard(response.json()["board"]))

        # no winner
        if john_turn or jane_turn:
            # TODO note that this assert will fail if an enemy piece is seen
            if jane_color == "white":
                assert response.json()["board"] == boards[i][0]
            else:
                assert response.json()["board"] == boards[i][1]

        response = client.get(
            f"/games/{game_uuid}/snap",
            headers={
                "Authorization": "Bearer " + john_token,
                "Content-Type": "application/json",
            },
        )

        if john_turn or jane_turn:
            if john_color == "white":
                assert response.json()["board"] == boards[i][0]
            else:
                assert response.json()["board"]== boards[i][1]

    # checkmate

    response = client.get(
        f"/games/{game_uuid}",
        headers={
            "Authorization": "Bearer " + jane_token,
            "Content-Type": "application/json",
        },
    )

    print(
        "{} with {} won the game".format(
            "janedoe" if jane_color == response.json()["winner"] else "johndoe",
            jane_color,
        )
    )

    assert response.json()["winner"] == "black"

