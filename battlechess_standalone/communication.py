KNOWN_HEADERS = ["NICK", "COLR", "OVER", "URLR", "MOVE", "BORD", "VALD"]

# NICK : Nickname, data is a string
# COLR : Player color, data is a string
# OVER : Game is Over, data is None
# URLR : URL for the replay, data is a string
# MOVE : Player's move, data is a 4 int list (int from 0 to 7, so always 1 char)
# BORD : Game state, data is TO BE DETERMINED
# VALD : Confirmation from the server for a client's action, data is a boolean


# generic tow way conversion from raw data to string representation
def dataToString(header, data):
    if header in ["NICK", "COLR", "URLR", "BORD"]:
        return data
    elif header == "OVER":
        return "None"
    elif header == "MOVE":
        return str(data[0]) + str(data[1]) + str(data[2]) + str(data[3])
    elif header == "VALD":
        if data:
            return "T"
        else:
            return "F"
    else:
        print("Unknown message type :", header)
        raise ValueError()


# and from string to raw data
def stringToData(header, data):
    if header in ["NICK", "COLR", "URLR", "BORD"]:
        return data
    elif header == "OVER":
        return None
    elif header == "MOVE":
        return [int(data[0]), int(data[1]), int(data[2]), int(data[3])]
    elif header == "VALD":
        return data == "T"
    else:
        print("Unknown message type :", header)
        raise ValueError()


# generic receive function
def myreceive(sock, MSGLEN):
    msg = ""
    while len(msg) < MSGLEN:
        chunk = sock.recv(MSGLEN - len(msg))
        if chunk == "":
            raise RuntimeError("socket connection broken")
        msg = msg + chunk.decode("utf-8")
    return msg


# send an object over the network
def sendData(sock, header, data):
    pack = header
    datas = dataToString(header, data)
    pack += "%05d" % (len(datas))
    pack += datas
    # sock.send(pack)
    sock.send(pack.encode("utf-8"))
    if header not in KNOWN_HEADERS:
        print("Unknown message type :", header)


# receive a message and return the proper object
def recvData(sock):
    header = myreceive(sock, 4)
    size = int(myreceive(sock, 5))
    datas = myreceive(sock, size)
    data = stringToData(header, datas)
    if header not in KNOWN_HEADERS:
        print("Unknown message type :", header)
    return list([header, data])


# wait for a specific type of data and returns it
def waitForMessage(sock, header):
    head = None
    while head != header:
        head, data = recvData(sock)
    return dataToString(head, data)
