//
//  Packet.h
//  SampleGame
//
//  Created by Pol Monso-Purti on 5/14/14.
//  Copyright (c) 2014 Bullets in a Burning Box, Inc. All rights reserved.
//

#ifndef __SampleGame__Packet__
#define __SampleGame__Packet__

#include <iostream>
#include <sstream> 

#define SIZENUMCHARS 5
#define HEADERNUMCHARS 4

class Packet {
public:
    char header[HEADERNUMCHARS];
    char sizeChArray[SIZENUMCHARS];
    int sizeInt;
    std::string data;
    
    Packet(const char header[HEADERNUMCHARS], const char sizeChArray[SIZENUMCHARS], std::string data){
        memcpy(this->header, header, HEADERNUMCHARS*sizeof(char));
        memcpy(this->sizeChArray, sizeChArray, SIZENUMCHARS*sizeof(char));
        this->data = data;
        
        copySizeCharArrayToInt();
        
    }
    
    int copySizeCharArrayToInt(){
        std::string sizeStr(sizeChArray);
        std::stringstream sstr(sizeStr);
        int x;
        sstr >> x;
        if (!sstr)
        {
            fprintf(stderr, "The conversion from char array to int failed.");
        }
        return x;
    }
    
};

#endif /* defined(__SampleGame__Packet__) */
