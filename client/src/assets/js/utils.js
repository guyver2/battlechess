import {Game, User, source} from './store.js'

const API_URL = 'http://sxbn.org:8080' ;
const DEFAULT_AVATAR = './img/avatars/avatar_09.jpeg';


export async function login(username, password) {
    let errorMessage = null;
    let token = null;
    const data = new URLSearchParams();
    data.append("username", username);
    data.append("password", password);
    const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: data,
    };
    try {
        const response = await fetch(API_URL+'/token', requestOptions);
        const data = await response.json();
        if (!response.ok) {
            const error = (data && data.message) || response.status;
            return Promise.reject(error);
        }
        if (data.access_token) {
            token = data.access_token
        } else {
            errorMessage = "login failed";
        }
    } catch (error) {
        console.error('There was an error!', error);
        errorMessage = "login failed";
    }
    return {token, errorMessage};
}


export async function register(username, email, password) {
    let errorMessage = null;
    let token = null;
    const data = {
        username: username,
        email: email,
        plain_password: password,
        full_name: '',
    };

    const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    };
    try {
        const response = await fetch(API_URL+'/users', requestOptions);
        const data = await response.json();
        if ([401, 409].includes(response.status)) {
            errorMessage = data.detail;
            return {token, errorMessage};
        }else if (!response.ok) {
            const error = (data && data.message) || response.status;
            return Promise.reject(error);
        }
        // logs in automatically
        const result = await login(username, password);
        token = result.token;
        errorMessage = result.errorMessage;
    } catch(error) {
                console.error('There was an error!', error);
                errorMessage = "user creation failed";
    }
    return {token, errorMessage};
}

export async function getUserInfo(token, userID=null) {
    let username = null;
    let userId = null;
    let error = null;
    let avatar = null;
    if (userID in source.users) {
        const user = source.users[userID];
        username = user.username;
        userId = user.id;
        avatar = user.avatar;
        return {username, userId, avatar, error};
    } else if (userID == null) {
        if (localStorage.username && localStorage.userId && localStorage.userAvatar){
            username = localStorage.username;
            userId = parseInt(localStorage.userId);
            avatar = localStorage.userAvatar;
            return {username, userId, avatar, error};
        }
    }
    const requestOptions = {
        method: 'GET',
        headers: { 
            'accept': 'application/json',
            'Authorization': 'Bearer '+token,
        }
    }
    const endpoint = userID?'/users/u/'+String(userID):'/users/me';
    try {
        const response = await fetch(API_URL+endpoint, requestOptions);
        const data = await response.json();
        if (!response.ok) {
            error = (data && data.message) || response.status;
        } else {
            username = data.username;
            userId = data.id;
            avatar = data.avatar;
        }
    } catch(err) {
        console.error('There was an error!', err);
        error = String(err);
    }
    source.users[userId] = new User(username, userId, avatar);
    return {username, userId, avatar, error};
}

function diff_minutes(date) {
  const now = new Date(); 
  let diff =(now.getTime() - (new Date(date)).getTime()) / 1000;
  diff /= 60;
  return Math.abs(Math.round(diff));
 }

 export function fancyDateText(date) {
     if (date == null){
         return {text:"None", tooltip:"no moves yet"};
     }
     const delta = diff_minutes(date);
     if (delta < 5) {
         return {text:"just now", tooltip:String(delta)+" minutes ago"};
     } else if (delta < 60) {
         return {text:"last hour", tooltip:String(delta)+" minutes ago"};
     } else if (delta < 60*24) {
         return {text:"last day", tooltip:date.toLocaleString()};
     } else if (delta < 60*24*7) {
         return {text:"last week", tooltip:date.toLocaleString()};
     } else {
         return {text:"long ago", tooltip:date.toLocaleString()};
     }
 }


export async function getUserGames(token) {
    const localUser = await getUserInfo(token);
    let liveGames = [];
    let finishedGames = [];
    let myOpenGames = [];
    let error = null;
    const requestOptions = {
        method: 'GET',
        headers: { 
            'accept': 'application/json',
            'Authorization': 'Bearer '+token,
        }
    }
    try {
        const response = await fetch(API_URL+'/users/me/games', requestOptions);
        const data = await response.json();
        if (!response.ok) {
            error = (data && data.message) || response.status;
        } else {
            for (let game of data) {
                let g = {}
                if (game.white_id != null){
                    if (game.white_id == localUser.userId) {
                        g.white = localUser;
                    } else {
                        const tmp = await getUserInfo(token, game.white_id);
                        g.white = tmp;
                    }
                    if(g.white.avatar == null) {
                        g.white.avatar = DEFAULT_AVATAR;
                    }
                } else {
                    g.white = null;
                }
                if (game.black_id != null){
                    if (game.black_id == localUser.userId) {
                        g.black = localUser;
                    } else {
                        g.black = await getUserInfo(token, game.black_id);
                    }
                    if(g.black.avatar == null) {
                        g.black.avatar = DEFAULT_AVATAR;
                    }
                } else {
                    g.black = null;
                }
                g.status = game.status;
                g.turn = game.turn;
                g.lastmove = game.last_move_time;
                g.lastmoveText = fancyDateText(g.lastmove);
                g.public = game.public;
                g.hash = game.uuid;
                g.canJoin = false;
                g.winner = null;
                if (game.winner === "white"){
                    g.winner = g.white;
                } else if (game.winner === "black"){
                    g.winner = g.black;
                }

                if(game.status === "waiting") {
                    myOpenGames.push(g);
                } else if (game.status === "started") {
                    liveGames.push(g);
                } else if (game.status === "finished") {
                    finishedGames.push(g);
                }
            }
        }
    } catch(err) {
        console.error('There was an error!', err);
        error = String(err);
    }
    return {liveGames, finishedGames, myOpenGames, error};
}


export async function getOpenGames(token) {
    const localUser = await getUserInfo(token);
    let openGames = [];
    let error = null;
    const data = { status: "waiting" };
    const requestOptions = {
        method: 'GET',
        headers: { 
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Bearer '+token,
        },
    }
    let url = new URL(API_URL+'/games')
    url.search = new URLSearchParams(data).toString();

    try {
        const response = await fetch(url, requestOptions);
        const data = await response.json();
        if (!response.ok) {
            error = (data && data.message) || response.status;
        } else {
            for (let game of data) {
                let g = {}
                if (game.white_id != null){
                    if (game.white_id == localUser.userId) {
                        g.white = localUser;
                    } else {
                        const tmp = await getUserInfo(token, game.white_id);
                        g.white = tmp;
                    }
                    if(g.white.avatar == null) {
                        g.white.avatar = DEFAULT_AVATAR;
                    }
                } else {
                    g.white = null;
                }
                if (game.black_id != null){
                    if (game.black_id == localUser.userId) {
                        g.black = localUser;
                    } else {
                        g.black = await getUserInfo(token, game.black_id);
                    }
                    if(g.black.avatar == null) {
                        g.black.avatar = DEFAULT_AVATAR;
                    }
                } else {
                    g.black = null;
                }

                g.status = game.status;
                g.turn = game.turn;
                g.lastmove = game.last_move_time;
                g.lastmoveText = fancyDateText(g.lastmove);
                g.public = game.public;
                g.hash = game.uuid;
                g.canJoin = true;
                openGames.push(g);
            }
        }
    } catch(err) {
        console.error('There was an error!', err);
        error = String(err);
    }

    return { openGames, error};
}


export async function joinGame(token, hash) {
    let error = null;
    const requestOptions = {
        method: 'GET',
        headers: { 
            'Authorization': 'Bearer '+token,
        },
    }
    let url = API_URL+'/games/'+hash+'/join';

    try {
        const response = await fetch(url, requestOptions);
        const data = await response.json();
        if (!response.ok) {
            error = (data && data.message) || response.status;
        }
    } catch(err) {
        console.error('There was an error joining a game!', err);
        error = String(err);
    }
    return { error };
}



export async function createGame(token, color, publicPrivate) {
    let error = null;

    const data = {
        color: color,
        public: publicPrivate === 'public',
    };

    const requestOptions = {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'accept': 'application/json',
            'Authorization': 'Bearer '+token,
         },
        body: JSON.stringify(data),
    };
    try {
        const response = await fetch(API_URL+'/games/', requestOptions);
        const data = await response.json();
        if (!response.ok) {
            error = (data && data.message) || response.status;
        }
    } catch(err) {
        console.error('There was an error!', err);
        error = String(err);
    }
    return error;
}



export async function getGameSnaps(token, gameId) {
    let error = null;
    let snaps = [];
    const requestOptions = {
        method: 'GET',
        headers: { 
            'accept': 'application/json',
            'Authorization': 'Bearer '+token,
        },
    }
    let url = `${API_URL}/games/${gameId}/snaps`;
    try {
        const response = await fetch(url, requestOptions);
        const data = await response.json();
        if (!response.ok) {
            error = (data && data.message) || response.status;
        } else {
            for (let snap of data) {
                // console.log(snap);
                snaps.push(snap);
            }
        }
    } catch(err) {
        console.error('There was an error!', err);
        error = String(err);
    }
    snaps.reverse();

    return { snaps, error };
}

export async function getLastGameSnap(token, gameId) {
    let error = null;
    let snap = null;
    const requestOptions = {
        method: 'GET',
        headers: { 
            'accept': 'application/json',
            'Authorization': 'Bearer '+token,
        },
    }
    let url = `${API_URL}/games/${gameId}/snap`;
    try {
        const response = await fetch(url, requestOptions);
        const data = await response.json();
        if (!response.ok) {
            error = (data && data.message) || response.status;
        } else {
            snap = data;
        }
    } catch(err) {
        console.error('There was an error!', err);
        error = String(err);
    }

    return { snap, error };
}

export async function getGame(token, gameId) {
    let error = null;
    let game = null;
    const requestOptions = {
        method: 'GET',
        headers: { 
            'accept': 'application/json',
            'Authorization': 'Bearer '+token,
        },
    }
    let url = `${API_URL}/games/${gameId}`;
    try {
        const response = await fetch(url, requestOptions);
        const data = await response.json();
        if (!response.ok) {
            error = (data && data.message) || response.status;
        } else {
            game = data
        }
    } catch(err) {
        console.error('There was an error!', err);
        error = String(err);
    }

    return { game, error };
}


export async function getPossibleMoves(token, gameId, start) {
    let error = null;
    let moves = [];
    const requestOptions = {
        method: 'GET',
        headers: { 
            'accept': 'application/json',
            'Authorization': 'Bearer '+token,
        },
    }
    let url = `${API_URL}/games/${gameId}/moves/${start}`;
    try {
        const response = await fetch(url, requestOptions);
        const data = await response.json();
        if (!response.ok) {
            error = (data && data.message) || response.status;
        } else {
            for (let move of data) {
                moves.push(move);
            }
        }
    } catch(err) {
        console.error('There was an error!', err);
        error = String(err);
    }

    return { moves, error };
}


export async function move(token, gameId, source, target) {
    let error = null;
    let snap = null;
    const data = {
        move: source+target,
    };

    const requestOptions = {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'accept': 'application/json',
            'Authorization': 'Bearer '+token,
         },
        body: JSON.stringify(data),
    };
    let url = `${API_URL}/games/${gameId}/move`;
    try {
        const response = await fetch(url, requestOptions);
        const data = await response.json();
        if (!response.ok) {
            error = (data && data.message) || response.status;
        } else {
            snap = data;
        }
    } catch(err) {
        console.error('There was an error making a move', source, "to", target, " : ", err);
        error = String(err);
    }

    return { snap, error };
}