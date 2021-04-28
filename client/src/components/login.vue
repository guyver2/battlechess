<template>
  <div class="flexctn">
        <div class="loginContent">
            <div v-if="incomingError" class="warning">
                <div>
                    <strong>Error!</strong> {{incomingError}}
                </div>
                <div>
                    <a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>
                </div>
            </div>

            <form class="myform">
                <h2 class="form-signin-heading text-color-5 center">Sign in</h2>
                <label for="inputUsername" class="text-color-5">username</label>
                <input type="text" id="inputUsername" class="bcinput text-color-5" placeholder="username" required autofocus  v-model="username">
                <label for="inputPassword" class="text-color-5">password</label>
                <input type="password" id="inputPassword" class="form-control text-color-5" placeholder="password" required v-model="password">
                <div class="text-color-5">
                    <button type="button" class="button" v-on:click="login">Sign in</button>
                    <div class="signup">Or <a href="/register">Sign up</a>.</div>
                </div>
            </form>
            
            <div v-if="errorMessage" class="warning">
                <div>
                    <strong>Error!</strong> {{errorMessage}}
                </div>
                <div>
                    <a href="#" v-on:click="errorMessage = ''" class="close" data-dismiss="alert" aria-label="close">&times;</a>
                </div>
            </div>
        </div>
    </div>
</template>

<script>

import * as utils from '../assets/js/utils.js'

export default {
  name: 'Login',
  props: {
      incomingError: String,
  },
  data() {
    return {
      username: 'Antoine',
      password:'secret',
      games: null,
      token: null,
      user: null,
      board: null,
      selectedCell: null,
      errorMessage: '',
    }
  },
  mounted() {   
  },
  methods: {
    async login() {
        const { token, errorMessage } = await utils.login(this.username, this.password);
        this.token = token;
        this.errorMessage = errorMessage;
        if (this.token) {
            this.$router.push({name:'home', params: {token: this.token}});
        }
    },

    getMyInfo() {
        const requestOptions = {
            method: 'GET',
            headers: { 
                'accept': 'application/json',
                'Authorization': 'Bearer '+ this.token,
            },
        };
        fetch("http://sxbn.org:8080/users/me/", requestOptions)
        .then(async response => {
            const data = await response.json();

            // check for error response
            if (!response.ok) {
                // get error message from body or default to response statusText
                const error = (data && data.message) || response.statusText;
                return Promise.reject(error);
            }
            this.user = `${data.full_name} (${data.username}) - ${data.email} ${data.disabled?"DISABLED":"ENABLED"}`;
        })
        .catch(error => {
        this.errorMessage = error;
        console.error("There was an error!", error);
        });
    },

    listAllGames() {
    fetch("http://localhost:8080/api/games")
    .then(async response => {
      const data = await response.json();

      // check for error response
      if (!response.ok) {
        // get error message from body or default to response statusText
        const error = (data && data.message) || response.statusText;
        return Promise.reject(error);
      }
      if (data.status == true) {
          this.games = data.games;
          this.page = "listgames"
      }
    })
    .catch(error => {
      this.errorMessage = error;
      console.error("There was an error!", error);
    });
    },

    listMyGames() {
        const requestOptions = {
        method: 'GET',
        headers: { 
                'accept': 'application/json',
                'Authorization': 'Bearer '+ this.token,
            },
        };
        fetch('http://sxbn.org:8080/users/me/games/', requestOptions)
            .then(async response => {
                const data = await response.json();

                // check for error response
                if (!response.ok) {
                    // get error message from body or default to response status
                    const error = (data && data.message) || response.status;
                    return Promise.reject(error);
                }
                this.games = data;
                this.page = "listgames";
            })
            .catch(error => {
                    this.errorMessage = error;
                    console.error('There was an error!', error);
            });
    },
    /*
    home() {
        this.page = "home";
    },

    selectCell(event) {
        for (let idx = 0; idx < 64; idx++) {
            let cellid = "c"+String(idx);
            let cell = this.$refs[cellid];
            cell.classList.remove("selected");
        }
        let targetId = event.currentTarget.id;
        if (this.selectedCell == null || this.selectedCell === targetId){
            if (targetId in this.board){
                let cell = this.$refs[targetId];
                cell.classList.add("selected")
                this.selectedCell = targetId;
            }
        } else {
            let origin = this.$refs[this.selectedCell];
            let target = this.$refs[targetId];
            Array.from(target.getElementsByTagName('img')).forEach((element) => {
                target.removeChild(element);
            });
            this.board[targetId] = this.board[this.selectedCell];
            delete this.board[this.selectedCell];
            console.log("moving piece from " + origin + " to " + target);
            target.appendChild(origin.getElementsByTagName('img')[0]);
            this.selectedCell = null;
        }
        this.drawFog();
    },
    
    drawBoard() {
        let data = GAMESTATE;
        this.board = {};
        [...data.board].forEach((element, idx) => {
            let cellid = "c"+String(idx)
            let cell = this.$refs[cellid];
            this.board[cellid] = element;
            if (element != "_") {
                let img = document.createElement("img");
                img.src = "img/" + element + ".svg";
                cell.appendChild(img);
            }
        });
        this.drawFog();
    },

    drawFog() {
        for (let idx = 0; idx < 64; idx++) {
            let cellid = "c"+String(idx)
            let cell = this.$refs[cellid];
            cell.classList.remove("fog");
        }
        const myColor = data.players.white === this.username ? "white":"black";
        const pieces = {"white":"rnbkqp", "black": "RNBKQP"};
        for(let i=0; i<64; i++){
            let neighbors = [-9, -8, -7, -1, 0, 1, 7, 8, 9];
            if (i%8 == 0){
                neighbors = [-8, -7, 0, 1, 8, 9];
            } else if (i%8 == 7){
                neighbors = [-9, -8, -1, 0, 7, 8];
            }
            console.log(i, i%8, neighbors);
            let fog = true;
            neighbors.forEach(n => {
                const cellid = i + n;
                if (cellid < 64 && cellid >= 0) {
                    if (pieces[myColor].includes(this.board["c"+String(cellid)])) {
                        fog = false;
                    }
                } 
            });
            if (fog) {
                let cell = this.$refs["c"+String(i)];
                cell.classList.add("fog");
                console.log("fog in c" + String(i));
            }
        }
    },*/

  },

  created () {
            document.title = "Battlechess -- Login";
        },

}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.flexctn {
    display: flex;
    justify-content: center;
    width:100%;
}

.loginContent {
    width:400px;
}

.center{
    text-align: center;
}

.button {
    margin-top: 10px;
    color: var(--color-5);
    text-decoration: none;
    color: #fff;
    background-color: var(--color-3);
    text-align: center;
    letter-spacing: .5px;
    -webkit-transition: background-color .2s ease-out;
    transition: background-color .2s ease-out;
    cursor: pointer;
    display: block;
    border: none;
    border-radius: 2px;
    display: inline-block;
    height: 36px;
    line-height: 36px;
    padding: 0 16px;
    text-transform: uppercase;
    -webkit-tap-highlight-color: transparent;
    display: inline;
}

.signup {
    float: right;
    margin-top: 10px;
}

.signup > a {
    color: var(--color-0);
}

.myform input[type=text]{
    border-bottom: 1px solid var(--color-3);
}

.myform input[type=text]:focus{
    border-bottom: 1px solid var(--color-0);
}

.myform input[type=password]{
    border-bottom: 1px solid var(--color-3);
}

.myform input[type=password]:focus{
    border-bottom: 1px solid var(--color-0);
}

.myform {
    background-color: var(--color-2);
    padding: 2px 30px 30px 30px;
    border-radius: 3px;
    box-shadow: 0 0 3px var(--color-5);
}

.warning {
    margin-top: 20px;
    box-shadow: 0 0 4px rgb(250, 102, 3);
    padding: 10px;
    border-color: rgb(250, 102, 3);
    border-width: 2px;
    border-style: solid;
    background-color: var(--color-5);
    border-radius: 3px;
    color: var(--color-1);
    font-size: 1.2em;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.warning strong {
    font-weight: 700;
}

.warning  a {
    float:right;
    color: var(--color-1);
    font-size: 1.5em;
}

</style>
