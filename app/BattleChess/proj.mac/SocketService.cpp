//
//  Socket.cpp
//  SampleGame
//
//  Created by Pol Monso-Purti on 5/12/14.
//  Copyright (c) 2014 Bullets in a Burning Box, Inc. All rights reserved.
//


#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <stdlib.h>
#include <stdio.h>
#include <limits.h>
#include <errno.h>
#include <assert.h>

#if CC_TARGET_PLATFORM != CC_PLATFORM_WIN32
#include <pthread.h>
#endif

#include "SocketService.h"
#define DEBUG 1

#define DEBUG2(...) \
do { if (DEBUG){  fprintf(stderr, "\n"); fprintf(stderr, __VA_ARGS__); \
fprintf(stderr, " [%s:%d:%s()]\n", __FILE__, __LINE__, __func__); }} while (0)

SocketService::SocketService(){
    _sockd = socket(AF_INET, SOCK_STREAM, 0);
    if (_sockd < 0)
    {
        DEBUG2("Socket creation error");
        exit(-1);
    }
}

int SocketService::ssconnect(std::string host, int port){
    
    // server address //
    _servName.sin_family = AF_INET;
    inet_pton(AF_INET, host.c_str(), &_servName.sin_addr);
    _servName.sin_port = htons(port);
    
    fprintf(stderr,"Connect to  %s:%d\n", host.c_str(), port);
    // connect to the server //
    _status = connect(_sockd, (struct sockaddr*)&_servName, sizeof(struct sockaddr));
    if (_status < 0)
    {
        DEBUG2("Connection error");
        return _status;
    }
    return _status;
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

int SocketService::ssread(std::string headerStr, std::string& data){
    
    char header[4];
    char sizeChArray[5];
    //read header
    int ret = recv(_sockd, header, 4*sizeof(char), 0);
    if( ret == -1){
        DEBUG2("Read error");
        return ret;
    }
    
    //read size
    ret = recv(_sockd, sizeChArray, 5*sizeof(char), 0);
    if( ret == -1){
        DEBUG2("Read error");
        return ret;
    }
    
    int size = charArray2Int(sizeChArray);
    
    ret = recv(_sockd, _buf, size*sizeof(char), 0);
    if( ret == -1){
        DEBUG2("Read error");
        return ret;
    }
    _buf[size*sizeof(char)] = '\0';
    
    data = _buf;
    char headerChArray[5];
    memcpy(headerChArray, header, 4*sizeof(char));
    headerChArray[4] = '\0';
    headerStr = headerChArray;
    DEBUG2("packet received: %s|%d|%s", headerStr.c_str(), size, data.c_str());
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
                DEBUG2("chArr2int ok");
            }else {
                printf("Successful conversion with possible garbage at end of input: >>%s<<\n", endptr);
            }
            break;

        case EINVAL:
            perror("Invalid value");
            DEBUG2("Invalid data received: %s",array);
            assert(!"Invalid input.");
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

int SocketService::ssrequest(std::string header, std::string data, std::string& reply){
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
    return NULL;
}
#endif // _WINDOWS_
