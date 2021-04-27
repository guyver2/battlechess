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

    def test__toElements__initialboard(self):
        b = Board()
        b.reset()

        elements = b.toElements()

        expected = {
            'board':'RNBQKBNRPPPPPPPP________________________________pppppppprnbqkbnr',
            'castelable':'KLSkls',
            'taken':''
        }

        self.assertDictEqual(elements, expected)

    def test__toElements__someboard(self):
        b = Board()
        b.reset()
        b.castleable = sorted(['kb', 'kw', 'rkb'])
        b.taken = ['bb', 'rb', 'rw', 'pw']

        elements = b.toElements()

        expected = {
            'board':'RNBQKBNRPPPPPPPP________________________________pppppppprnbqkbnr',
            'castelable':'KSk',
            'taken':'BRrp'
        }

        self.assertDictEqual(elements, expected)