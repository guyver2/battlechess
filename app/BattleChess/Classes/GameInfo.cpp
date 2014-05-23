//
//  GameInfo.cpp
//  SimpleGame
//
//  Created by Pol Monso-Purti on 5/15/14.
//
//

#include "GameInfo.h"

const std::string GameInfo::WHITE = "white";
const std::string GameInfo::BLACK = "black";

GameInfo::GameInfo(std::string playerName, std::string opponentName, std::string gameUrl, std::string color){
    this->playerName = playerName;
    this->opponentName = opponentName;
    this->gameUrl = gameUrl;
    if(color == GameInfo::WHITE)
        this->playerColor = 'w';
    else
        this->playerColor = 'b';
}