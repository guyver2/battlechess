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
#include <stdio.h>

#include <vector>
#include <queue>

#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/types.h>

#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <sys/wait.h>
#include <signal.h>

//#include "CCHttpRequest.h"
//#include "CCNetwork.h"

#ifdef _WINDOWS_
#else
//TODO find out how to protect queues...
//#include <mutex>
#endif

#include "constants.h"

#define MAX_BUF 1024
#define S_PORT  8887

class Packet {
public:
    std::string header;
    std::string body;

    Packet(){};
    Packet(std::string header, std::string body){
        this->header = header;
        this->body = body;
    }

};

class SocketService {
public:
    SocketService();
    ~SocketService();
    int ssconnect(std::string host = "localhost", int port = 8887);
    int sswrite(std::string header, std::string data);
    int ssread(std::string& header, std::string& data);
    int ssrequest(std::string header, std::string data, std::string& replyHeader, std::string& reply);
    void ssdisconnect();
    int charArray2Int(const char sizeChar[5]);
    //TODO packet structure
    bool start();
    void ssshutdown();
    void ssclose();
    
    
    bool connectProtocol(std::string myName, std::string& color);
    bool waitInit(std::string& url, std::string& opponentName);
    bool sendMove(int originI, int originJ, int destI, int destJ);

    //replay
    void openUrl(const std::string& url, std::string& content);
    void fetchMoves(std::string url, std::vector<std::string> moves);
    
    //multithreading
    void sendPacket(const Packet& packet);
    bool getPacket(Packet &packet);
    //TODO protect with mutex
    bool _expectMsg;
    bool _terminate;
    
    std::string _host;
    int _port;
    
private:
    int _sockd;
    int _count;
    struct addrinfo hints, *servinfo, *p;
    char _buf[MAX_BUF];

    //multhreading
    //TODO protect this thread-wise
    std::queue<Packet> _recvQueue;
    std::queue<Packet> _sendQueue;
    
#ifdef _WINDOWS_
    static DWORD WINAPI ssRequest(LPVOID lpParam);
#else // _WINDOWS_
//    Mutex mutex;
    pthread_t m_thread;
    static void* ssRequest(void *data);
#endif // _WINDOWS_

};
#endif /* defined(__SampleGame__Socket__) */
