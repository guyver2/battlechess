from battlechess.core.btchBoard import BtchBoard


def startboardStr():
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

def fakeElements():
    elements = {
        "board": startboardStr(),
        "taken": "",
        "castleable": "LSKlsk",
        "enpassant": None,
        "winner": None,
    }

    return elements

def squares2ascii(squares):
    return "\n".join(
        "".join("x" if (i, j) in squares else "_" for j in range(0, 12))
        for i in range(0, 12)
    )

def test__factory():
    btchBoard = BtchBoard.factory(startboardStr())

    btchBoard.toElements() == fakeElements()

def test__isEnemy():

    result = BtchBoard.isEnemy("white", None)

    assert not result

    result = BtchBoard.isEnemy("white", "p")

    assert not result

    result = BtchBoard.isEnemy("white", "P")

    assert result

    result = BtchBoard.isEnemy("white", "_")

    assert not result

def test__rookMoves__emptyBoard():

    b = BtchBoard()
    b.empty()

    moves = sorted(sq for sq in b.rookMoves("white", 2, 2))

    print("moves\n{}".format(squares2ascii(moves)))

    expected = sorted(
        [(i, 2) for i in range(3, 10)] + [(2, j) for j in range(3, 10)]
    )

    print("expected\n{}".format(squares2ascii(expected)))

    assert moves == expected

def test__rookMoves__startBoard():

    b = BtchBoard()

    moves = sorted(sq for sq in b.rookMoves("black", 2, 2))

    expected = []

    assert moves == expected

def test__bishopMoves__emptyBoard():

    b = BtchBoard()
    b.empty()

    moves = sorted(sq for sq in b.bishopMoves("white", 6, 6))

    print("moves\n{}".format(squares2ascii(moves)))

    expected = sorted(
        [(i, i) for i in range(2, 10)] + [(3 + i, 9 - i) for i in range(0, 7)]
    )
    expected.remove((6, 6))
    expected.remove((6, 6))

    print("expected\n {}".format(squares2ascii(expected)))

    assert moves == expected

def test__moves__pawn():
    b = BtchBoard()

    moves = sorted(sq for sq in b.pawnMoves("white", 8, 6))

    expected = [(6, 6), (7, 6)]

    assert moves == expected

def test__moves__manyMoves():
    pass

def test__moves__enpassant():
    pass

def test__moves__notMovingForbidden():
    pass

# check that an impossible move is possible if fogged enemies
def test__moves__unknownInfo():
    pass

def test__filter__startPosition():
    color = "white"
    b = BtchBoard()
    b.filter(color)

    expectedBoardStr = (
        "________"
        "________"
        "________"
        "________"
        "________"
        "________"
        "pppppppp"
        "rnbqkbnr"
    )

    expected = BtchBoard.factory(expectedBoardStr)
    expected.castleable = "lsk"

    assert b.toElements() == expected.toElements()

def test__moves__fog():
    boardStr = (
        "________"
        "________"
        "________"
        "________"
        "________"
        "________"
        "ppppppp_"
        "rnbqkbnr"
    )

    b = BtchBoard.factory(boardStr)

    print("fog {} ".format(b.toElements()))

    moves = b.possibleMoves("white", 9, 9)

    expectedMoves = sorted([(i, 9) for i in range(2, 9)])

    assert moves == expectedMoves
