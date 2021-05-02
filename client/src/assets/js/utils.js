const API_URL = 'http://sxbn.org:8080' ;
const DEFAULT_AVATAR = './img/avatar_09.jpeg';

export async function login(username, password) {
    let errorMessage = null;
    let token = null;
    console.log("login in with ", username, password);
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
    console.log("user creation with ", username, email, password);
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
    const requestOptions = {
        method: 'GET',
        headers: { 
            'accept': 'application/json',
            'Authorization': 'Bearer '+token,
        }
    }
    const endpoint = userID?'/users/'+String(userID):'/users/me';
    try {
        const response = await fetch(API_URL+endpoint, requestOptions);
        const data = await response.json();
        console.log(data);
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
         return {text:"unknown", tooltip:"unknown"};
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
    let openGames = [];
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
        console.log(data);
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

                // const w_username = game.white_id == localUser.userId?localUser.username:"the other one";
                // const b_username = game.black_id == localUser.userId?localUser.username:"the other one";
                // const w_avatar = game.white_id == localUser.userId?localUser.avatar:null; 
                // const b_avatar = game.black_id == localUser.userId?localUser.avatar:null;

                // g.white = {username:'@'+w_username, avatar:w_avatar!=null?w_avatar:DEFAULT_AVATAR}
                // g.black = {username:'@'+b_username, avatar:b_avatar!=null?b_avatar:DEFAULT_AVATAR}
                g.moves = game.snaps.length;
                g.status = game.status;
                g.turn = game.turn;
                g.lastmove = game.last_move_time;
                g.public = game.public;
                g.hash = game.uuid;

                if(game.status === "waiting") {
                    openGames.push(g);
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
    return {liveGames, finishedGames, openGames, error};
}



// var game = {}
//     if (Math.floor(Math.random() * 2) == 0){
//         game.white = users.sample();
//         game.black = localUser;
//     } else {
//         game.black = users.sample();
//         game.white = localUser;
//     }
//     game.moves = Math.floor(Math.random() * 50);
//     game.turn = (Math.floor(Math.random() * 2) == 0) ? "white":"black";
//     game.status = status;
//     var d = new Date();
//     d.setDate(d.getDate() - Math.floor(Math.random()*15));
//     game.lastmove = d.toLocaleString();
//     game.lastmoveText = fancyDateText(d);
//     return game;