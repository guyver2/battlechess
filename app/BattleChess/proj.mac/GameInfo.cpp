//
//  GameInfo.cpp
//  SimpleGame
//
//  Created by Pol Monso-Purti on 5/15/14.
//
//

#include "GameInfo.h"

const std::string GameInfo::WHITE = "white";


GameInfo::GameInfo(std::string playerName, std::string opponentName, std::string gameUrl, std::string color){
    this->playerName = playerName;
    this->opponentName = opponentName;
    this->gameUrl = gameUrl;
    this->color = color;
}