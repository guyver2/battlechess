//
//  Board.cpp
//  SampleGame
//
//  Created by Pol Monso-Purti on 5/8/14.
//  Copyright (c) 2014 Bullets in a Burning Box, Inc. All rights reserved.
//

#include "Board.h"
#include "GameInfo.h"

using namespace cocos2d;
using namespace std;

Board::Board(){
    reset();
}

void Board::reset(){
    
    _winner = false;
    
    _taken.clear();
    
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
    for(int i=2; i<=5; i++){
        for(int j=0; j<8; j++)
            _board[i][j] = "";
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

void Board::setSelectedOrigin(int i, int j, char myColor){
    if( !isIn(i,j) || _board[i][j][1] != myColor){
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
    _possiblePositions.clear();
    int i = _move._originI;
    int j = _move._originJ;
    std::string piece = _board[i][j];
    getPossiblePositions(piece, i, j, _possiblePositions);
}

void Board::getPossiblePositions( const std::string piece, int i, int j, std::vector< Position >& possiblePositions){
    std::vector< Position > possiblePositionsAux;
    std::pair<int,int> position;
    DEBUG2("piece: %s", piece.c_str());
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
        if(contains(_castleable,piece)){
            if(piece.c_str()[1] == 'w'){
                if(contains(_castleable,"rqw"))
                        possiblePositionsAux.push_back(Position(7,2));
                if(contains(_castleable,"rkw"))
                        possiblePositionsAux.push_back(Position(7,6));
            } else if( piece.c_str()[1] == 'b'){
                if(contains(_castleable,"rqb"))
                        possiblePositionsAux.push_back(Position(0,2));
                if(contains(_castleable,"rkb"))
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
            possiblePositions.push_back(pos);
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

std::string Board::toString(){
    stringstream ss;
    
    for(int i=0; i<8; i++){
        for(int j=0; j<8; j++){
            if(i!=0 || j!=0)
                ss << "_";
            std::string aux = _board[i][j];
            ss << _board[i][j];
        }
    }
    ss << "#";
    
    for(int i=0; i<_taken.size();i++){
        ss << _taken[i];
        //quick fix to remove the last _
        if(i==_taken.size()-1)
            break;
        ss << "_";
    }
    
    //std::string::erase()?
    
    ss << "###n"; //ignore casteable, enpassant and winner for now
    std::string boardStr = ss.str();
    return boardStr;
    //res = boardStr+'#'+takenStr+'#'+castleableStr+'#'+enpassantStr+'#'+winnerStr

    /*
     # dump as a string to ease portability with other apps
	def toString(self, color=None):
		visibility = [[True for i in xrange(8)] for j in xrange(8)]
		if color : # hide if necessary
			visibility = [[False for i in xrange(8)] for j in xrange(8)]
			for i in xrange(8):
				for j in xrange(8) :
					if self.board[i][j].endswith(color) :
						for di in xrange(-1,2):
							for dj in xrange(-1,2):
								if self.isIn(i+di, j+dj) :
									visibility[i+di][j+dj] = True
		boardStr = ''
		for i in xrange(8):
			for j in xrange(8) :
				if not visibility[i][j] :
					boardStr += '_' # 3 spaces
				else :
					boardStr += self.board[i][j]+'_'
		boardStr = boardStr[:-1] # remove last '_'
		takenStr = '_'.join(self.taken)
		if color :
			castleableStr = '_'.join([e for e in self.castleable if e.endswith(color)])
		else :
			castleableStr = '_'.join([e for e in self.castleable])
		#todo only send enpassant if it's actually possible, otherwise we are leaking information
		if color == 'b' and visibility[4][self.enpassant] == False:
			enpassantStr = str(-1) 
		elif color == 'w' and visibility[3][self.enpassant] == False:
			enpassantStr = str(-1) 
		else:
			enpassantStr = str(self.enpassant)
		if self.winner : winnerStr = self.winner
		else : winnerStr = 'n'
		res = boardStr+'#'+takenStr+'#'+castleableStr+'#'+enpassantStr+'#'+winnerStr
		return res
     */
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
  
    //store board for replay
    _collectedBoardStrings.push_back(board);
    //
    fromStringWithoutSave(board);
}

void Board::fromStringWithoutSave(std::string board){
    
    std::vector<std::string> boardInfoVect = StringParser::split(board, '#');
    //we have 4 fields, board, taken pieces, casteable pieces and winner
    assert(boardInfoVect.size() == 5);
    //quick fix of the split not getting an empty piece after the last _
    boardInfoVect[0] = boardInfoVect[0] + "_";
    std::vector<std::string> boardVect = StringParser::split(boardInfoVect[0], '_');
    _taken = StringParser::split(boardInfoVect[1], '_');
    std::sort(_taken.begin(),_taken.end());
    _castleable = StringParser::split(boardInfoVect[2], '_');
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


std::vector< Board > Board::boardsFromStrings(){
 
    std::vector< Board > replayBoards;
    Board board;
    for(int i=0; i < _collectedBoardStrings.size(); i++){
        board.fromString(_collectedBoardStrings[i]);
        replayBoards.push_back(board);
    }
    
    return replayBoards;
}

std::vector< std::string > Board::boardsStringsFromMoves(std::string savedGameContent){

    std::vector< std::string > boardsStrings;
    std::istringstream iss(savedGameContent);
    std::string line;
    
    reset();
    std::string boardstr = this->toString();
    boardsStrings.push_back(boardstr);

    //remove header //TODO reassign it to gameInfo
    std::getline(iss,line);
    if(line.find("Vs.") == std::string::npos){
        DEBUG2("Error reading url, header invalid (does not contain 'Vs.': %s. Aborting replay.", line.c_str());
        return boardsStrings;
    }
    int i = 0;
    while (std::getline(iss, line))
    {
        //split
        i++;
        DEBUG2("Loading move %d", i);
        istringstream iss(line);
        Move move;
        //TODO check that iss is valid
        iss >> move._originI;
        iss >> move._originJ;
        iss >> move._destI;
        iss >> move._destJ;
        this->move(move);

        std::string auxstr = this->toString();
        DEBUG2("b: %s", auxstr.c_str());

        boardsStrings.push_back(this->toString());
    }
    return boardsStrings;
}

//not used //FIXME why build other Boards provokes the node destruction?
std::vector< Board > Board::boardsFromMoves(std::string savedGameContent){

    std::vector< Board > boards;
    std::istringstream iss(savedGameContent);
    std::string line;
    Board boardAux;
    
    //remove header //TODO reassign it to gameInfo
    std::getline(iss,line);
    
    while (std::getline(iss, line))
    {
        //split
        istringstream iss(line);
        Move move;
        //TODO check that iss is valid
        iss >> move._originI;
        iss >> move._originJ;
        iss >> move._destI;
        iss >> move._destJ;
        boardAux.move(move);
        //todo this just sets the reference, we need to copy
        boards.push_back(boardAux);
    }
    return boards;
}

std::string Board::castleInfo(int i, int j, int ii, int jj){
    if(_board[i][j][0] == 'k') {
        if(jj - j == 2){
            if(_board[i][j][1] == 'w')
                return "rkw";
            else
                return "rkb";
        }else if( j - jj == 2) {
            if(_board[i][j][1] == 'w')
                return "rqw";
            else
                return "rqb";
        }
    }
    return "";
}


Move Board::getClosest(Move move, const std::vector< Position >& reach){
    int ii = move._destI;
    int jj = move._destJ;
    int i  = move._originI;
    int j  = move._originJ;
    int di,dj;
    
    std::string piece = _board[i][j];
    
    //knight always reaches destination
    if(piece.c_str()[0] == 'n')
        return move;
    
    //get direction vector
    if(ii - i == 0)
		di = 0;
	else if(ii - i < 0)
		di = -1;
	else
		di =  1;
	if(jj - j == 0)
		dj = 0;
	else if(jj - j < 0)
		dj = -1;
	else
		dj =  1;
    
    //FIXME assumption that moving to the same position is filtered out by the server
	for(int a = 1; isIn(i+a*di,j+a*dj) && !(i+a*di == ii  && j+a*dj == jj); a++) {
        std::string obsPiece = _board[i+a*di][j+a*dj];
        if( obsPiece != "" ){
            if(obsPiece.c_str()[1] == piece.c_str()[1]){
                move._destI = i+(a-1)*di;
                move._destJ = j+(a-1)*dj;
                break;
            }else{
                //taking the enemy piece
                move._destI = i+a*di;
                move._destJ = j+a*dj;
                break;
            }
        }
    }
	return move;
}


void Board::move(const Move& move){
    
    int i = move._originI;
    int j = move._originJ;
    //FIXME do I have to implement this too? Or the stored move is the actual valid move?
    
    std::vector< Position > reach;
    getPossiblePositions(_board[i][j], i, j, reach);
    Move reachMove = getClosest(move, reach);

    int ii = reachMove._destI;
    int jj = reachMove._destJ;
    
    //FIXME some error testing would be nice to prevent EXC_BAD_ACCESS
    if(_board[ii][jj] != "")
        _taken.push_back(_board[ii][jj]);
    
    //if pawn, moved diagonally but nothing killed it means we had killed in passant at (i,jj) during game
    if(_board[i][j][0] == 'p' && j != jj && _board[ii][jj] == "")
        _board[i][jj] = "";
    
    //# if we were performing a castle, move the tower too
    std::string whichRock = castleInfo(i,j,ii,jj);
    if(whichRock == "rqb"){
        _board[0][0] = "";
        _board[0][3] = "rb";
    } else if(whichRock == "rkb"){
        _board[0][7] = "";
        _board[0][5] = "rb";
    } else if(whichRock == "rqw") {
        _board[7][0] = "";
        _board[7][3] = "rw";
    } else if(whichRock == "rkw") {
        _board[7][7] = "";
        _board[7][5] = "rw";
    }

    //# replace destination with origin
    _board[ii][jj] = _board[i][j];
    _board[i][j] = "";
     
     //# if a pawn reached the end of the board, it becomse a queen
     if(_board[ii][jj][0] == 'p' && (ii==0 || ii==7))
         _board[ii][jj] = 'q'+ _board[ii][jj][1];
     }