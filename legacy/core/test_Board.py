import unittest
import unittest.mock as mock

from core.Board import Board

class Test_Board(unittest.TestCase):

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
            'enpassant': None,
            'winner': None,
        }

        return elements

    def test__updateFromElements__board(self):
        b = Board()
        b.reset()

        expected = b.toString()

        b.updateFromElements(**self.fakeElements())

        startStrUpdated = b.toString()

        self.assertEqual(startStrUpdated, expected)

    def test__toElements__initialboard(self):
        b = Board()
        b.reset()

        elements = b.toElements()

        expected = {
            'board': 'RNBQKBNRPPPPPPPP________________________________pppppppprnbqkbnr',
            'castleable': 'KLSkls',
            'taken': ''
        }

        self.assertDictEqual(elements, expected)

    def test__toElements__someboard(self):
        b = Board()
        b.reset()
        b.castleable = sorted(['kb', 'kw', 'rkb'])
        b.taken = ['bb', 'rb', 'rw', 'pw']

        elements = b.toElements()

        expected = {
            'board': 'RNBQKBNRPPPPPPPP________________________________pppppppprnbqkbnr',
            'castleable': 'KSk',
            'taken': 'BRrp'
        }

        self.assertDictEqual(elements, expected)

    def test__toElements__anotherboard(self):
        b = Board()
        b.reset()
        b.board[0][2] = ''
        b.board[0][5] = ''
        b.board[0][7] = ''
        b.board[1][3] = 'pw'
        b.board[1][4] = ''
        b.board[5][7] = 'bb'
        b.board[6][3] = ''
        b.board[6][5] = ''
        b.board[7][0] = ''
        b.castleable = sorted(['kb', 'kw', 'rkb'])
        b.taken = ['bb', 'rb', 'rw', 'pw', 'pb']

        elements = b.toElements()

        expected = {
            'board': 'RN_QK_N_PPPp_PPP_______________________________Bppp_p_pp_nbqkbnr',
            'castleable': 'KSk',
            'taken': 'BRrpP'
        }

        self.assertDictEqual(elements, expected)

    def test__toElementsFiltered__anotherboard(self):
        b = Board()
        b.reset()
        b.board[0][2] = ''
        b.board[0][5] = ''
        b.board[0][7] = ''
        b.board[1][3] = 'pw'
        b.board[1][4] = ''
        b.board[5][7] = 'bb'
        b.board[6][3] = ''
        b.board[6][5] = ''
        b.board[7][0] = ''

        b.castleable = sorted(['kb', 'kw', 'rkb'])
        b.taken = ['bb', 'rb', 'rw', 'pw', 'pb']

        elements = b.toElements('w')

        expected = {
            'board': '___QK_____Pp___________________________________Bppp_p_pp_nbqkbnr',
            'castleable': 'KSk',
            'taken': 'BRrpP'
        }

        self.assertDictEqual(elements, expected)