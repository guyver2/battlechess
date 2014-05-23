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
    static const std::string WHITE;
    static const std::string BLACK;
    GameInfo(){
        playerName = "defaultName";
        opponentName = "defaultOpponentName";
        gameUrl = "http://sxbn.org";
        playerColor = 'n';
    };
    GameInfo(std::string playerName, std::string opponentName, std::string gameUrl, std::string color);
};

#endif /* defined(__SimpleGame__GameInfo__) */
