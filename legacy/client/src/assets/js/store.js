

class User {
    constructor(username, id, avatar) {
        this.username = username;
        this.id = id;
        this.avatar = avatar;
    }
}

class Game {
    constructor(id, hash, white, black, status, turn, winner, openToAll){
        this.id = id;
        this.hash = hash;
        this.white = white;
        this.black = black;
        this.status = status;
        this.turn = turn;
        this.winner = winner;
        this.public = openToAll;
    }
}

var source = {users:{}};



exports.source = source;
exports.User = User;
exports.Game = Game;
