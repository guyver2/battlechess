import chess
import chess.pgn
import json

mrexongames = 'ia/algebraic2icu/pgn/lichess_MrExon_2021-05-23.pgn'

# board = chess.board()
# themoves = "f4 e6 2. Nf3 d5 3. e3 c5 4. b3 f6 5. Bd3 g6 6. Qe2".split(' ')
# moves = [move for move in themovesl if '.' not in move]
#ucimoves = [board.push_san(move).uci() for move in moves]

username = mrexongames.split('_')[1]

pgn = open(mrexongames)

ucigames = {}

while True:
    game = chess.pgn.read_game(pgn)
    if not game:
        break

    print("[{} {}] {} {} vs {} {}".format(game.headers['UTCDate'], game.headers['UTCTime'],
                                          game.headers['Site'], game.headers['White'],
                                          game.headers['Black'], game.headers['Result']))
    ucigames[game.headers['Site']] = [move.uci() for move in game.mainline_moves()]

with open('ia/algebraic2icu/icu/{}games.txt'.format(username), 'w') as outfile:
    json.dump(ucigames, outfile)