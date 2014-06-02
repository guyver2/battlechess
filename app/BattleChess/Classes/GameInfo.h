//
//  GameInfo.h
//  SimpleGame
//
//  Created by Pol Monso-Purti on 5/15/14.
//
//

#ifndef __SimpleGame__GameInfo__
#define __SimpleGame__GameInfo__

#include <iostream>

class GameInfo {
public:
    std::string playerName;
    std::string opponentName;
    std::string gameUrl;
    char playerColor;
    char opponentColor;
    static const std::string WHITE;
    static const std::string BLACK;
    GameInfo();
    GameInfo(std::string playerName, std::string opponentName, std::string gameUrl, std::string color);
    void setPlayerColor(std::string myColor);
    static std::string getUsername();
};

#endif /* defined(__SimpleGame__GameInfo__) */
