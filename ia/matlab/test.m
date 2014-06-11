
global boards

board = zeros(8,8);

board(8,:) = [4,2,3,5,6,3,2,4];
board(7,:) = [1,1,1,1,1,1,1,1];
board(2,:) = board(7,:) + 6;
board(1,:) = board(8,:) + 6;

board
toString(board)

% white = 1
% black = 2
color = 1; 

nextboard = board;

game = zeros(size(board,1),size(board,2));
gameMoves = zeros(1,4);
while(deadKing(nextboard) == 0)
    
    [theboards, themoves] = branch(nextboard, color);
    selBoard = randi(size(theboards,3));
    nextboard = theboards(:,:,selBoard);
    nextMove = themoves(selBoard,:);

    game = cat(3,game,nextboard);
    gameMoves = cat(2,gameMoves,nextMove);
    if color == 1
        color = 2;
    else
        color = 1;
    end
end

game(:,:,1) = [];
gameMoves(1,:) = [];

for g = 1:size(game,3)
    toString(game(:,:,g))
end


if deadKing(nextboard) == 1
    disp('white wins')
else
    disp('black wins')
end

%not working properly yet
%writeGame('testVsTest.txt',gameMoves);
