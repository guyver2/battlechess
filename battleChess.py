import pygame
import sys
import time
import math
import socket
import threading
import random
from pygame.locals import *

# GLOBAL VARIABLES
W, H = 512, 384 # wibndow prop
black = (0, 0, 0, 255) # background
WHITE, BLACK = True, False # players
#--------------------------


class Board():
	def __init__(self, sprite_pieces, sniper):
		self.reset()
		self.sprite_pieces = sprite_pieces
		self.sniper = sniper
		self.taken = []
		self.visibility = None
		# debug purpose
		#self.board[1][5] = 'pw'
		# self.board[2][3] = 'pw'
		# self.board[2][5] = 'pw'
		# self.board[4][4] = 'qb'
		# self.board[4][3] = 'bb'
		# self.board[4][5] = 'rb'

	def reset(self):
		self.board = [['' for i in xrange(8)] for j in xrange(8)]
		self.board[0] = ['rb', 'nb', 'bb', 'qb', 'kb', 'bb', 'nb', 'rb']
		self.board[1] = ['pb', 'pb', 'pb', 'pb', 'pb', 'pb', 'pb', 'pb']
		self.board[7] = ['rw', 'nw', 'bw', 'qw', 'kw', 'bw', 'nw', 'rw']
		self.board[6] = ['pw', 'pw', 'pw', 'pw', 'pw', 'pw', 'pw', 'pw']

	# make a deep copy of the board
	def copy(self):
		res = Board(self.sprite_pieces, self.sniper)
		res.taken = list(self.taken)
		res.board = [list(l) for l in self.board]
		return res

	def draw(self, screen, selected=None, turn=None):
		for i in xrange(8):
			for j in xrange(8) :
				c = self.board[i][j]
				if c == '':
					continue
				else :
					dx = 2
					dy = 2
					if c[1] == 'b':
						dx += 84
					if c[0] in ['n', 'r', 'b']:
						dx += 42
					if c[0] in ['q', 'r']:
						dy += 42
					if c[0] in ['p', 'b']:
						dy += 84
					patch_rect = (dx, dy, 36, 36)
					screen.blit(self.sprite_pieces, (106+j*40, 30+i*40), patch_rect)
		if turn != None:
			self.visibility = [[False for i in xrange(8)] for j in xrange(8)]
			# get white piece
			color = 'b'
			if turn : 
				color = 'w'
			for i in xrange(8):
				for j in xrange(8):
					if self.board[i][j].endswith(color) :
						for di in xrange(-1,2):
							for dj in xrange(-1,2):
								if self.isIn(i+di, j+dj) :
									self.visibility[i+di][j+dj] = True
			fog = pygame.Surface((38, 38))
			fog.set_alpha(255)
			fog.fill((0, 0, 0))
			for i in xrange(8):
				for j in xrange(8):
					if not self.visibility[i][j] :
						screen.blit(fog, (106+j*40, 30+i*40))		
		# draw possible displacement positions	
		s = pygame.Surface((34, 34))
		s.set_alpha(128)
		s.fill((255, 0, 255))
		if selected:
			pos = self.getPossiblePosition(selected[0], selected[1])
			#pos = self.getReachablePosition(selected[0], selected[1])
			for p in pos :
				screen.blit(s, (106+p[1]*40, 30+p[0]*40))
		# draw taken pieces
		# white 
		for i, p in enumerate([p for p in self.taken if p[1] == 'w']) :
			dx = 2
			dy = 2
			if p[0] in ['n', 'r', 'b']:
				dx += 42
			if p[0] in ['q', 'r']:
				dy += 42
			if p[0] in ['p', 'b']:
				dy += 84
			patch_rect = (dx, dy, 36, 36)
			screen.blit(self.sprite_pieces, (6+(i%2)*40, 20+(i/2)*40), patch_rect)
		for i, p in enumerate([p for p in self.taken if p[1] == 'b']) :
			dx = 86
			dy = 2
			if p[0] in ['n', 'r', 'b']:
				dx += 42
			if p[0] in ['q', 'r']:
				dy += 42
			if p[0] in ['p', 'b']:
				dy += 84
			patch_rect = (dx, dy, 36, 36)
			screen.blit(self.sprite_pieces, (426+(i%2)*40, 338-(i/2)*40), patch_rect)
			


	def click(self, pos):
		i = (pos[1]-30)/40
		j = (pos[0]-106)/40
		if self.isIn(i,j):
			return [i, j]
		return None

	def isIn(self, i, j):
		return i>-1 and i<8 and j>-1 and j<8

	def isFree(self, i, j, c=''):
		if self.isIn(i,j) :
			if self.board[i][j] == '' :
				return 1
			if self.board[i][j][1] != c :
				return 2
		else :
			return 0


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
		elif c[0] == 'k':
			pos.append([i,j+1])
			pos.append([i,j-1])
			pos.append([i+1,j+1])
			pos.append([i+1,j-1])
			pos.append([i+1,j])
			pos.append([i-1,j+1])
			pos.append([i-1,j-1])
			pos.append([i-1,j])
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
		elif c == 'pw':
			pos.append([i-1,j])
			if self.isFree(i-1, j+1, 'w') == 2:
				pos.append([i-1,j+1])
			if self.isFree(i-1, j-1, 'w') == 2:
				pos.append([i-1,j-1])
			if i == 6 and self.isFree(i-1, j) == 1:
				pos.append([i-2,j])
		elif c[0] == 'k':
			pos.append([i,j+1])
			pos.append([i,j-1])
			pos.append([i+1,j+1])
			pos.append([i+1,j-1])
			pos.append([i+1,j])
			pos.append([i-1,j+1])
			pos.append([i-1,j-1])
			pos.append([i-1,j])
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

	def move(self, i, j, ii, jj):
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
			if self.visibility : # check if we're not in playback mode
				if (abs(ii-i) > 1 or abs(jj-j) > 1) and (self.visibility[ii][jj] == False or self.visibility[i][j] == False):
					self.sniper.play()
			self.taken.append(str(self.board[ii][jj]))
		self.board[ii][jj] = self.board[i][j]
		# if a pawn reached the end of the board, it becomse a queen
		if self.board[ii][jj][0] == 'p' and (ii==0 or ii==7) :
			self.board[ii][jj] = 'q'+self.board[ii][jj][1]
		self.board[i][j] = ''
		return True, [i,j,ii,jj]


# ****************************************************************************

def loadData():
	sprite_board = pygame.image.load('data/board_big.png').convert(24)
	sprite_pieces = pygame.image.load('data/pieces_big.png').convert(24)
	sprite_pieces.set_colorkey((255,255,255))
	sprite_pieces = sprite_pieces.convert_alpha(sprite_pieces)
	sniper = pygame.mixer.Sound('data/sniper.wav')
	return [sprite_board, sprite_pieces, sniper]


# get keyboard to work 
def events():
	click = False
	keys  = []
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			return (False, None, keys)
		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_ESCAPE:
				return (False, None, keys)
			if event.key == pygame.K_SPACE:
				keys.append('SPACE')
			if event.key == pygame.K_RIGHT:
				keys.append('RIGHT')
			if event.key == pygame.K_LEFT:
				keys.append('LEFT')
		elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
				mousex, mousey = pygame.mouse.get_pos()
				return (True, [mousex, mousey], keys)
	return (True, None, keys)




def myreceive(sock, MSGLEN):
	msg = ''
	while len(msg) < MSGLEN:
		chunk = sock.recv(MSGLEN-len(msg))
		if chunk == '':
			raise RuntimeError("socket connection broken")
		msg = msg + chunk
	return msg

def sendN(sock, msg):
	sock.send("%05d"%len(msg))
	sock.send(msg)

def receiveN(sock):
	size = int(myreceive(sock, 5))
	return myreceive(sock, size)



class SockThread(threading.Thread):
	def __init__(self, sock):
		super(SockThread, self).__init__()
		self.sock = sock
		self.sock.settimeout(0.01)
		self.ready = False
		self.data = None
		self.running = True

	def run(self):
		while self.running :
			if not self.ready :
				try :
					self.data = myreceive(self.sock, 4)
					if self.data == 'over' :
						self.running = False
					self.ready = True
				except :
					pass
			time.sleep(0.01)
		self.sock.close()

		



# ****************************************************************************

# regular two player game over network
def networkGame(argv):

	PORT = 8887
	HOST = "sxbn.org" # "iccvlabsrv16.epfl.ch" #  
	NICK = "anon_%d"%(random.randint(0,100))
	if len(argv) == 1 :
		print "Usage:\n\t", argv[0], "NICKNAME HOST PORT"
	if len(argv) > 1 :
		NICK = argv[1].replace(' ', '_')
	if len(argv) > 2 :
		HOST = argv[2]
	if len(argv) > 3 :
		PORT = int(argv[3])

	print "connecting to", HOST+":"+str(PORT)

	pygame.init()
	pygame.mixer.init()
	screen = pygame.display.set_mode((W,H))
	sprite_board, sprite_pieces, sniper = loadData()
	#pygame.mixer.music.load('data/sniper.mp3')
	#pygame.mixer.music.play()
	board = Board(sprite_pieces, sniper)

	clickCell = None
	localPlayer = None
	turn = WHITE
	#create socket and connect
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect((HOST, PORT))
	# get player color
	msg = myreceive(sock, 5)
	print "I'll be player ", msg
	if msg == "white" :
		localPlayer = WHITE
	else :
		localPlayer = BLACK
	#send nickname
	sendN(sock, NICK)
	# wait for other player
	msg = myreceive(sock, 5)
	print "ready ? ", msg
	# get his nickname
	opponent = receiveN(sock)
	print "Playing against", opponent
	pygame.display.set_caption(NICK+" Vs. "+opponent)

	# start socket thread
	sockThread = SockThread(sock)
	sockThread.start()

	# MAIN GAME LOOP
	loop = True
	while(loop):
		screen.fill(black)
		screen.blit(sprite_board, (0,0))
		board.draw(screen, clickCell, localPlayer)
		font = pygame.font.Font(None, 20)
		if turn :
			text = font.render("White", 1, (0, 0, 0))
		else :
			text = font.render("Black", 1, (0, 0, 0))
		screen.blit(text,(10, 10))
		# other player's turn :
		if turn != localPlayer:
			loop, _ , _ = events() # grab events and throw them away :)
			if sockThread.ready :
				if sockThread.data == 'over':
					print "You WON !"
					loop = False
					continue
				i, j, ii, jj = [int(c) for c in sockThread.data]
				sockThread.ready = False
				# if he lands on a king
				if board.board[ii][jj].startswith('k'):
					print "you are a pathetic loser..."
					sock.send("over")
					loop = False
				board.move(i,j, ii,jj)
				#reset clicked state 
				clickCell = None
				mpos = None
				turn = not turn
			
			pygame.display.update()
			time.sleep(0.01)
			continue

		# my turn
		loop, mpos , keys = events()
		if mpos :
			valid = False
			# already clicked, try to move
			if clickCell :
				cell = board.click(mpos)
				if cell :
					valid, pos = board.move(clickCell[0], clickCell[1], cell[0], cell[1])
			if valid :
				sock.send(''.join([str(e) for e in pos]))
				turn = not turn
			else :
				clickCell = board.click(mpos)
				if clickCell :
					piece = board.board[clickCell[0]][clickCell[1]]  
				else :
					piece = ''
				if piece == '':
					clickCell = None
				elif turn == WHITE :
					if board.board[clickCell[0]][clickCell[1]][1] != 'w':
						clickCell = None
				elif turn == BLACK :
					if board.board[clickCell[0]][clickCell[1]][1] != 'b':
						clickCell = None
		pygame.display.update()
		time.sleep(0.01)

	# EXITING
	try :
		print "exiting"
		sockThread.running = False
		sockThread.sock.close()
	except :
		pass
	pygame.quit()
	sys.exit()




def replay(argv):

	if len(argv) < 3 :
		print "missing replay file"
		sys.exit()
	 
	fic = open(argv[2], 'r')
	matchup = fic.readline()

	pygame.init()
	pygame.mixer.init()
	screen = pygame.display.set_mode((W,H))
	pygame.display.set_caption(matchup)
	sprite_board, sprite_pieces, sniper = loadData()
	# load moves
	moves = [[int(c) for c in l.split()] for l in fic]
	boards = [Board(sprite_pieces, sniper)]
	for m in moves :
		boards.append(boards[-1].copy())
		boards[-1].move(*m)

	turn = WHITE
	loop = True
	step = 0
	while loop:
		loop, _ , keys = events()
		# reset to initial state
		if 'SPACE' in keys :
			step = 0
			turn = WHITE
		# one step forward
		if 'RIGHT' in keys :
			step += 1
			turn = not turn
			if step >= len(boards):
				step = 0
				turn = WHITE
		# one step backward
		if 'LEFT' in keys :
			step -= 1
			if step < 0 :
				step = len(boards)-1
				if step % 2 == 0 :
					turn = WHITE
				else :
					turn = BLACK

		screen.fill(black)
		screen.blit(sprite_board, (0,0))
		boards[step].draw(screen, None, None)
		font = pygame.font.Font(None, 20)
		if turn :
			text = font.render("White", 1, (0, 0, 0))
		else :
			text = font.render("Black", 1, (0, 0, 0))
		screen.blit(text,(10, 10))

		pygame.display.update()
		time.sleep(0.01)

	# out of the game loop
	pygame.quit()
	sys.exit()








if __name__ == '__main__':
	if len(sys.argv) > 2 :
		if sys.argv[1] == '-p' :
			replay(sys.argv)

	networkGame(sys.argv)

	
