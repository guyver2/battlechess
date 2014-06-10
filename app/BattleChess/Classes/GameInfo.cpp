//
//  GameInfo.cpp
//  SimpleGame
//
//  Created by Pol Monso-Purti on 5/15/14.
//
//

#include "cocos2d.h"
#include "GameInfo.h"

const std::string GameInfo::WHITE = "white";
const std::string GameInfo::BLACK = "black";

GameInfo::GameInfo(){
    
    playerName = getUsername();
    opponentName = "unknown";
    gameUrl = "http://sxbn.org";
    playerColor = 'n';
    opponentColor = 'n';
}

GameInfo::GameInfo(std::string playerName, std::string opponentName, std::string gameUrl, std::string color){
    this->playerName = playerName;
    this->opponentName = opponentName;
    this->gameUrl = gameUrl;
    setPlayerColor(color);
}

std::string GameInfo::getUsername(){
    struct cocos2d::cc_timeval startTime;
    cocos2d::CCTime::gettimeofdayCocos2d(&startTime, NULL);
    std::stringstream ss;
    ss << "anon_" << startTime.tv_sec;
    std::string randUser = ss.str();
    CCLOG("random username: %s", randUser.c_str());
    std::string name = cocos2d::CCUserDefault::sharedUserDefault()->getStringForKey("username", randUser);
    
    if(name == randUser)
        CCLOG("Nothing is stored, we will store the randUser %s", randUser.c_str());

    cocos2d::CCUserDefault::sharedUserDefault()->setStringForKey("username", name.c_str());
    CCLOG("Stored username: %s", name.c_str());
    return name;
}

void GameInfo::setPlayerColor(std::string myColor){
    if(myColor == GameInfo::WHITE){
        this->playerColor = 'w';
        this->opponentColor = 'b';
    } else {
        this->playerColor = 'b';
        this->opponentColor = 'w';
    }
}
