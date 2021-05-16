import unittest
import unittest.mock as mock

from core.btchBoard import BtchBoard


class Test_BtchBoard(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def fakeElements(self):
        elements = {
            'board': ('RNBQKBNR'
                      'PPPPPPPP'
                      '________'
                      '________'
                      '________'
                      '________'
                      'pppppppp'
                      'rnbqkbnr'),
            'taken': '',
            'castleable': 'LSKlsk',
            'enpassant': '',
            'winner': None,
        }

        return elements

    def squares2ascii(self, squares):
        return "\n".join(
            "".join('x' if (i, j) in squares else '_' for j in range(0, 12)) for i in range(0, 12))

    def test__isEnemy(self):

        result = BtchBoard.isEnemy('white', None)

        self.assertFalse(result)

        result = BtchBoard.isEnemy('white', 'p')

        self.assertFalse(result)

        result = BtchBoard.isEnemy('white', 'P')

        self.assertTrue(result)

        result = BtchBoard.isEnemy('white', '_')

        self.assertFalse(result)

    def test__rookMoves__emptyBoard(self):

        b = BtchBoard()
        b.empty()

        moves = sorted(sq for sq in b.rookMoves('white', 2, 2))

        print('moves\n{}'.format(self.squares2ascii(moves)))

        expected = sorted([(i, 2) for i in range(3, 10)] + [(2, j) for j in range(3, 10)])

        print('expected\n{}'.format(self.squares2ascii(expected)))

        self.assertListEqual(moves, expected)

    def test__rookMoves__startBoard(self):

        b = BtchBoard()

        moves = sorted(sq for sq in b.rookMoves('black', 2, 2))

        expected = []

        self.assertListEqual(moves, expected)

    def test__bishopMoves__emptyBoard(self):

        b = BtchBoard()
        b.empty()

        moves = sorted(sq for sq in b.bishopMoves('white', 6, 6))

        print('moves\n{}'.format(self.squares2ascii(moves)))

        expected = sorted([(i, i) for i in range(2, 10)] + [(3 + i, 9 - i) for i in range(0, 7)])
        expected.remove((6, 6))
        expected.remove((6, 6))

        print('expected\n {}'.format(self.squares2ascii(expected)))

        self.assertListEqual(moves, expected)

    def test__moves__notMovingForbidden(self):
        pass