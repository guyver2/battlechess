//
//  Board.h
//  SampleGame
//
//  Created by Pol Monso-Purti on 5/8/14.
//  Copyright (c) 2014 Bullets in a Burning Box, Inc. All rights reserved.
//

#ifndef __SampleGame__Board__
#define __SampleGame__Board__

#include <iostream>
#include "cocos2d.h"
#include "constants.h"
#include "platform/CCCommon.h"

typedef std::pair<int, int> Position;

class Move{
public:
    int _originI;
    int _originJ;
    int _destI;
    int _destJ;

    bool _validOrigin;
    bool _validDest;
    
    Move(){
        _validOrigin = false;
        _validDest = false;
    }

    bool isValid(){
        return _validOrigin && _validDest;
    }
};

class Board : public cocos2d::CCSpriteBatchNode
{
public:
    Board();

    enum {
        kBackground,
        kBoard,
        kPieces,
        kForeground
    };
    
    enum PColor {
        NONE,
        WHITE,
        BLACK
    };
    Move _move;
    char _winner;
    int _enpassant;
    std::vector<std::string> _casteable;
    std::vector<std::string> _taken;
    std::vector< std::pair<int,int> > _possiblePositions;
    std::string _board[8][8];
    void reset();
    static bool isIn(int row, int col);
    bool foggy(int i, int j, char myColor) const;
    void setSelectedOrigin(int i, int j);
    void setSelectedDest(int i, int j);
    std::string getSelectedPiece(){
        if(_move._validOrigin)
            return _board[_move._originI][_move._originJ];
        DEBUGNOCC("Invalid origin");
        assert(!"Invalid origin");
    }
    std::string getSelectedDestination(){
        return _board[_move._destI][_move._destJ];
    }
    void fromString(std::string boardStr);
  
    bool isFree(int i, int j) const;
    PColor isColor(int i, int j);
private:
    void updatePossiblePositions();
    bool contains(std::vector<std::string> v, std::string x ){
        return std::find(v.begin(), v.end(), x) != v.end();
    }

};

#endif /* defined(__SampleGame__Board__) */
