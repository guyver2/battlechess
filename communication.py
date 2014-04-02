import socket
import cPickle 


KNOWN_HEADERS = ['NICK', 'COLR', 'OVER', 'URLR', 'MOVE', 'BORD', 'VALD']

# generic receive function
def myreceive(sock, MSGLEN):
	msg = ''
	while len(msg) < MSGLEN:
		chunk = sock.recv(MSGLEN-len(msg))
		if chunk == '':
			raise RuntimeError("socket connection broken")
		msg = msg + chunk
	return msg

# send an object over the network
def sendData(sock, header, data):
	pack  = header
	datas = cPickle.dumps(data)
	pack += "%05d"%(len(datas))
	pack += datas
	sock.send(pack)
	if header not in KNOWN_HEADERS :
		print 'Unknown message type :', header

# recieve a message and return the proper object
def recvData(sock):
	header = myreceive(sock, 4)
	size   = int(myreceive(sock, 5))
	msg    = myreceive(sock, size)
	data   = cPickle.loads(msg)
	if header not in KNOWN_HEADERS :
		print 'Unknown message type :', header
	return list([header, data])

# wait for a specific type of data and returns it
def waitForMessage(sock, header):
	head = None
	while head != header:
		head, data = recvData(sock)
	return data 




















