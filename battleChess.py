#!/usr/bin/python

# proublyd brought to you by Antoine Letouzey and Pol Monso !

import pygame
import sys
import time
import socket
import threading
import random
import urllib
from core.Board import Board
from pygame.locals import *
from communication import sendData, recvData, waitForMessage

# GLOBAL VARIABLES
W, H = 512, 384  # wibndow prop
black = (0, 0, 0, 255)  # background
WHITE, BLACK = True, False  # players

#  --------------------------


class BoardPlayer(Board):
    def __init__(self, sprite_pieces, sprite_board, sniper):
        super(BoardPlayer, self).__init__()
        self.sprite_pieces = sprite_pieces
        self.sprite_board = sprite_board
        self.sniper = sniper
        self.visibility = None

    def copy(self):
        board = super(BoardPlayer, self).copy()
        res = BoardPlayer(self.sprite_pieces, self.sprite_board, self.sniper)
        res.updateFromBoard(board)
        return res

    def draw(self, screen, selected=None, turn=None):
        screen.blit(self.sprite_board, (0,0))
        for i in range(8):
            for j in range(8):
                c = self.board[i][j]
                if c == '':
                    continue
                else:
                    dx = 0
                    dy = 0
                    if c[1] == 'b':
                        dx += 72
                    if c[0] in ['n', 'r', 'b']:
                        dx += 36
                    if c[0] in ['q', 'r']:
                        dy += 36
                    if c[0] in ['p', 'b']:
                        dy += 72
                    patch_rect = (dx, dy, 36, 36)
                    screen.blit(self.sprite_pieces, (104+j*40, 30+i*40), patch_rect)
        if turn is not None:
            self.visibility = [[False for i in range(8)] for j in range(8)]
            # get white piece
            color = 'b'
            if turn:
                color = 'w'
            for i in range(8):
                for j in range(8):
                    if self.board[i][j].endswith(color):
                        for di in range(-1,2):
                            for dj in range(-1,2):
                                if self.isIn(i+di, j+dj):
                                    self.visibility[i+di][j+dj] = True
            fog = pygame.Surface((38, 38))
            fog.set_alpha(150)
            fog.fill((0, 0, 0))
            for i in range(8):
                for j in range(8):
                    if not self.visibility[i][j]:
                        screen.blit(fog, (105+j*40, 30+i*40))
        # draw possible displacement positions    
        s = pygame.Surface((34, 34))
        s.set_alpha(128)
        s.fill((255, 0, 255))
        if selected:
            pos = self.getPossiblePosition(selected[0], selected[1])
            for p in pos:
                screen.blit(s, (106+p[1]*40, 30+p[0]*40))
        # draw taken pieces
        # white
        for i, p in enumerate([p for p in self.taken if p[1] == 'w']):
            dx = 0
            dy = 0
            if p[0] in ['n', 'r', 'b']:
                dx += 36
            if p[0] in ['q', 'r']:
                dy += 36
            if p[0] in ['p', 'b']:
                dy += 72
            patch_rect = (dx, dy, 36, 36)
            screen.blit(self.sprite_pieces, (6+(i % 2)*40, 20+(i/2)*40), patch_rect)
        for i, p in enumerate([p for p in self.taken if p[1] == 'b']):
            dx = 72
            dy = 0
            if p[0] in ['n', 'r', 'b']:
                dx += 36
            if p[0] in ['q', 'r']:
                dy += 36
            if p[0] in ['p', 'b']:
                dy += 72
            patch_rect = (dx, dy, 36, 36)
            screen.blit(self.sprite_pieces, (426+(i % 2)*40, 338-(i/2)*40), patch_rect)

    def click(self, pos):
        i = int((pos[1]-30) / 40)
        j = int((pos[0]-106) / 40)
        if self.isIn(i, j):
            return [i, j]
        return None

# ****************************************************************************


def loadData():
    sprite_board = pygame.image.load('data/board.png').convert(24)
    sprite_pieces = pygame.image.load('data/pieces.png')
    # sprite_pieces.set_colorkey((255,0,255)) # for non-transparent png, chroma-keying
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


class SockThread(threading.Thread):
    def __init__(self, sock):
        super(SockThread, self).__init__()
        self.sock = sock
        self.sock.settimeout(0.1)
        self.ready = False
        self.data = None
        self.header = None
        self.running = True

    # wait for a given message
    def waitForMessage(self, header):
        while self.running:
            if self.ready:
                if self.header == 'OVER':
                    return [False, 'OVER', None]
                if self.header == header:
                    head, data = self.getDataAndRelease()
                    return [True, head, data] # object is there, ready to be read
                else:  # JUNK
                    print('got', self.header, 'instead of', header, ', still waiting')
                    self.getDataAndRelease()
            else:  # don't check too much
                time.sleep(0.01)
        return [False, 'OVER', None] # if thread stoped in the meantime

    # unary copy of the data and release the socket to make it ready to read more data
    def getDataAndRelease(self):
        head = str(self.header)
        data = self.data
        self.ready = False
        return list([head, data])

    def run(self):
        while self.running:
            if not self.ready:
                try:
                    self.header, self.data = recvData(self.sock)
                    if self.header == 'OVER':
                        self.running = False
                    self.ready = True
                except Exception as e:
                    #print("GOT EXCEPTION IN MAIN LOOP")
                    #print(e)
                    pass
            time.sleep(0.01)
        self.sock.close()


class ConnectionThread(threading.Thread):
    def __init__(self, host, port, nick):
        super(ConnectionThread, self).__init__()
        self.host = host
        self.port = port
        self.nick = nick
        self.opponent = None
        self.localPlayer = None
        self.sock = None
        self.done = False
        self.running = True
        self.replayURL = None

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.sock.settimeout(0.01)
        #create socket and connect
        print('connecting to' , (self.host, self.port))
        self.sock.connect((self.host, self.port))
        # get player color
        msg = waitForMessage(self.sock, 'COLR')
        print("I'll be player ", msg)
        if msg == "white":
            self.localPlayer = WHITE
        else:
            self.localPlayer = BLACK
        # send nickname
        sendData(self.sock, 'NICK', self.nick)

        # get replay filename
        self.replayURL = waitForMessage(self.sock, 'URLR')
        print("Game replay at:", self.replayURL)

        # get his nickname
        self.opponent = waitForMessage(self.sock, 'NICK')
        print("Playing against", self.opponent)

        self.done = True
        while self.running:
            time.sleep(0.1)
        
        # return [sock, sockThread, localPlayer]

# ****************************************************************************


def mainGameState(screen, localPlayer, sockThread, sock, board):

    clickCell = None
    turn = WHITE
    loop = True
    winner = None
    font = pygame.font.Font(None, 20)
    while loop:
        screen.fill(black)
        board.draw(screen, clickCell, localPlayer)
        if turn:
            text = font.render("White", 1, (0, 0, 0))
        else:
            text = font.render("Black", 1, (0, 0, 0))
        screen.blit(text, (10, 10))
        # other player's turn:
        if turn != localPlayer:
            loop, _ , _ = events() # grab events and throw them away:)
            if sockThread.ready:
                if sockThread.header == 'OVER':
                    winner = localPlayer
                    loop = False
                    continue
                elif sockThread.header != 'BORD':
                    print('got', sockThread.header, 'instead of BORD, still waiting')
                    sockThread.ready = False
                    continue
                else:
                    newBoard = sockThread.data
                    board.updateFromString(newBoard)
                    sockThread.ready = False
                # reset clicked state
                clickCell = None
                mpos = None
                turn = not turn

            pygame.display.update()
            time.sleep(0.01)
            # continue
        else:
            # my turn
            loop, mpos, _keys = events()
            if mpos:
                valid = False
                # already clicked, try to move
                if clickCell:
                    cell = board.click(mpos)
                    if cell:
                        sendData(sock, 'MOVE', [clickCell[0], clickCell[1], cell[0], cell[1]])
                        loop, header, valid = sockThread.waitForMessage('VALD')
                if valid:
                    loop, header, newBoard = sockThread.waitForMessage('BORD')
                    if loop:
                        board.updateFromString(newBoard)
                        turn = not turn
                else:
                    clickCell = board.click(mpos)
                    if clickCell:
                        piece = board.board[clickCell[0]][clickCell[1]]
                    else:
                        piece = ''
                    if piece == '':
                        clickCell = None
                    elif turn == WHITE:
                        if board.board[clickCell[0]][clickCell[1]][1] != 'w':
                            clickCell = None
                    elif turn == BLACK:
                        if board.board[clickCell[0]][clickCell[1]][1] != 'b':
                            clickCell = None

        # check wether we have a winner
        if board.winner:
            if board.winner == 'w':
                winner = WHITE
            else:
                winner = BLACK
            loop = False

        pygame.display.update()
        time.sleep(0.01)

    return winner


# prevents abrupt ending by displaying the complete board
def endGameState(screen, winner, localPlayer, board):
    replay_sprite = pygame.image.load('data/replay.png').convert(24)
    newGame_sprite = pygame.image.load('data/new_game.png').convert(24)
    loop = True
    font = pygame.font.Font(None, 50)
    while loop:
        loop, mpos , _ = events()

        if mpos:
            x, y = mpos
            if x>50 and x<206 and y>288 and y<338:
                print('r')
                return 'r'
            elif x>306 and x<462 and y>288 and y<338:
                print('new game')
                return 'g' 
        screen.fill(black)
        board.draw(screen, None, None)
        if winner == localPlayer:
            text = font.render("You WON !", 1, (255, 0, 0))
        else:
            text = font.render("You lose...", 1, (255, 0, 0))
        screen.blit(text,(int(W/2.-text.get_width()/2.), int(H/2.-text.get_height()/2.)))
        screen.blit(replay_sprite,(50, 3*H/4))
        screen.blit(newGame_sprite,(306, 3*H/4))
        pygame.display.update()
        time.sleep(0.01)
    return 'n' # nothing

# intro state waiting for opponenent
def introGameState(screen, board, connectionThread = None):
    loop = True
    t0 = time.time()
    font = pygame.font.Font(None, 50)
    text = font.render("Waiting for opponent . .", 1, (255, 0, 0))
    posMess = (int(W/2.-text.get_width()/2.), int(H/2.-text.get_height()/2.))
    while not connectionThread.done and loop:
        loop, _ , _ = events()
        screen.fill(black)
        board.draw(screen, None, None)
        message = "Waiting for opponent "+'. '*(int(2*time.time()-2*t0) % 4)
        text = font.render(message, 1, (255, 0, 0))
        screen.blit(text, posMess)
        pygame.display.update()
        time.sleep(0.01)

    return loop



# regular two player game over network
def networkGame(argv, screen, sprite_board, sprite_pieces, sniper):

    board = BoardPlayer(sprite_pieces, sprite_board, sniper)

    PORT = 8887
    HOST = "sxbn.org"  
    NICK = "anon_%d"%(random.randint(0,100))
    if len(argv) == 1:
        print("Usage:\n\t", argv[0], "NICKNAME HOST PORT")
    if len(argv) > 1:
        NICK = argv[1].replace(' ', '_')
    if len(argv) > 2:
        HOST = argv[2]
    if len(argv) > 3:
        PORT = int(argv[3])

    print("connecting to", HOST+":"+str(PORT))


    
    localPlayer = None
    connectionThread = ConnectionThread(HOST, PORT, NICK)
    connectionThread.start()

    # MAIN GAME LOOP
    # TODO: FIND A WAY TO KILL THE CONNECTION THREAD IN CASE OF EARLY EXIT
    loop = introGameState(screen, board, connectionThread)

    # get info from connection Thread
    opponent = connectionThread.opponent
    localPlayer = connectionThread.localPlayer
    sock = connectionThread.sock
    url = connectionThread.replayURL
    connectionThread.running = False
    connectionThread.join()
    
    pygame.display.set_caption(NICK+" Vs. "+opponent)
    sockThread = SockThread(sock)
    sockThread.start()
    

    winner = mainGameState(screen, localPlayer, sockThread, sock, board)
    whatNext = endGameState(screen, winner, localPlayer, board)

    # EXITING
    try:
        print("exiting")
        sockThread.running = False
        sockThread.sock.close()
    except:
        pass

    if whatNext == 'r':
        replay(url, screen, sprite_board, sprite_pieces, sniper)
    elif whatNext == 'g':
        networkGame(argv, screen, sprite_board, sprite_pieces, sniper)






def replay(url, screen, sprite_board, sprite_pieces, sniper):
    
    fic = urllib.urlopen(url)
    matchup = fic.readline()
    pygame.display.set_caption(matchup)

    # load moves
    moves = [[int(c) for c in l.split()] for l in fic]
    boards = [BoardPlayer(sprite_pieces, sprite_board, sniper)]
    for m in moves:
        boards.append(boards[-1].copy())
        boards[-1].move(*m)

    turn = WHITE
    loop = True
    step = 0
    while loop:
        loop, _ , keys = events()
        # reset to initial state
        if 'SPACE' in keys:
            step = 0
            turn = WHITE
        # one step forward
        if 'RIGHT' in keys:
            step += 1
            turn = not turn
            if step >= len(boards):
                step = 0
                turn = WHITE
        # one step backward
        if 'LEFT' in keys:
            step -= 1
            if step < 0:
                step = len(boards)-1
                if step % 2 == 0:
                    turn = WHITE
                else:
                    turn = BLACK

        screen.fill(black)
        screen.blit(sprite_board, (0,0))
        boards[step].draw(screen, None, turn)
        font = pygame.font.Font(None, 20)
        if turn:
            text = font.render("White", 1, (0, 0, 0))
        else:
            text = font.render("Black", 1, (0, 0, 0))
        screen.blit(text,(10, 10))

        pygame.display.update()
        time.sleep(0.01)

    # out of the game loop








if __name__ == '__main__':

    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((W,H))
    sprite_board, sprite_pieces, sniper = loadData()
    

    if len(sys.argv) > 2:
        if sys.argv[1] == '-p':
            if len(sys.argv) < 3:
                print("missing replay file")
                sys.exit()
            replay(sys.argv[2], screen, sprite_board, sprite_pieces, sniper)
            pygame.quit()
            sys.exit()


    networkGame(sys.argv, screen, sprite_board, sprite_pieces, sniper)
    pygame.quit()
    sys.exit()
    
