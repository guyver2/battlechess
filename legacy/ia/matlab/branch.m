function [theboards, themoves] = branch( board, color)
%BRANCH branch returns all the possible boards from the current position @board given a color @color
%   board is a 8x8 chess board where white is placed on the bottom and
%   black at the top
%   color is 1 for white, 2 for black

%%todo check input board integrity
allboards = zeros(8,8,1);
allmoves = zeros(1,4);
for i = 1:size(board,1)
    for j = 1:size(board,2)
        piece = board(i,j);
        if piece ~= 0 && getColor(board, i,j) == color
            [pieceboards, piecemoves] = getPossibleBoards(board, i,j);
            allboards = cat(3,allboards,pieceboards);
            allmoves  = cat(1,allmoves, piecemoves);
        end
    end
end

%remove the first allocating board
allboards(:,:,1) = [];
allmoves(1,:) = [];
theboards = allboards;
themoves = allmoves;
end

function outcome = isIn(i,j)
    if 0 < i && i <= 8 && 0 < j && j <= 8
        outcome = true;
    else
        outcome = false;
    end
end

function outcome = getColor(board, i, j)
    if ~isIn(i,j)
        outcome = -1;
    elseif board(i,j) == 0
        outcome = 0;
    elseif board(i,j) > 6
        outcome = 2;
    else
        outcome = 1;
    end
end

% 
% 	def move(self, i, j, ii, jj):
% 		if self.board[ii][jj] != '' and self.board[i][j][1] == self.board[ii][jj][1]:
% 			# same color
% 			return False, []
% 		reach = self.getReachablePosition(i,j) # actually possible destination (obstacles, ennemies)
% 		pos = self.getPossiblePosition(i,j) # anything in the range of the piece
% 		if [ii,jj] not in pos:
% 			return False, []
% 		elif [ii,jj] not in reach :
% 			res = self.getClosest(i,j,ii,jj,reach)
% 			if res :
% 				ii, jj = res
% 			else :
% 				return False, []
% 		if self.board[ii][jj] != '':
% 			# sniper sound
% 			#if self.visibility : # check if we're not in playback mode
% 			#	if (abs(ii-i) > 1 or abs(jj-j) > 1) and (self.visibility[ii][jj] == False or self.visibility[i][j] == False):
% 			#		self.sniper.play()
% 			self.taken.append(str(self.board[ii][jj]))
% 
% 		#check if we killed in passant
% 		self.takeEnPassant(i,j,ii,jj)	
% 		#reset enpassant value
% 		self.enpassant = -1
% 		#the pawn jumped, set it as 'en passant' pawn
% 		if self.board[i][j][0] == 'p':
% 			if self.board[i][j][1] == 'b' and i == 1 and ii == 3:
% 				self.enpassant = j
% 			elif self.board[i][j][1] == 'w' and i == 6 and ii == 4:
% 				self.enpassant = j
% 
% 		# replace destination with origin
% 		self.board[ii][jj] = self.board[i][j]
% 		self.board[i][j] = ''
% 
% 		# if a pawn reached the end of the board, it becomse a queen
% 		if self.board[ii][jj][0] == 'p' and (ii==0 or ii==7) :
% 			self.board[ii][jj] = 'q'+self.board[ii][jj][1]
% 
%     	# if we were performing a castle, move the tower too 
% 		whichRock = self.castleInfo(self.board[ii][jj],i,j,ii,jj)  
% 		if whichRock == 'rqb':
% 			self.board[0][0] = ''
% 			self.board[0][3] = 'rb'
% 		elif whichRock == 'rkb':
% 			self.board[0][7] = '' 
% 			self.board[0][5] = 'rb' 
% 		elif whichRock == 'rqw':
% 			self.board[7][0] = '' 
% 			self.board[7][3] = 'rw' 
% 		elif whichRock == 'rkw':
% 			self.board[7][7] = '' 
% 			self.board[7][5] = 'rw' 
% 		# if k or r, castle for that piece forbidden in the future
% 		if self.board[ii][jj][0] == 'k' and self.board[ii][jj] in self.castleable:
% 			self.castleable.remove(self.board[ii][jj])	
% 		elif self.board[ii][jj][0] == 'r':
% 			if [i, j] == RQBPOS and 'rqb' in self.castleable:
% 				self.castleable.remove('rqb')
% 			elif [i, j] == RKBPOS and 'rkb' in self.castleable:
% 				self.castleable.remove('rkb')
% 			elif [ii, j] == RQWPOS and 'rqw' in self.castleable:
% 				self.castleable.remove('rqw')
% 			elif [i, j] == RKWPOS and 'rkw' in self.castleable:
% 				self.castleable.remove('rkw')
% 
% 		# check if we have a winner
% 		if 'kb' in self.taken :
% 			self.winner = 'w'
% 		elif 'kw' in self.taken :
% 			self.winner = 'b'
% 
% 		return True, [i,j,ii,jj]


function nextboard = move(board, i,j,ii,jj)

    %TODO finish this
    board(ii,jj) = board(i,j);
    board(i,j) = 0;
    nextboard = board;
end

function addMoveIfOk(board, i,j,ii,jj)
    global boards
    global moves
    if isIn(ii,jj) && getColor(board, i,j) > 0 && getColor(board,ii,jj) > -1 ...
                   && getColor(board,i,j) ~= getColor(board,ii,jj) %includes free, different color
        boards = cat(3,boards,move(board,i,j,ii,jj));
        moves = cat(1,moves,[i j ii jj]);
    end
end

%checks if trajectory is free too
%does not do casteable, enpassant nor promotion as for now
function [pieceBoards, piecemoves] = getPossibleBoards(board, i, j)
    global boards
    global moves
    
    boards = zeros(size(board,1),size(board,2));
    moves = zeros(1,4);
    
    dictionaryColorChange = 6; %unname('kw')
    piece = board(i,j);
    color = 1;
    colorlessPiece = piece;
    if piece > dictionaryColorChange
        color = 2;
        colorlessPiece = piece - dictionaryColorChange;
    end

    switch colorlessPiece
        case 1 %p
            if color == 2 %w going up
                if getColor(board, i+1,j) == 0
                    addMoveIfOk(board,i,j,i+1,j);
                end
                if i == 2 && getColor(board, i+1,j) == 0 && getColor(board, i+2,j) == 0
                    addMoveIfOk(board,i,j,i+2,j);
                end
                if getColor(board,i+1,j+1) == 1
                    addMoveIfOk(board,i,j,i+1,j+1);
                end
                if getColor(board,i+1,j-1) == 1
                    addMoveIfOk(board,i,j,i+1,j-1);
                end    
            else %b going down
                if getColor(board,i-1,j) == 0
                    addMoveIfOk(board,i,j,i-1,j);
                end
                if i == 7 && getColor(board,i-1,j) == 0 && getColor(board,i-2,j) == 0
                    addMoveIfOk(board,i,j,i-2,j);
                end
                if getColor(board,i-1,j-1) == 2
                    addMoveIfOk(board,i,j,i-1,j-1);
                end
                if getColor(board,i-1,j+1) == 2
                    addMoveIfOk(board,i,j,i-1,j+1);
                end 
            end
        case 2 %n
            addMoveIfOk(board,i,j,i+1,j+2);
            addMoveIfOk(board,i,j,i+1,j-2);
            addMoveIfOk(board,i,j,i-1,j+2);
            addMoveIfOk(board,i,j,i-1,j-2);
            addMoveIfOk(board,i,j,i+2,j+1);
            addMoveIfOk(board,i,j,i-2,j+1);
            addMoveIfOk(board,i,j,i+2,j-1);
            addMoveIfOk(board,i,j,i-2,j-1);
        case 3 %b
            addBishopReach(board,i,j,color);
        case 4 %r
            addRookReach(board,i,j,color);
        case 5 %q
            addBishopReach(board,i,j,color);
            addRookReach(board,i,j,color);
        case 6 %k
            addMoveIfOk(board,i,j,i+1,j+1);
            addMoveIfOk(board,i,j,i+1,  j);
            addMoveIfOk(board,i,j,i-1,j-1);
            addMoveIfOk(board,i,j,i  ,j+1);
            addMoveIfOk(board,i,j,i  ,j-1);
            addMoveIfOk(board,i,j,i-1,j+1);
            addMoveIfOk(board,i,j,i-1,  j);
            addMoveIfOk(board,i,j,i-1,j-1);
    end
    
    boards(:,:,1) = []; %remove allocating empty first board
    moves(1,:) = [];
    pieceBoards = boards;
    piecemoves = moves;
end

function addRookReach(board, i,j, color)
    global boards
    
    a=1;
    while a
        dcolor = getColor(board,i,j+a);
        if dcolor < 0
            break;
        elseif dcolor == 0
            a = a+1;
        elseif dcolor ~= color
            addMoveIfOk(board,i,j,i,j+a);
            break;
        else
            break;
        end
    end
    a=1;
    while a
        dcolor = getColor(board,i,j-a);
        if dcolor < 0
            break;
        elseif dcolor == 0
            a = a+1;
        elseif dcolor ~= color
            addMoveIfOk(board,i,j,i,j-a);
            break;
        else
            break;
        end
    end
    a=1;
    while a
        dcolor = getColor(board,i+a,j);
        if dcolor < 0
            break;
        elseif dcolor == 0
            a = a+1;
        elseif dcolor ~= color
            addMoveIfOk(board,i,j,i+a,j);
            break;
        else
            break;
        end
    end
    a=1;
    while a
        dcolor = getColor(board,i+a,j);
        if dcolor < 0
            break;
        elseif dcolor == 0
            a = a+1;
        elseif dcolor ~= color
            addMoveIfOk(board,i,j,i+a,j);
            break;
        else
            break;
        end
    end     
end

function addBishopReach(board, i, j, color)
    global boards
    
    a=1;
    while a
        dcolor = getColor(board,i+a,j+a);
        if dcolor < 0
            break;
        elseif dcolor == 0
            a = a+1;
        elseif dcolor ~= color
            addMoveIfOk(board,i,j,i+a,j+a);
            break;
        else
            break;
        end
    end
    a=1;
    while a
        dcolor = getColor(board,i+a,j-a);
        if dcolor < 0
            break;
        elseif dcolor == 0
            a = a+1;
        elseif dcolor ~= color
            addMoveIfOk(board,i,j,i+a,j-a);
            break;
        else
            break;
        end
    end
    a=1;
    while a
        dcolor = getColor(board,i-a,j+a);
        if dcolor < 0
            break;
        elseif dcolor == 0
            a = a+1;
        elseif dcolor ~= color
            addMoveIfOk(board,i,j,i-a,j+a);
            break;
        else
            break;
        end
    end
    a=1;
    while a
        dcolor = getColor(board,i-a,j-a);
        if dcolor < 0
            break;
        elseif dcolor == 0
            a = a+1;
        elseif dcolor ~= color
            addMoveIfOk(board,i,j,i-a,j-a);
            break;
        else
            break;
        end
    end     
end