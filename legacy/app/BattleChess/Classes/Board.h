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
#include <algorithm>

typedef std::pair<int, int> Position;

class StringParser {
public:
    static std::vector<std::string> &split(const std::string &s, char delim, std::vector<std::string> &elems) {
        std::stringstream ss(s);
        std::string item;
        while (std::getline(ss, item, delim)) {
            elems.push_back(item);
        }
        return elems;
    }
    
    static std::vector<std::string> split(const std::string &s, char delim) {
        std::vector<std::string> elems;
        split(s, delim, elems);
        return elems;
    }
};

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
    std::vector<std::string> _castleable;
    std::vector<std::string> _taken;
    std::vector< std::pair<int,int> > _possiblePositions;
    std::string _board[8][8];
    void reset();
    static bool isIn(int row, int col);
    bool foggy(int i, int j, char myColor) const;
    void setSelectedOrigin(int i, int j, char myColor);
    void setSelectedDest(int i, int j);
    std::string getSelectedPiece(){
        if(_move._validOrigin)
            return _board[_move._originI][_move._originJ];
        assert(!"Invalid origin");
    }
    std::string getSelectedDestination(){
        return _board[_move._destI][_move._destJ];
    }
    std::string toString();
    void print();
    void fromStringWithoutSave(std::string boardStr);
    void fromString(std::string boardStr);
  
    bool isFree(int i, int j) const;
    PColor isColor(int i, int j);
    
    void getPossiblePositions(const std::string piece, int i, int j, std::vector< Position >& possiblePositions);
    std::vector<std::string> _collectedBoardStrings;
    std::vector< Board > boardsFromStrings();
    
    //not used
    std::vector< std::string > boardsStringsFromMoves(std::string savedGameContent);
    static std::vector< Board > boardsFromMoves(std::string savedGameContent);
    void move(const Move& move);
private:
    Move getClosest(Move move, const std::vector< Position >& reach);
    std::string castleInfo(int i, int j, int ii,int jj);
    void updatePossiblePositions();
    bool contains(std::vector< std::string > v, std::string x ){
        return std::find(v.begin(), v.end(), x) != v.end();
    }
    bool contains(std::vector< Position > v, Position x ){
        //todo overload == operator?
        for(int i;i<v.size();i++){
            if(v[i].first == x.first && v[i].second == x.second)
                return true;
        }
        return false;
    }

};

#endif /* defined(__SampleGame__Board__) */
