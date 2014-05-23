//
//  Socket.cpp
//  SampleGame
//
//  Created by Pol Monso-Purti on 5/12/14.
//  Copyright (c) 2014 Bullets in a Burning Box, Inc. All rights reserved.
//
#include <string.h>
#include <stdio.h>
#include <cstdio>
#include <unistd.h>
#include <stdlib.h>
#include <limits.h>
#include <errno.h>
#include <assert.h>
#include <sstream>

#include "cocos2d.h"

#if CC_TARGET_PLATFORM != CC_PLATFORM_WIN32
#include <pthread.h>
#endif

#include "SocketService.h"

pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

// get sockaddr, IPv4 or IPv6:
void *get_in_addr(struct sockaddr *sa)
{
    if (sa->sa_family == AF_INET) {
        return &(((struct sockaddr_in*)sa)->sin_addr);
    }
    
    return &(((struct sockaddr_in6*)sa)->sin6_addr);
}


SocketService::SocketService(){
    _sockd = socket(AF_INET, SOCK_STREAM, 0);
    if (_sockd < 0)
    {
        DEBUG2("Socket creation error: %s", strerror(errno));
    	//CCLog("Socket creation error");
        perror("Socket creation error");
        //FIXME might not be a good idea to finish this abruptly
        exit(-1);
    }
    _expectMsg = false;
    _terminate = false;
}

SocketService::~SocketService(){
    freeaddrinfo(servinfo); // all done with this structure
}

int SocketService::ssconnect(std::string host, int port){
    int rv;
    char s[INET6_ADDRSTRLEN];
    
    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    
    std::stringstream ss;
    ss << port;
    std::string portStr = ss.str();
    
    if ((rv = getaddrinfo(host.c_str(), portStr.c_str(), &hints, &servinfo)) != 0) {
        fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(rv));
        return -1;
    }
    
    // loop through all the results and connect to the first we can
    for(p = servinfo; p != NULL; p = p->ai_next) {
        if ((_sockd = socket(p->ai_family, p->ai_socktype,
                             p->ai_protocol)) == -1) {
            perror("client: socket");
            continue;
        }
        
        if (connect(_sockd, p->ai_addr, p->ai_addrlen) == -1) {
            close(_sockd);
            perror("client: connect");
            continue;
        }
        
        break;
    }
    
    if (p == NULL) {
        fprintf(stderr, "client: failed to connect\n");
        return -2;
    }
    
    inet_ntop(p->ai_family, get_in_addr((struct sockaddr *)p->ai_addr),
              s, sizeof s);
    printf("client: connecting to %s\n", s);
    fprintf(stderr,"Connected to %s:%d\n", host.c_str(), port);

    return 0;
}

void SocketService::ssdisconnect(){
    close(_sockd);
}

int SocketService::sswrite(std::string header, std::string data){
    
    int sizeInt = data.size();
    char sizeChArray[6];
    sprintf(sizeChArray, "%05d", sizeInt);
    sizeChArray[5] = '\0';
    std::string sizeStr = sizeChArray;
    std::string package = header + sizeChArray + data;
    int packageSize = 4 + 5 + sizeInt;
    assert(package.size() == packageSize);
    int ret = send(_sockd, package.c_str(), packageSize*sizeof(char), 0);
    if( ret < 0){
        DEBUG2("package send error");
        return ret;
    }
    return ret;
}

int SocketService::ssread(std::string& header, std::string& data){
    
    char headerChArray[4];
    char sizeChArray[5];
    //read header
    int ret = recv(_sockd, headerChArray, 4*sizeof(char), MSG_WAITALL);
    if( ret == -1){
        DEBUG2("Read error");
        return ret;
    }
    
    //read size
    ret = recv(_sockd, sizeChArray, 5*sizeof(char), MSG_WAITALL);
    if( ret == -1){
        DEBUG2("Read error");
        return ret;
    }
    
    int size = charArray2Int(sizeChArray);
    
    ret = recv(_sockd, _buf, size*sizeof(char), MSG_WAITALL	);
    if( ret == -1){
        DEBUG2("Read error");
        return ret;
    }
    _buf[size*sizeof(char)] = '\0';
    
    data = _buf;
    char headerChString[5];
    memcpy(headerChString, headerChArray, 4*sizeof(char));
    headerChString[4] = '\0';
    header = headerChString;
    cocos2d::CCLog("packet received%s|%d|%s", header.c_str(), size, data.c_str());
    DEBUG2("packet received: %s|%d|%s", header.c_str(), size, data.c_str());
    return ret;
}

int SocketService::charArray2Int(const char input[5]){
    char *endptr;
    errno = 0;
    char array[6];
    memcpy(array, input, 5*sizeof(char));
    array[5] = '\0';

    long n = strtol (array, &endptr, 10);
    switch (errno) {
            
        case ERANGE:
            switch (n) {
                case LONG_MIN:
                    DEBUG2("UNDERFLOW");
                    break;
                case LONG_MAX:
                    DEBUG2("OVERFLOW");
                    break;
                default:
                    assert(!"ERANGE with invalid return value!?");
                    break;
            }
            break;
            
        case 0:
            if (endptr == input) {
                DEBUG2("Invalid input; no conversion took place");
            } else if (*endptr == '\0') {
            }else {
                DEBUG2("Successful conversion with possible garbage at end of input: >>%s<<\n", endptr);
            }
            break;

        case EINVAL:
            perror("Invalid value");
            DEBUG2("Invalid data received: %s",array);
            //assert(!"Invalid input.");
            break;
        default:
            perror("Invalid errno");
            DEBUG2("Input received: %s",array);
            assert(!"Invalid errno!?");
            n=0;
            break;
    }
    return (int) n;
}

int SocketService::ssrequest(std::string header, std::string data, std::string& replyHeader, std::string& reply){
    bool ret = sswrite(header, data);
    std::string headerStr;
    if(ret < 0)
        return ret;
    ssread(headerStr, reply);
    return ret;
}

bool SocketService::connectProtocol(std::string myName, std::string& color){
    
    std::string headerStr;
    DEBUG2("read packet ");
    ssread(headerStr, color);
    fprintf(stderr,"I'll be player %s\n", color.c_str());
    headerStr = "NICK";
    sswrite(headerStr, myName);
    return true;
}

bool SocketService::waitInit(std::string& url, std::string& opponentName){
    std::string headerStr;
    ssread(headerStr, url);
    DEBUG2("fetched url %s", url.c_str());
    ssread(headerStr, opponentName);
    fprintf(stderr, "Playing against %s\n", opponentName.c_str());
    return true;
}

bool SocketService::sendMove(int originI, int originJ, int destI, int destJ){
    std::string validHeader, validReply;
    std::string header = "MOVE";
    std::stringstream sstm;
    sstm << originI << originJ << destI << destJ;
    std::string moveData = sstm.str();
    ssrequest(header, moveData, validHeader, validReply);
    if(validReply == "T")
        return true;
    else if(validReply == "F")
        return false;
    else {
        DEBUG2("Unrecognized valid reply. Aborting.");
        return false;
    }
}

//multithreading
void SocketService::sendPacket(const Packet &packet){
    sswrite(packet.header, packet.body);
}

bool SocketService::getPacket(Packet& packet){
    
    //FIXME windows mutex protect this
    int size = _recvQueue.size();
    if(_recvQueue.empty()){
        return false;
    }
#ifdef _WINDOWS_
    packet = _recvQueue.front();
    _recvQueue.pop();
#else
    pthread_mutex_lock(&mutex);
    packet = _recvQueue.front();
    _recvQueue.pop();
    pthread_mutex_unlock(&mutex);
#endif
     return true;
}

bool SocketService::start(){
    
#ifdef _WINDOWS_
    CreateThread(NULL,          // default security attributes
                 0,             // use default stack size
                 ssRequest,   // thread function name
                 this,          // argument to thread function
                 0,             // use default creation flags
                 NULL);
#else
    pthread_create(&m_thread, NULL, ssRequest, this);
    pthread_detach(m_thread);
#endif

    return true;
}


#ifdef _WINDOWS_
DWORD WINAPI SocketService::ssRequest(LPVOID lpParam)
{
    SocketService* instance = (SocketService*)lpParam;
    return 0;
}

#else // _WINDOWS_

void* SocketService::ssRequest(void *data)
{
    SocketService* instance = (SocketService*)data;

    //TODO possible race condition here waiting message before writing request
    //if the first thread added packet and changed waitingMsg while the thread
    //was on the 2nd if, about to check waitingMsg
    while(!instance->_terminate){
        
            Packet packet;
            //TODO put a timeout
            if(instance->ssread(packet.header, packet.body)){
                
                //FIXME with espera activa/mutex, quick patch
                if(packet.header == "OVER")
                    instance->_terminate = true;
                
                #ifdef _WINDOWS_
                instance->_recvQueue.push(packet);
                #else
                pthread_mutex_lock(&mutex);
                instance->_recvQueue.push(packet);
                pthread_mutex_unlock(&mutex);
                #endif
            }else{
                //error
                DEBUG2("socket read error");
            }
        
        
    }
    DEBUG2("socket service thread terminating");
    return NULL;
}
#endif // _WINDOWS_
