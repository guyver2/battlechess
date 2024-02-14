import json

import pytest

from battlechess.server import models


def prettyBoard(boardStr):
    print("    abcdefgh")
    print("    01234567")
    for i in range(8):
        print("{} - {} - {}".format(i, boardStr[8 * i : 8 * i + 8], 8 - i))


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


def resetGame(db, uuid):
    game = db.query(models.Game).filter(models.Game.uuid == uuid).first()
    game.reset()
    db.commit()


def test__move__MrExonGame__OneGame__EnPassant(client, game_setup):

    firstgame_uuid, john_token, jane_token = game_setup

    tokens = [jane_token, john_token]

    # read games
    # for game in games:
    # for moves in game['moves']
    with open("ia/algebraic2icu/icu/mrexongames.txt") as json_file:
        data = json.load(json_file)
        moves = data["https://lichess.org/auXLYNj1"]
        for i, move in enumerate(moves):
            response = send_move(client, firstgame_uuid, move, tokens[i % 2])

            if response.status_code == 200:
                prettyBoard(response.json()["board"])
            else:
                print(response.json())
            response.status_code == 200


def test__move__MrExonGame__Enpassant2(db, client, game_setup):

    firstgame_uuid, john_token, jane_token = game_setup

    tokens = [john_token, jane_token]

    resetGame(db, firstgame_uuid)

    # read games
    # for game in games:
    # for moves in game['moves']
    with open("ia/algebraic2icu/icu/mrexongames.txt") as json_file:
        data = json.load(json_file)
        moves = data["https://lichess.org/X1Nk72xr"]
        for i, move in enumerate(moves):
            response = send_move(client, firstgame_uuid, move, tokens[i % 2])

            if response.status_code == 200:
                prettyBoard(response.json()["board"])
            else:
                print(response.json())
            assert response.status_code == 200


@pytest.mark.skip(reason="Extremely slow test. Run with -s option.")
def test__move__MrExonGames(db, client, game_setup):
    firstgame_uuid, john_token, jane_token = game_setup

    tokens = [john_token, jane_token]

    resetGame(db, firstgame_uuid)

    # read games
    # for game in games:
    # for moves in game['moves']
    with open("ia/algebraic2icu/icu/mrexongames.txt") as json_file:
        data = json.load(json_file)
        for game, moves in data.items():
            print("Game: {} moves {}".format(game, moves))
            for i, move in enumerate(moves):
                response = send_move(client, firstgame_uuid, move, tokens[i % 2])

                if response.status_code == 200:
                    prettyBoard(response.json()["board"])
                else:
                    print(response.json())
                assert response.status_code == 200

            resetGame(db, firstgame_uuid)
