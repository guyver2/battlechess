import socket
import sys
import threading
import time


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


class GameThread(threading.Thread):
	def __init__(self, client_1, client_2):
		super(GameThread, self).__init__()
		self.client_1 = client_1
		self.client_2 = client_2
		self.nick_1 = ""
		self.nick_2 = ""

	def run(self):
		self.nick_1 = receiveN(self.client_1)
		self.nick_2 = receiveN(self.client_2)
		filename = time.strftime("games/%Y_%m_%d_%H_%M_%S")
		filename += "_"+self.nick_1+"_Vs_"+self.nick_2+".txt"
		log = open(filename, "w")
		log.write(self.nick_1+' Vs. '+self.nick_2+'\n')
		
		sendN(client_1, "http://git.sxbn.org/battleChess/"+filename)
		sendN(client_2, "http://git.sxbn.org/battleChess/"+filename)
		self.client_1.send("ready")
		self.client_2.send("ready")

		sendN(self.client_1, self.nick_2)
		sendN(self.client_2, self.nick_1)


		loop = True
		try :
			while loop:
				move = myreceive(self.client_1, 4)
				if move == "over" :
					loop = False
					continue
				i, j, ii, jj = [int(c) for c in move]
				#print "got move from", [i,j], "to", [ii,jj], "from white"
				log.write("%d %d %d %d\n"%(i,j,ii,jj))
				self.client_2.send(move)

				move = myreceive(self.client_2, 4)
				if move == "over" :
					loop = False
					continue
				i, j, ii, jj = [int(c) for c in move]
				#print "got move from", [i,j], "to", [ii,jj], "from black"
				log.write("%d %d %d %d\n"%(i,j,ii,jj))
				self.client_1.send(move)
		except :
			pass
		finally :
			#print "finishing the game"
			self.client_1.send("over")
			#sendN(client_1, "http://git.sxbn.org/battleChess/"+filename)
			self.client_2.send("over")
			#sendN(client_1, "http://git.sxbn.org/battleChess/"+filename)
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
			client_1.send("white")
			(client_2, address) = serversocket.accept()
			client_2.send("black")

			game = GameThread(client_1, client_2)
			game.start()
		except :
			loop = False
			serversocket.close()
