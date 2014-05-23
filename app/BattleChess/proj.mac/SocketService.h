//
//  Socket.h
//  SampleGame
//
//  Created by Pol Monso-Purti on 5/12/14.
//  Copyright (c) 2014 Bullets in a Burning Box, Inc. All rights reserved.
//

#ifndef __SampleGame__SocketService__
#define __SampleGame__SocketService__

#include <iostream>

#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/types.h>

#include "Packet.h"

#define MAX_BUF 1024
#define S_PORT  8887

class SocketService {
public:
    SocketService();
    int ssconnect(std::string host = "127.0.0.1", int port = 8887);
    int sswrite(std::string header, std::string data);
    int ssread(std::string headerStr, std::string& data);
    int ssrequest(std::string header, std::string data, std::string& reply);
    void ssdisconnect();
    int charArray2Int(const char sizeChar[5]);
    //TODO packet structure
    int readPacket(Packet& packet){return -1;};
    int writePacket(const Packet& packet){return -1;};
    int requestPacket(const Packet& requestPacket, Packet& replyPacket){return -1;};
    bool start();
    bool connectProtocol(std::string myName, std::string& color);
    bool waitInit(std::string& url, std::string& opponentName);

private:
    int _sockd;
    int _count;
    struct sockaddr_in _servName;
    int _status;
    char _buf[MAX_BUF];
    
#ifdef _WINDOWS_
    static DWORD WINAPI ssRequest(LPVOID lpParam);
#else // _WINDOWS_
    pthread_t m_thread;
    static void* ssRequest(void *data);
#endif // _WINDOWS_

};
#endif /* defined(__SampleGame__Socket__) */
