#!/usr/bin/python

import socket
import sys, traceback
import signal
import threading
import time
from Board import Board
from communication import sendData, recvData, waitForMessage


class GameThread(threading.Thread):
	def __init__(self, client_1, client_2):
		super(GameThread, self).__init__()
		self.client_1 = client_1
		self.client_2 = client_2
		self.nick_1 = ""
		self.nick_2 = ""
		self.board = Board()

	def run(self):
		self.nick_1 = waitForMessage(self.client_1, 'NICK')
		self.nick_2 = waitForMessage(self.client_2, 'NICK')
		filename = time.strftime("games/%Y_%m_%d_%H_%M_%S")
		filename += "_"+self.nick_1+"_Vs_"+self.nick_2+".txt"
		log = open(filename, "w")
		log.write(self.nick_1+' Vs. '+self.nick_2+'\n')
		
		sendData(self.client_1, 'URLR', "http://git.sxbn.org/battleChess/"+filename)
		sendData(self.client_2, 'URLR', "http://git.sxbn.org/battleChess/"+filename)


		sendData(self.client_1, 'NICK', self.nick_2)
		sendData(self.client_2, 'NICK', self.nick_1)


		loop = True
		try :
			while loop:
				valid = False
				while not valid :
					head, move = recvData(self.client_1)
					if head == "OVER" :
						loop = False
						raise # jump to finaly
					elif head == 'MOVE':
						i, j, ii, jj = move
						valid, pos = self.board.move(i,j,ii,jj)
						#print "got move from", [i,j], "to", [ii,jj], "from white", valid
						sendData(self.client_1, 'VALD', valid)
					else :
						print 'error : server was expecting MOVE, not', head
						raise 

				log.write("%d %d %d %d\n"%(i,j,ii,jj))
				if self.board.winner : # if we have a winner, send the whole board
					endBoard = self.board.toString()
					sendData(self.client_1, 'BORD', endBoard)
					sendData(self.client_2, 'BORD', endBoard)
					break # game is over
				else :
					sendData(self.client_1, 'BORD', self.board.toString('w'))
					sendData(self.client_2, 'BORD', self.board.toString('b'))

				valid = False
				while not valid :
					head, move = recvData(self.client_2)
					if head == "OVER" :
						loop = False
						raise # jump to finaly
					elif head == 'MOVE':
						i, j, ii, jj = move
						valid, pos = self.board.move(i,j,ii,jj)
						#print "got move from", [i,j], "to", [ii,jj], "from black", valid
						sendData(self.client_2, 'VALD', valid)
					else :
						print 'error : server was expecting MOVE, not', head
						raise 	

				log.write("%d %d %d %d\n"%(i,j,ii,jj))
				if self.board.winner : # if we have awinner, send the whole board
					endBoard = self.board.toString()
					sendData(self.client_1, 'BORD', endBoard)
					sendData(self.client_2, 'BORD', endBoard)
					break # game is over
				else :
					sendData(self.client_1, 'BORD', self.board.toString('w'))
					sendData(self.client_2, 'BORD', self.board.toString('b'))
		except Exception as e:
			#print e
			#traceback.print_exc(file=sys.stdout)
			pass
		finally : # Always close the game
			#print "finishing the game"
			log.flush()
			log.close()
			sendData(self.client_1, 'OVER', None)
			sendData(self.client_2, 'OVER', None)
			self.client_1.close()
			self.client_2.close()




if __name__ == '__main__':
	PORT = 8887
	HOST = '' # default value
	if len(sys.argv) == 1 :
		print "Usage:\n\t", sys.argv[0], "PORT"
	if len(sys.argv) > 1 :
		PORT = int(sys.argv[1])
	if len(sys.argv) > 2 :
		HOST = sys.argv[2]
	
	#print " starting server on "+socket.gethostname()+":"+str(PORT)

	#create an INET, STREAMing socket
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind((HOST, PORT))

	# register SIGINT to close socket
	def signal_handler(signal, frame):
		print('You pressed Ctrl+C!')
		serversocket.close()
		sys.exit(0)


	#become a server socket
	serversocket.listen(5)
	loop = True
	while loop :
		try :
			#accept connections from outside
			(client_1, address) = serversocket.accept()
			sendData(client_1, 'COLR', 'white')
			(client_2, address) = serversocket.accept()
			sendData(client_2, 'COLR', 'black')
			game = GameThread(client_1, client_2)
			game.start()
		except Exception as e:
			print e
			loop = False
			serversocket.close()
