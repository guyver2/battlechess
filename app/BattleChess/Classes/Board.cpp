//
//  Board.cpp
//  SampleGame
//
//  Created by Pol Monso-Purti on 5/8/14.
//  Copyright (c) 2014 Bullets in a Burning Box, Inc. All rights reserved.
//

#include "Board.h"
#include "StringParser.h"
#include "GameInfo.h"

using namespace cocos2d;
using namespace std;

Board::Board(){

    reset();
    
}

void Board::reset(){
    
    _winner = false;
    
    _board[0][0]= "rb";
    _board[0][1]= "nb";
    _board[0][2]= "bb";
    _board[0][3]= "qb";
    _board[0][4]= "kb";
    _board[0][5]= "bb";
    _board[0][6]= "nb";
    _board[0][7]= "rb";
    
    for(int i=0; i<8; i++){
        _board[1][i]= "pb";
        _board[6][i]= "pw";
    }
    _board[7][0]= "rw";
    _board[7][1]= "nw";
    _board[7][2]= "bw";
    _board[7][3]= "qw";
    _board[7][4]= "kw";
    _board[7][5]= "bw";
    _board[7][6]= "nw";
    _board[7][7]= "rw";

}

bool Board::isIn(int row, int col){
    if( row < 0 || 7 < row || col < 0 || 7 < col )
        return false;
    return true;
}

bool Board::foggy(int i, int j, char myColor) const {
    if(myColor != GameInfo::WHITE.c_str()[0] && myColor != GameInfo::BLACK.c_str()[0])
        return false;
    for(int row=i-1;row<=i+1;row++){
        for(int col=j-1;col<=j+1;col++){
            if( !isIn(row,col))
                continue;
            if(_board[row][col] != "" && _board[row][col].c_str()[1] == myColor)
                return false;
        }
    }
    return true;
}

void Board::setSelectedOrigin(int i, int j){
    if( !isIn(i,j) ){
        _move._validOrigin = false;
        return;
    }
    _move._originI = i;
    _move._originJ = j;
    updatePossiblePositions();
    _move._validOrigin = true;
}
                                                                                   
bool Board::isFree(int i, int j) const{
    if(isIn(i,j))
        return _board[i][j] == "";
    return false;
}

Board::PColor Board::isColor(int i, int j){
    if(!isIn(i,j))
        return NONE;
    if(_board[i][j] == "")
        return NONE;
    else if(_board[i][j].c_str()[1] == 'w')
        return WHITE;
    else if(_board[i][j].c_str()[1] == 'b')
        return BLACK;
    else{
        //error
        return NONE;
    }
}

void Board::updatePossiblePositions(){
    int i = _move._originI;
    int j = _move._originJ;
    std::string piece = _board[i][j];
    std::pair<int,int> position;
    _possiblePositions.clear();
    std::vector< Position > possiblePositionsAux;
    if(piece == "")
        return;
    if(piece == "pb"){
        possiblePositionsAux.push_back(Position(i+1,j));
        if(WHITE == isColor(i+1, j+1))
            possiblePositionsAux.push_back(Position(i+1,j+1));
        if(WHITE == isColor(i+1, j-1))
            possiblePositionsAux.push_back(Position(i+1,j-1));
        if(i == 1 and isFree(i+1, j))
            possiblePositionsAux.push_back(Position(i+2,j));
        if(_enpassant != -1 and i == 4 and (j == _enpassant-1 or j == _enpassant+1))
            possiblePositionsAux.push_back(Position(i+1, _enpassant));
    } else if(piece == "pw"){
        possiblePositionsAux.push_back(Position(i-1,j));
        if(BLACK == isColor(i-1, j+1))
            possiblePositionsAux.push_back(Position(i-1,j+1));
        if(BLACK == isColor(i-1, j-1))
            possiblePositionsAux.push_back(Position(i-1,j-1));
        if(i == 6 and isFree(i-1, j))
            possiblePositionsAux.push_back(Position(i-2,j));
        if(_enpassant != -1 and i == 3 and (j == _enpassant-1 or j == _enpassant+1))
            possiblePositionsAux.push_back(Position(i-1, _enpassant));
    } else if( piece.c_str()[0] == 'k'){
        possiblePositionsAux.push_back(Position(i,j+1));
        possiblePositionsAux.push_back(Position(i,j-1));
        possiblePositionsAux.push_back(Position(i+1,j+1));
        possiblePositionsAux.push_back(Position(i+1,j-1));
        possiblePositionsAux.push_back(Position(i+1,j));
        possiblePositionsAux.push_back(Position(i-1,j+1));
        possiblePositionsAux.push_back(Position(i-1,j-1));
        possiblePositionsAux.push_back(Position(i-1,j));
        if(contains(_casteable,piece)){
            if(piece.c_str()[1] == 'w'){
                if(contains(_casteable,"rqw"))
                        possiblePositionsAux.push_back(Position(7,2));
                if(contains(_casteable,"rkw"))
                        possiblePositionsAux.push_back(Position(7,6));
            } else if( piece.c_str()[1] == 'b'){
                if(contains(_casteable,"rqb"))
                        possiblePositionsAux.push_back(Position(0,2));
                if(contains(_casteable,"rkb"))
                        possiblePositionsAux.push_back(Position(0,6));
            }
        }
    } else if( piece.c_str()[0] == 'n'){
        possiblePositionsAux.push_back(Position(i+1,j+2));
        possiblePositionsAux.push_back(Position(i+1,j-2));
        possiblePositionsAux.push_back(Position(i-1,j+2));
        possiblePositionsAux.push_back(Position(i-1,j-2));
        possiblePositionsAux.push_back(Position(i+2,j+1));
        possiblePositionsAux.push_back(Position(i+2,j-1));
        possiblePositionsAux.push_back(Position(i-2,j+1));
        possiblePositionsAux.push_back(Position(i-2,j-1));
    } else if( piece.c_str()[0] == 'r'){
        for(int a=1;a<8;a++){
            possiblePositionsAux.push_back(Position(i,j+a));
            possiblePositionsAux.push_back(Position(i+a,j));
            possiblePositionsAux.push_back(Position(i,j-a));
            possiblePositionsAux.push_back(Position(i-a,j));
        }
    } else if( piece.c_str()[0] == 'b'){
        for(int a=1;a<8;a++){
            possiblePositionsAux.push_back(Position(i+a,j+a));
            possiblePositionsAux.push_back(Position(i-a,j+a));
            possiblePositionsAux.push_back(Position(i+a,j-a));
            possiblePositionsAux.push_back(Position(i-a,j-a));
        }
    } else if( piece.c_str()[0] == 'q'){
        for(int a=1;a<8;a++){
            possiblePositionsAux.push_back(Position(i,j+a));
            possiblePositionsAux.push_back(Position(i+a,j));
            possiblePositionsAux.push_back(Position(i,j-a));
            possiblePositionsAux.push_back(Position(i-a,j));
            possiblePositionsAux.push_back(Position(i+a,j+a));
            possiblePositionsAux.push_back(Position(i-a,j+a));
            possiblePositionsAux.push_back(Position(i+a,j-a));
            possiblePositionsAux.push_back(Position(i-a,j-a));
        }
    }
    for(int i=0;i<possiblePositionsAux.size();i++){
        Position pos = possiblePositionsAux[i];
        if(isIn(pos.first, pos.second))
            _possiblePositions.push_back(pos);
    }
}

void Board::setSelectedDest(int i, int j){
    if( !isIn(i,j) ){
        _move._validDest = false;
        return;
    }
    _move._destI = i;
    _move._destJ = j;
    _move._validDest = true;

}
/*
 format [board state]#[taken pieces]#[castleable pieces]#[winner]
 full message example (initial state as seen by white player) :
 ________________________________________________pw_pw_pw_pw_pw_pw_pw_pw_rw_nw_bw_qw_kw_bw_nw_rw##kb_kw_rqb_rkb_rqw_rkw#n

 board state is a succession of 64 cells dumped as string and divided by ‘_’ characters
 Cells are given row-wise from top to bottom and from left to right. An empty string is an empty cell. Every other cell is encoded as a 2-characters string. The first character gives the figure (‘r’ : rook, ‘n’ : knight, ‘b’ : bishop, ‘q’ : queen, ‘k’ : king) and the second gives its color (‘w’ or ‘b’)
 
 taken pieces list all the pieces that have been taken so far, in order. The string has the same form as the board state. Without the empty cells.
 castleable pieces indicates which castling moves are still available. The string has the same form as the board state. Without the empty cells.
 winner is a single character whose value indicates if there is a winner to the current game (‘n’ : no winner so far, ‘w’ : white wins, ‘b’ : black wins)

*/
void Board::fromString(std::string board){
  
    std::vector<std::string> boardInfoVect = StringParser::split(board, '#');
    //we have 4 fields, board, taken pieces, casteable pieces and winner
    assert(boardInfoVect.size() == 5);
    //quick fix of the split not getting an empty piece after the last _
    boardInfoVect[0] = boardInfoVect[0] + "_";
    std::vector<std::string> boardVect = StringParser::split(boardInfoVect[0], '_');
    _taken = StringParser::split(boardInfoVect[1], '_');
    _casteable = StringParser::split(boardInfoVect[2], '_');
    std::istringstream ss(boardInfoVect[3]);
    ss >> _enpassant;
    _winner = boardInfoVect[4].c_str()[0];
    assert(   _winner == 'n'
           || _winner == 'w'
           || _winner == 'b' );
    
    for(int i=0; i<8; i++){
        for(int j=0; j<8; j++){
            _board[i][j] = boardVect[i*8 + j];
        }
    }
}