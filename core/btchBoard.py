# j = rows = alpha
# i = cols = digit
# board[i][j]


# create a board for each player
# using list of lists requires deepcopy
class BtchBoard():

    def __init__(self, board=None):
        self.board = board or self.startBoard()
        self.taken = ''
        self.castleable = 'LSKlsk'  # TODO change for 'LSls'
        self.enpassant = None  #column -> 2-9
        self.winner = None

    def startBoard(self):
        board = [[None, None, *['' for j in range(8)], None, None] for i in range(0, 12)]

        # yapf: disable
        board[0] = [None]*12
        board[1] = [None]*12
        board[2] = [None, None, 'R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R', None, None]
        board[3] = [None, None, 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', None, None]
        board[8] = [None, None, 'p', 'p', 'p', 'p', 'p', 'p', 'p', 'p', None, None]
        board[9] = [None, None, 'r', 'n', 'b', 'q', 'k', 'b', 'n', 'r', None, None]
        board[10] = [None]*12
        board[11] = [None]*12
        # yapf: enable

        return board

    def reset(self):
        self.board = self.startBoard()
        self.taken = ''
        self.castleable = 'KLSkls'
        self.enpassant = None
        self.winner = None

    # make a deep copy of the board
    def copy(self, board=None):
        bb = BtchBoard(board or [list(b) for b in self.board])
        bb.taken = self.taken
        bb.castleable = self.castleable
        bb.enpassant = self.enpassant
        bb.winner = self.winner
        return bb

    def filteredBoardFactory(self, color):
        # you can self.filterBoard and self.copy(board) if efficency is a problem
        btchBoard = self.copy()
        btchBoard.filter(color)
        return btchBoard

    @classmethod
    def factory(cls, boardstr: str):
        # board, taken, castleable, enpassant = boardstr.split("#")
        b = BtchBoard()
        for i, c in enumerate(boardstr):
            b.board[i // 8 + 2][i % 8 + 2] = c if c != '_' else ''
        return b

    def boardToStr(self):

        def bpiece(p):
            return '_' if not p else p

        return ''.join([bpiece(self.board[i][j]) for i in range(2, 10) for j in range(2, 10)])

    def toElements(self):

        elements = {
            "castleable": self.castleable,
            "taken": self.taken,
            "board": self.boardToStr(),
            "enpassant": self.enpassant,
            "winner": self.winner
        }
        return elements

    def empty(self):
        self.board = [[None, None, *['' for j in range(8)], None, None] for i in range(0, 12)]
        self.board[0] = [None] * 12
        self.board[1] = [None] * 12
        self.board[10] = [None] * 12
        self.board[11] = [None] * 12

    def isOk(self, i, j):
        return self.board[i][j] != None

    def isIn(self, i, j):
        return i > 1 and i < 10 and j > 1 and j < 10

    @staticmethod
    def isWhite(color):
        return color == 'white'

    @staticmethod
    def isBlack(color):
        return color == 'black'

    @staticmethod
    def getColor(c):
        return 'black' if c.isupper() else 'white' if c.islower() else None

    def isFree(self, i, j):
        return self.board[i][j] == ''

    @staticmethod
    def isEnemy(color, piece):
        return True if piece and (piece.isupper() and color == 'white' \
                    or piece.islower() and color == 'black') else False

    def extendboard(self, boardStr):
        return "_" * 10 + "".join(["_" + boardStr[j * 8:(j + 1) * 8] + "_" for j in range(8)
                                  ]) + "_" * 10

    def shrinkboard(self):
        return [[self.board[i][j] for j in range(2, 10)] for i in range(2, 10)]

    def hasEnemy(self, i, j):
        c = self.board[i][j]
        for jj in [j - 1, j, j + 1]:
            for ii in [i - 1, i, i + 1]:
                cc = self.board[ii][jj]
                if cc == '' or cc is None:
                    continue
                elif c.isupper() and cc.islower():
                    return True
                elif c.islower() and cc.isupper():
                    return True

    def filterSquare(self, color, i, j):
        c = self.board[i][j]
        if c is None or c == '' or self.hasEnemy(i, j):
            return c
        elif color == 'black':
            return c if c.isupper() else ''
        elif color == 'white':
            return c if c.islower() else ''
        else:
            print(f"{color} is not a color")
            return None

    # TODO we could filter the shrunk board if speed is an issue
    def filterBoard(self, color):
        return [[self.filterSquare(color, i, j) for j in range(0, 12)] for i in range(0, 12)]

    def filterCastleable(self, color):
        if color == 'black':
            self.castleable = ''.join(c for c in self.castleable if c.isupper())
            # self.move = self.move if not self.move_number % 2 else None
        elif color == 'white':
            self.castleable = ''.join(c for c in self.castleable if c.islower())
            # self.move = self.move if self.move_number % 2 else None

    def filterEnpassant(self, color):
        j = self.enpassant
        if j:
            # if owner is black, check white enpassant
            i = 7 if self.isBlack(color) else 4
            # and filter out if not visible
            if not self.hasEnemy(i, j):
                self.enpassant = ''

    # color is the viewer color. So if you want to keep the black info, color = black.
    def filter(self, color):
        self.board = self.filterBoard(color)
        self.filterCastleable(color)
        self.filterEnpassant(color)

    def possibleMoves(self, color, i, j):
        c = self.board[i][j]
        if self.getColor(c) != color:
            return list()

        moves = list()

        if c.lower() == 'p':
            moves = list(self.pawnMoves(color, i, j))
        elif c.lower() == 'r':
            moves = list(self.rookMoves(color, i, j))
        elif c.lower() == 'n':
            moves = list(self.knightMoves(color, i, j))
        elif c.lower() == 'b':
            moves = list(self.bishopMoves(color, i, j))
        elif c.lower() == 'q':
            moves = list(self.queenMoves(color, i, j))
        elif c.lower() == 'k':
            moves = list(self.kingMoves(color, i, j))
        else:
            print('Unknown piece {}'.format(c))

        print('Possible moves {} at {}, {}: {}'.format(c, i, j, moves))

        moves.sort()

        return moves

    def vectorMove(self, color, i, j, v):
        ii, jj = i, j
        while True:
            ii, jj = ii + v[0], jj + v[1]
            if self.isFree(ii, jj):
                yield (ii, jj)
            elif self.isEnemy(color, self.board[ii][jj]):
                yield (ii, jj)
                break
            else:
                break

    def rookMoves(self, color, i, j):
        v = (1, 0)
        yield from self.vectorMove(color, i, j, v)
        v = (0, 1)
        yield from self.vectorMove(color, i, j, v)
        v = (-1, 0)
        yield from self.vectorMove(color, i, j, v)
        v = (0, -1)
        yield from self.vectorMove(color, i, j, v)

    def bishopMoves(self, color, i, j):
        v = (1, 1)
        yield from self.vectorMove(color, i, j, v)
        v = (-1, 1)
        yield from self.vectorMove(color, i, j, v)
        v = (1, -1)
        yield from self.vectorMove(color, i, j, v)
        v = (-1, -1)
        yield from self.vectorMove(color, i, j, v)

    def queenMoves(self, color, i, j):
        yield from self.rookMoves(color, i, j)
        yield from self.bishopMoves(color, i, j)

    def kingMoves(self, color, i, j):
        for di in range(-1, 1):
            for dj in range(-1, 1):
                ii, jj = i + di, j + dj
                if self.isFree(ii, jj):
                    yield (ii, jj)
                else:
                    if self.isEnemy(color, self.board[ii][jj]):
                        yield (ii, jj)

        #castles
        k, l, s = 'KLS' if self.isBlack(color) else 'kls'
        r = 2 if self.isBlack(color) else 9
        if k in self.castelable:
            if l in self.castelable:
                if self.isFree(r, 5) and self.isFree(r, 4) and self.isFree(r, 3):
                    yield (r, 4)
            if s in self.castelable:
                if self.isFree(r, 7) and self.isFree(r, 8):
                    yield (r, 8)

    def knightMoves(self, color, i, j):
        deltas = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (-1, 2), (1, -2), (-1, -2)]
        return [(i + di, j + dj)
                for di, dj in deltas
                if self.isFree(i + di, j + dj) or self.isEnemy(color, self.board[i + di][j + dj])]

    def pawnMoves(self, color, i, j):
        di = -1 if self.isWhite(color) else 1

        # move forward
        if self.isFree(i + di, j):
            yield (i + di, j)

        # kill
        if self.isEnemy(i + di, j - 1):
            yield (i + di, j - 1)

        if self.isEnemy(i + di, j + 1):
            yield (i + di, j + 1)

        # enpassant
        enpassantrow = 7 if self.isWhite(color) else 5
        if i == enpassantrow:
            if self.isEnemy(i, j - 1) and j - 1 in self.enpassant:
                yield (i, j - 1)

            if self.isEnemy(i, j + 1) and j + 1 in self.enpassant:
                yield (i, j + 1)
