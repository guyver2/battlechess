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
            'board' : (
                'RNBQKBNR'
                'PPPPPPPP'
                '________'
                '________'
                '________'
                '________'
                'pppppppp'
                'rnbqkbnr'
            ),
            'taken' :'',
            'castleable' : 'LSKlsk',
            'enpassant' : '',
            'winner' : None,
        }

        return elements

    def test__updateFromElements__board(self):
        b = Board()
        b.reset()

        expected = b.toString()

        b.updateFromElements(**self.fakeElements())

        startStrUpdated = b.toString()

        self.assertEqual(startStrUpdated, expected)
