import cPickle

RQBPOS = [0,0]
RKBPOS = [0,7]
RQWPOS = [7,0]
RKWPOS = [7,7]
KBPOS = [0,4]
KWPOS = [7,4]
CASTLEQBPOS = [0,2]
CASTLEKBPOS = [0,6]
CASTLEQWPOS = [7,2]
CASTLEKWPOS = [7,6]
CASTLEABLE = ['kb', 'kw', 'rqb', 'rkb', 'rqw', 'rkw']

class Board(object):
	def __init__(self):
		self.reset()
		self.taken = []
		self.castleable = list(CASTLEABLE)
		self.enpassant = -1
		self.winner = None
		self.enpassant = -1

	def reset(self):
		self.board = [['' for i in xrange(8)] for j in xrange(8)]
		self.board[0] = ['rb', 'nb', 'bb', 'qb', 'kb', 'bb', 'nb', 'rb']
		self.board[1] = ['pb', 'pb', 'pb', 'pb', 'pb', 'pb', 'pb', 'pb']
		self.board[7] = ['rw', 'nw', 'bw', 'qw', 'kw', 'bw', 'nw', 'rw']
		self.board[6] = ['pw', 'pw', 'pw', 'pw', 'pw', 'pw', 'pw', 'pw']

	# make a deep copy of the board
	def copy(self):
		res = Board()
		res.taken = list(self.taken)
		res.board = [list(l) for l in self.board]
		res.castleable = list(self.castleable)
		res.enpassant = self.enpassant
		res.winner = self.winner
		return res
			

	def isIn(self, i, j):
		return i>-1 and i<8 and j>-1 and j<8

	# tells wether a cell is free or not
	# returns :
	#	1 if the cell is empty
	#	2 if the cell is occupied by a different player than the one given
	#	0 if the cell is out of bound
	def isFree(self, i, j, c=''):
		if self.isIn(i,j) :
			if self.board[i][j] == '' :
				return 1
			if self.board[i][j][1] != c :
				return 2
		else :
			return 0

	def takeEnPassant(self, i, j, ii, jj):
		if self.board[i][j][0] == 'p' and jj == self.enpassant and (j == self.enpassant-1 or j == self.enpassant+1):
			if(   self.board[i][j][1] == 'w' and i == 3 or self.board[i][j][1] == 'b' and i == 4):
				#todo remove this error check
				if self.board[i][self.enpassant] == '':
					print "Nothing at " + str([i,self.enpassant]) + ". Assuming you killed normally"
				else:
					self.taken.append(str(self.board[i][self.enpassant]))
					self.board[i][self.enpassant] = ''

	def castleInfo(self, piece, i, j, ii, jj):
		if piece in self.castleable:
			if piece[1] == 'w':
				if [KWPOS,CASTLEQWPOS] == [[i,j],[ii,jj]] and 'rqw' in self.castleable:
						return 'rqw'
				if [KWPOS,CASTLEKWPOS] == [[i,j],[ii,jj]] and 'rkw' in self.castleable:
						return 'rkw'
			elif piece[1] == 'b':
				if [KBPOS,CASTLEQBPOS] == [[i,j],[ii,jj]] and 'rqb' in self.castleable:
						return 'rqb'
				if [KBPOS,CASTLEKBPOS] == [[i,j],[ii,jj]] and 'rkb' in self.castleable:
						return 'rkb'
		return ''

	def getRookReach(self, i, j, color):
		a = 1
		pos = []
		while a:
			f = self.isFree(i,j+a, color)
			if f :
				pos.append([i,j+a])
				a+=1
				if f == 2 : break
			else :
				break
		a = 1
		while True:
			f = self.isFree(i,j-a, color)
			if f :
				pos.append([i,j-a])
				a+=1
				if f == 2 : break
			else :
				break
		a = 1
		while True:
			f = self.isFree(i+a,j, color)
			if f :
				pos.append([i+a,j])
				a+=1
				if f == 2 : break
			else :
				break
		a = 1
		while True:
			f = self.isFree(i-a,j, color)
			if f :
				pos.append([i-a,j])
				a+=1
				if f == 2 : break
			else :
				break
		return pos

	def getBishopReach(self, i, j, color):
		a = 1
		pos = []
		while True:
			f = self.isFree(i+a,j+a, color)
			if f :
				pos.append([i+a,j+a])
				a+=1
				if f == 2 : break
			else :
				break
		a = 1
		while True:
			f = self.isFree(i-a,j-a, color)
			if f :
				pos.append([i-a,j-a])
				a+=1
				if f == 2 : break
			else :
				break
		a = 1
		while True:
			f = self.isFree(i+a,j-a, color)
			if f :
				pos.append([i+a,j-a])
				a+=1
				if f == 2 : break
			else :
				break
		a = 1
		while True:
			f = self.isFree(i-a,j+a, color)
			if f :
				pos.append([i-a,j+a])
				a+=1
				if f == 2 : break
			else :
				break
		return pos


	def getReachablePosition(self, i, j):
		c = self.board[i][j]
		pos = []
		if c == '':
			return []
		color = c[1]
		if c == 'pb':
			if self.isFree(i+1, j, 'b') == 1:
				pos.append([i+1,j])
			if self.isFree(i+1, j+1, 'b') == 2:
				pos.append([i+1,j+1])
			if self.isFree(i+1, j-1, 'b') == 2:
				pos.append([i+1,j-1])
			if i == 1 and self.isFree(i+2, j) == 1 \
								and self.isFree(i+1, j) == 1:
				pos.append([i+2,j])
			if self.enpassant != -1 and i == 4 and (j == self.enpassant-1 or j == self.enpassant+1):
				pos.append([i+1, self.enpassant])
		elif c == 'pw':
			if self.isFree(i-1, j, 'w') == 1:
				pos.append([i-1,j])
			if self.isFree(i-1, j+1, 'w') == 2:
				pos.append([i-1,j+1])
			if self.isFree(i-1, j-1, 'w') == 2:
				pos.append([i-1,j-1])
			if i == 6 and self.isFree(i-2, j) == 1 \
								and self.isFree(i-1, j) == 1:
				pos.append([i-2,j])
			if self.enpassant != -1 and i == 3 and (j == self.enpassant-1 or j == self.enpassant+1):
				pos.append([i-1, self.enpassant])
		elif c[0] == 'k':
			pos.append([i,j+1])
			pos.append([i,j-1])
			pos.append([i+1,j+1])
			pos.append([i+1,j-1])
			pos.append([i+1,j])
			pos.append([i-1,j+1])
			pos.append([i-1,j-1])
			pos.append([i-1,j])
			if c in self.castleable:
				if c[1] == 'w':
					if 'rqw' in self.castleable:
						if self.isFree(7,1) == 1  and self.isFree(7,2) == 1 \
																 and self.isFree(7,3) == 1 :
							pos.append([7,2])
					if 'rkw' in self.castleable:
						if self.isFree(7,6) == 1 and self.isFree(7,5) == 1:
							pos.append([7,6])
				elif c[1] == 'b':
					if 'rqb' in self.castleable:
						if self.isFree(0,1) == 1 and self.isFree(0,2) == 1 \
            										 and self.isFree(0,3) == 1:
							pos.append([0,2])
					if 'rkb' in self.castleable:
						if self.isFree(0,6) == 1 and self.isFree(0,5) == 1:
							pos.append([0,6])
		elif c[0] == 'n':
			pos.append([i+1,j+2])
			pos.append([i+1,j-2])
			pos.append([i-1,j+2])
			pos.append([i-1,j-2])
			pos.append([i+2,j+1])
			pos.append([i+2,j-1])
			pos.append([i-2,j+1])
			pos.append([i-2,j-1])
		elif c[0] == 'r':
			pos = self.getRookReach(i,j, color)
		elif c[0] == 'b':
			pos = self.getBishopReach(i,j,color)
		elif c[0] == 'q':
			# rook
			pos.extend(self.getRookReach(i,j,color))
			# bishop
			pos.extend(self.getBishopReach(i,j,color))
		res = []
		for p in pos:
			if self.isFree(p[0], p[1], color):
				res.append(p)
		return list(res)


	def getPossiblePosition(self, i, j):
		c = self.board[i][j]
		pos = []
		if c == '':
			return []
		color = c[1]
		if c == 'pb':
			pos.append([i+1,j])
			if self.isFree(i+1, j+1, 'b') == 2:
				pos.append([i+1,j+1])
			if self.isFree(i+1, j-1, 'b') == 2:
				pos.append([i+1,j-1])
			if i == 1 and self.isFree(i+1, j) == 1:
				pos.append([i+2,j])
			if self.enpassant != -1 and i == 4 and (j == self.enpassant-1 or j == self.enpassant+1):
				pos.append([i+1, self.enpassant])
		elif c == 'pw':
			pos.append([i-1,j])
			if self.isFree(i-1, j+1, 'w') == 2:
				pos.append([i-1,j+1])
			if self.isFree(i-1, j-1, 'w') == 2:
				pos.append([i-1,j-1])
			if i == 6 and self.isFree(i-1, j) == 1:
				pos.append([i-2,j])
			if self.enpassant != -1 and i == 3 and (j == self.enpassant-1 or j == self.enpassant+1):
				pos.append([i-1, self.enpassant])
		elif c[0] == 'k':
			pos.append([i,j+1])
			pos.append([i,j-1])
			pos.append([i+1,j+1])
			pos.append([i+1,j-1])
			pos.append([i+1,j])
			pos.append([i-1,j+1])
			pos.append([i-1,j-1])
			pos.append([i-1,j])
			if c in self.castleable:
				if c[1] == 'w':
					if 'rqw' in self.castleable:
							pos.append([7,2])
					if 'rkw' in self.castleable:
							pos.append([7,6])
				elif c[1] == 'b':
					if 'rqb' in self.castleable:
							pos.append([0,2])
					if 'rkb' in self.castleable:
							pos.append([0,6])
		elif c[0] == 'n':
			pos.append([i+1,j+2])
			pos.append([i+1,j-2])
			pos.append([i-1,j+2])
			pos.append([i-1,j-2])
			pos.append([i+2,j+1])
			pos.append([i+2,j-1])
			pos.append([i-2,j+1])
			pos.append([i-2,j-1])
		elif c[0] == 'r':
			for a in xrange(1,8):
				pos.append([i,j+a])
				pos.append([i+a,j])
				pos.append([i,j-a])
				pos.append([i-a,j])
		elif c[0] == 'b':
			for a in xrange(1,8):
				pos.append([i+a,j+a])
				pos.append([i-a,j+a])
				pos.append([i+a,j-a])
				pos.append([i-a,j-a])
		elif c[0] == 'q':
			for a in xrange(1,8):
				pos.append([i,j+a])
				pos.append([i+a,j])
				pos.append([i,j-a])
				pos.append([i-a,j])
				pos.append([i+a,j+a])
				pos.append([i-a,j+a])
				pos.append([i+a,j-a])
				pos.append([i-a,j-a])
		res = []
		for p in pos:
			if self.isIn(*p):
				res.append(p)
		return list(res)
	
	def getClosest(self, i, j, ti, tj, reach):
		d = 20
		res = None
		if ti - i == 0:
			di = 0
		elif ti - i < 0 :
			di = -1
		else :
			di =  1
		if tj - j == 0:
			dj = 0
		elif tj - j < 0 :
			dj = -1
		else :
			dj =  1
		for a in xrange(7,0,-1):
			if [i+a*di, j+a*dj] in reach :
				return [i+a*di, j+a*dj]
		return None

	def move(self, i, j, ii, jj, color=None):
		# are given position inside the board ?
		if not self.isIn(i,j) or not self.isIn(ii,jj):
			return False, []
		# the player is trying to move a piece from the other player
		if color and self.board[i][j][1] != color:
			return False, []
		if self.board[ii][jj] != '' and self.board[i][j][1] == self.board[ii][jj][1]:
			# same color
			return False, []
		reach = self.getReachablePosition(i,j) # actually possible destination (obstacles, ennemies)
		pos = self.getPossiblePosition(i,j) # anything in the range of the piece
		if [ii,jj] not in pos:
			return False, []
		elif [ii,jj] not in reach :
			res = self.getClosest(i,j,ii,jj,reach)
			if res :
				ii, jj = res
			else :
				return False, []
		if self.board[ii][jj] != '':
			self.taken.append(str(self.board[ii][jj]))

		#check if we killed in passant
		self.takeEnPassant(i,j,ii,jj)	
		#reset enpassant value
		self.enpassant = -1
		#the pawn jumped, set it as 'en passant' pawn
		if self.board[i][j][0] == 'p':
			if self.board[i][j][1] == 'b' and i == 1 and ii == 3:
				self.enpassant = j
			elif self.board[i][j][1] == 'w' and i == 6 and ii == 4:
				self.enpassant = j

		# replace destination with origin
		self.board[ii][jj] = self.board[i][j]
		self.board[i][j] = ''

		# if a pawn reached the end of the board, it becomse a queen
		if self.board[ii][jj][0] == 'p' and (ii==0 or ii==7) :
			self.board[ii][jj] = 'q'+self.board[ii][jj][1]

    	# if we were performing a castle, move the tower too 
		whichRock = self.castleInfo(self.board[ii][jj],i,j,ii,jj)  
		if whichRock == 'rqb':
			self.board[0][0] = ''
			self.board[0][3] = 'rb'
		elif whichRock == 'rkb':
			self.board[0][7] = '' 
			self.board[0][5] = 'rb' 
		elif whichRock == 'rqw':
			self.board[7][0] = '' 
			self.board[7][3] = 'rw' 
		elif whichRock == 'rkw':
			self.board[7][7] = '' 
			self.board[7][5] = 'rw' 
		# if k or r, castle for that piece forbidden in the future
		if self.board[ii][jj][0] == 'k' and self.board[ii][jj] in self.castleable:
			self.castleable.remove(self.board[ii][jj])	
		elif self.board[ii][jj][0] == 'r':
			if [i, j] == RQBPOS and 'rqb' in self.castleable:
				self.castleable.remove('rqb')
			elif [i, j] == RKBPOS and 'rkb' in self.castleable:
				self.castleable.remove('rkb')
			elif [i, j] == RQWPOS and 'rqw' in self.castleable:
				self.castleable.remove('rqw')
			elif [i, j] == RKWPOS and 'rkw' in self.castleable:
				self.castleable.remove('rkw')

		# check if we have a winner
		if 'kb' in self.taken :
			self.winner = 'w'
		elif 'kw' in self.taken :
			self.winner = 'b'

		return True, [i,j,ii,jj]


	# save the state of the board for a given player (or full state)
	def dump(self, color=None):
		boardCopy = self.copy()
		# hide other player
		if color :
			visibility = [[False for i in xrange(8)] for j in xrange(8)]
			for i in xrange(8):
				for j in xrange(8) :
					if boardCopy.board[i][j].endswith(color) :
						for di in xrange(-1,2):
							for dj in xrange(-1,2):
								if boardCopy.isIn(i+di, j+dj) :
									visibility[i+di][j+dj] = True
			for i in xrange(8):
				for j in xrange(8) :
					if not visibility[i][j] :
						boardCopy.board[i][j] = ''
		return boardCopy

	# dump as a string to ease portability with other apps
	def toString(self, color=None):
		visibility = [[True for i in xrange(8)] for j in xrange(8)]
		if color : # hide if necessary
			visibility = [[False for i in xrange(8)] for j in xrange(8)]
			for i in xrange(8):
				for j in xrange(8) :
					if self.board[i][j].endswith(color) :
						for di in xrange(-1,2):
							for dj in xrange(-1,2):
								if self.isIn(i+di, j+dj) :
									visibility[i+di][j+dj] = True
		boardStr = ''
		for i in xrange(8):
			for j in xrange(8) :
				if not visibility[i][j] :
					boardStr += '_' # 3 spaces
				else :
					boardStr += self.board[i][j]+'_'
		boardStr = boardStr[:-1] # remove last '_'
		takenStr = '_'.join(self.taken)
		if color :
			castleableStr = '_'.join([e for e in self.castleable if e.endswith(color)])
		else :
			castleableStr = '_'.join([e for e in self.castleable])
		#todo only send enpassant if it's actually possible, otherwise we are leaking information
		if color == 'b' and visibility[4][self.enpassant] == False:
			enpassantStr = str(-1) 
		elif color == 'w' and visibility[3][self.enpassant] == False:
			enpassantStr = str(-1) 
		else:
			enpassantStr = str(self.enpassant)
		if self.winner : winnerStr = self.winner
		else : winnerStr = 'n'
		res = boardStr+'#'+takenStr+'#'+castleableStr+'#'+enpassantStr+'#'+winnerStr
		return res

	# update whole state from a string
	def updateFromString(self, data):
		boardStr, takenStr, castleableStr,enpassantStr,winnerStr = data.split('#')
		for i, c in enumerate(boardStr.split('_')):
			self.board[i/8][i%8] = c
		if takenStr == '':
			self.taken = []
		else :
			self.taken = takenStr.split('_')
		if castleableStr == '':
			self.castleable = []
		else :
			self.castleable = castleableStr.split('_')
		self.enpassant = int(enpassantStr)
		if winnerStr == 'n':
			self.winner = None
		else :
			self.winner = winnerStr


	def updateFromBoard(self, board):
		self.taken = list(board.taken)
		self.board = [list(l) for l in board.board]
		self.castleable = list(board.castleable)
		self.enpassant = board.enpassant
		self.winner = board.winner


if __name__ == '__main__':
	board = Board()

	for i in xrange(8):
		for j in xrange(8):
			print "%4s"%board.board[i][j],
		print
	print board.taken
	print board.castleable
	print board.winner

	print(board.move(1,2,4,2)) # invalid move
	print(board.move(6,2,4,2)) # valid move

	print '----------------'

	board.updateFromString(board.toString('w'))


	for i in xrange(8):
		for j in xrange(8):
			print "%4s"%board.board[i][j],
		print
	print board.taken
	print board.castleable
	print board.winner


























