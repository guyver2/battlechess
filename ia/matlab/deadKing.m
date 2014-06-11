function outcome = deadKing( board )
%DEADKING Summary of this function goes here
%   Detailed explanation goes here

    whiteAlive = false;
    blackAlive = false;
    for i = 1:size(board,1)
        for j = 1:size(board,2)
            if board(i,j) == 12 %unname('kw')
                whiteAlive = true;
            elseif board(i,j) == 6 %unname('kb')
                blackAlive = true;
            end
        end
    end

    if whiteAlive && blackAlive
        outcome = 0;
    elseif whiteAlive && ~blackAlive
        outcome = 1;
    elseif ~whiteAlive && blackAlive
        outcome = 2;
    else
        outcome = -1;
    end
end

