function writeGame( filename, gameMoves )
    fid = fopen(filename,'w');
    fprintf(fid, 'ia1 Vs. ia2\n');
    for i = 1:size(gameMoves,1)
        move = gameMoves(i,:) - ones(1,4);
        fprintf(fid,'%d %d %d %d\n',move(1,:));
    end
    fclose(fid);
end

