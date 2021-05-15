# j = rows = alpha
# i = cols = digit
# board[i][j]


class BtchBoard():

    def __init__(self):
        self.reset()
        self.taken = []
        self.castleable = str
        self.enpassant = None
        self.winner = None

    def reset(self):
        self.board = [[None, None, *['' for j in range(8)], None, None] for i in range(0, 12)]
        # yapf: disable
        self.board[0] = [None]*12
        self.board[1] = [None]*12
        self.board[2] = [None, None, 'R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R', None, None]
        self.board[3] = [None, None, 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', None, None]
        self.board[8] = [None, None, 'p', 'p', 'p', 'p', 'p', 'p', 'p', 'p', None, None]
        self.board[9] = [None, None, 'r', 'n', 'b', 'q', 'k', 'b', 'n', 'r', None, None]
        self.board[10] = [None]*12
        self.board[11] = [None]*12
        # yapf: enable

    def isOk(self, i, j):
        return self.board[i][j] != None

    def isIn(self, i, j):
        return i > 1 and i < 10 and j > 1 and j < 10

    def extendboard(self, boardStr):
        return "_" * 10 + "".join(["_" + boardStr[j * 8:(j + 1) * 8] + "_" for j in range(8)
                                  ]) + "_" * 10

    def shrinkboard(self):
        return [[self.board[i][j] for j in range(2, 10)] for i in range(2, 10)]

    def hasEnemy(self, i, j):
        c = self.board[i][j]
        if c is None:
            # TODO should we raise instead?
            return False
        # print(f"{j} {i} {c} {extboard}")
        for j2 in [j - 1, j, j + 1]:
            for i2 in [i - 1, i, i + 1]:
                c2 = self.board[j2 * 12 + i2]
                if c2 is None or c2 == '':
                    continue
                elif c.isupper() and c2.islower():
                    return True
                elif c.islower() and c2.isupper():
                    return True

    def filtersquare(self, color, i, j):
        c = self.board[j][i]
        if color == 'black':
            return c if c == '_' or c.isupper() or self.hasEnemy(i, j) else 'X'
        elif color == 'white':
            return c if c == '_' or c.islower() or self.hasEnemy(i, j) else 'x'
        else:
            print(f"{color} is not a color")
            return None

    def createFilteredBoard(self, color):
        return [[self.filterSquare(color, i, j) for j in range(2, 10)] for i in range(2, 10)]

    def createFilteredBoards(self):
        self.white_board = [
            [self.filterSquare('white', i, j) for j in range(2, 10)] for i in range(2, 10)
        ]
        self.black_board = [
            [self.filterSquare('black', i, j) for j in range(2, 10)] for i in range(2, 10)
        ]

    def boardForPlayer(self, player_color: str):
        if not self.black_board:
            self.createFilteredBoards(self)

        #foreach enemy piece, check if theres a friendly piece around, delete if not

        if player_color == 'black':
            print(f"filtered board is {self.black_board}")
            return self.black_board
        elif player_color == 'white':
            print(f"filtered board is {self.white_board}")
            return self.white_board
        else:
            print("Player color {player_color} is not a known color. {white, black}")
            return None

    def filterCastleable(self, player_color: str):
        if player_color == 'black':
            self.castelable = ''.join(c for c in self.castelable if c.isupper())
            # self.move = self.move if not self.move_number % 2 else None
        elif player_color == 'white':
            self.castelable = ''.join(c for c in self.castelable if c.islower())
            # self.move = self.move if self.move_number % 2 else None

    def getPossibleMoves(self, color, i, j):
        if color == 'white':
            board = self.white_board
        elif color == 'black':
            board = self.black_board
        else:
            print("Player color {player_color} is not a known color. {white, black}")
            # TODO raise
            return None

    def getColor(self, c):
        return 'black' if c.isUpper() else 'white' if c.isLower() else None

    def possibleMoves(self, color, i, j):
        c = self.board[i][j]
        if self.getColor(c) != color:
            return []

        if c.lower() == 'p':
            moves = self.pawnMoves(color, i, j)
        elif c.lower() == 'r':
            moves = self.rookMoves(color, i, j)
        elif c.lower() == 'n':
            moves = self.knightMoves(color, i, j)
        elif c.lower() == 'b':
            moves = self.bishopMoves(color, i, j)
        elif c.lower() == 'q':
            moves = self.queenMoves(color, i, j)
        elif c.lower() == 'k':
            moves = self.kingMoves(color, i, j)

        return moves

    def pawnMoves(self, color, i, j):
        pass

    def rookMoves(self, color, i, j):
        pass

    def bishopMoves(self, color, i, j):
        pass

    def knightMoves(self, color, i, j):
        pass

    def queenMoves(self, color, i, j):
        pass

    def kingMoves(self, color, i, j):
        pass