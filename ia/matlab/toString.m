function verboseBoard = toString(board)

    verboseBoard = cell(size(board,1), size(board,2));
    for i = 1:size(board,1)
        for j = 1:size(board,2)
            verboseBoard(i,j) = name(board(i,j));
        end
    end
end

function piece = name( pieceInt )
    dictionary = cellstr(['  ';'pw';'nw';'bw';'rw';'qw';'kw';'pb';'nb';'bb';'rb';'qb';'kb']);
    piece = dictionary(pieceInt+1);
end