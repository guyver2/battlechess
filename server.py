import socket
import sys
import threading
import time
from communication import sendData, recvData, waitForMessage


class GameThread(threading.Thread):
	def __init__(self, client_1, client_2):
		super(GameThread, self).__init__()
		self.client_1 = client_1
		self.client_2 = client_2
		self.nick_1 = ""
		self.nick_2 = ""

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
				head, move = recvData(self.client_1)
				if head == "OVER" :
					loop = False
					continue
				i, j, ii, jj = move
				print "got move from", [i,j], "to", [ii,jj], "from white"
				log.write("%d %d %d %d\n"%(i,j,ii,jj))
				sendData(self.client_2, 'MOVE', move)

				head, move = recvData(self.client_2)
				if head == "OVER" :
					loop = False
					continue
				i, j, ii, jj = move
				print "got move from", [i,j], "to", [ii,jj], "from black"
				log.write("%d %d %d %d\n"%(i,j,ii,jj))
				sendData(self.client_1, 'MOVE', move)
		except :
			pass
		finally : # Always close the game
			print "finishing the game"
			sendData(self.client_1, 'OVER', None)
			sendData(self.client_2, 'OVER', None)
			self.client_1.close()
			self.client_2.close()
			log.close()
		

if __name__ == '__main__':
	
	PORT = 8887
	if len(sys.argv) == 1 :
		print "Usage:\n\t", sys.argv[0], "PORT"
	if len(sys.argv) == 2 :
		PORT = int(sys.argv[1])

	print " starting server on "+socket.gethostname()+":"+str(PORT)

	#create an INET, STREAMing socket
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind(('', PORT))
	#become a server socket
	serversocket.listen(5)
	loop = True
	while loop :
		try :
			#accept connections from outside
			(client_1, address) = serversocket.accept()
			print 'new client'
			sendData(client_1, 'COLR', 'white')
			(client_2, address) = serversocket.accept()
			sendData(client_2, 'COLR', 'black')
			print 'second client, ready to go'
			game = GameThread(client_1, client_2)
			game.start()
		except Exception as e:
			print e
			loop = False
			serversocket.close()
