<template>
<div class="games">
    <ul class="menu">
        <li class="tab live"
        v-bind:class="{active: currentList=== 'live'}"><a href="#" @click="showLive">Live</a></li>
        <li class="tab finished"
        v-bind:class="{active: currentList=== 'finished'}"><a href="#" @click="showFinished">Finished</a></li>
        <li class="tab open"
        v-bind:class="{active: currentList=== 'open'}"><a href="#" @click="showOpen">Open</a></li>
        <li class="tab right valign-wrapper"><a href="#" @click="showNewGameModal"><i class="material-icons">add</i></a></li>
    </ul>

    <!-- <div v-if="(currentList!='open' && games.length === 0) || (currentList=='open' && (games.length+myOpenGames.length) === 0)" class="gamesCol"> -->
    <div v-if="games.length === 0" class="gamesCol">
        <div class="gamesRow">
            <div class="valign-wrapper col-12 text-color-5 push-center">
                So empty...
            </div>
        </div>
    </div>

    <div v-else class="gamesCol">
        <div class="gamesRow" v-for="game in games"
             v-bind:class="{ canjoin: game.canJoin || currentList === 'live' }" 
             v-bind:key="game"
             @click="clicked(game)">
            <div class="opponents">
                <div v-if="game.white == null" class="whitePlayer">
                    Not Set
                </div>
                <div v-else class="whitePlayer">
                    <div  class="avatar"
                    v-bind:class="{ activeWhite: game.turn === 'white'}">
                        <img :src="game.white.avatar" alt="" class="circle gamePlayerImg">
                    </div>
                    <div class="paddedText"> 
                        {{game.white.username}}
                    </div>
                </div>
                <div class="versus">
                Vs.
                </div>
                <div v-if="game.black == null" class="blackPlayer">
                    Not Set
                </div>
                <div v-else class="blackPlayer">
                    <div class="paddedText">
                        {{game.black.username}}
                    </div>
                    <div class="avatar"
                    v-bind:class="{ activeBlack: game.turn === 'black'}">
                        <img :src="game.black.avatar" alt="" class="circle gamePlayerImg">
                    </div>
                </div>
            </div>
            <div class="col-1">  
            </div>
            <div v-if="currentList === 'live'" class="gameInfo">
                <div>
                    Last move: 
                    <span class="tooltip">
                        {{game.lastmoveText.text}}
                        <span class="tooltiptext">
                            {{game.lastmoveText.tooltip}}
                        </span>
                    </span>
                </div>       
            </div>
            <div v-if="currentList === 'finished'" class="gameInfo">
                <div>

                    <span v-if="game.winner.userId == userId" class="valign-wrapper">Won<i class="material-icons tiny">emoji_events</i></span>
                    <span v-else>Lost</span>
                </div>
            </div>
            <div v-if="currentList === 'open'" class="gameInfo">
                <div class="valign-wrapper">
                    <span class="bold"><i class="material-icons tiny">{{game.public?"lock_open":"lock"}}</i></span>{{game.public?"Public":"Private"}}
                </div>
                <div class="valign-wrapper">
                    <span class="bold">#</span>{{game.hash}}
                </div>
            </div>
        </div>
    </div>
    <Modal
      v-show="isModalVisible"
      @close="closeModal"
      :parrentCallback="getGames"
    />
</div>
</template>

<script>
import * as utils from '../assets/js/utils.js'
import {source} from '../assets/js/store.js'
import Modal from './modalNewGame.vue'

Array.prototype.sample = function(){
  return this[Math.floor(Math.random()*this.length)];
};

export default {
  name: 'Games',
  components: {
      Modal,
  },
  data() {
      return {
          token: '',
          username: null,
          userId: null,
          avatar: null,
          games: [],
          liveGames: [],
          finishedGames: [],
          openGames: [],
          myOpenGames: [],
          currentList: 'live',
          isModalVisible: false,
          canjoin: false,
          timer: null,
      }
  },
  created(){
        if(localStorage.token && localStorage.username && localStorage.userId && localStorage.userAvatar){
            this.token = localStorage.token;
            this.username = localStorage.username;
            this.userId = localStorage.userId;
            this.avatar = localStorage.avatar;
        } else {
            this.$router.push({name:'login', params: {}});
        }
      this.init();
      },  
  mounted () {
  },

  beforeUnmount() {
    if(this.timer) {
        clearTimeout(this.timer);
        this.timer = null;
    }
    },

  methods: {

      startTimer() {
            this.timer = setTimeout(async () => {
                await this.fetchGames();
                this.startTimer();
            }, 3000);
        },

    init() {
        this.getGames();
        this.startTimer();
    },

    async fetchGames() {
        const { liveGames, finishedGames, myOpenGames, error } = await utils.getUserGames(this.token);
        const { openGames , error2 } = await utils.getOpenGames(this.token);
        if (liveGames != this.liveGames) {
            this.liveGames = liveGames;
        }
        if (finishedGames != this.finishedGames) {
            this.finishedGames = finishedGames;
        }
        if (myOpenGames != this.myOpenGames) {
            this.myOpenGames = myOpenGames;
        }
        if (openGames != this.openGames) {
            this.openGames = openGames;
        }
        if (this.currentList === 'open'){
            this.games = this.myOpenGames.concat(this.openGames);
        }

    },

    async getGames() {
        const { liveGames, finishedGames, myOpenGames, error } = await utils.getUserGames(this.token);
        const { openGames , error2 } = await utils.getOpenGames(this.token);
        this.liveGames = liveGames;
        this.finishedGames = finishedGames;
        this.myOpenGames = myOpenGames;
        this.openGames = openGames;
        if (error || error2) {
            this.$router.push({name:'login', params: {incomingError: error + " " + error2 }});
        } else {
            switch (this.currentList) {
                case 'live':
                    this.games = this.liveGames;
                    break;
                case 'finished':
                    this.games = this.finishedGames;
                    break;
                case 'open':
                    this.games = this.myOpenGames.concat(this.openGames);
                    break;
                default:
                    break;
            }
        }

    },

  async clicked(game) {
      if (this.currentList === 'open'){
          await this.join(game);
          this.fetchGames();
      } else if (this.currentList === 'live') {
          this.play(game);
      }
  },

  play(game) {
      localStorage.activeGame = game.hash;
      this.$router.push({name:'game'});
  },

  async join(game) {
      if (game.canJoin) {
          const { error } = await utils.joinGame(this.token, game.hash);
          if (error) {
              console.log("error joining a game", error);
          }
      }
  },
  showLive() {
      if (this.currentList != 'live'){
          this.currentList = 'live';
          this.games = this.liveGames;
      }
  },
  showFinished() {
      if (this.currentList != 'finished'){
          this.currentList = 'finished';
          this.games = this.finishedGames;
      }
  },
  showOpen() {
      if (this.currentList != 'open'){
          this.currentList = 'open'
          this.games = this.myOpenGames.concat(this.openGames);
      }
  },
  showNewGameModal() {
        this.isModalVisible = true;
  },
  closeModal() {
        this.isModalVisible = false;
        this.fetchGames();
  },
}




}
</script>


<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.canjoin {
   cursor: pointer; 
}

.gameCol {
    width: 100%;
    height: 100%;
}

.opponents {
    width: 75%;
    display: flex;
    align-items: center;
}

.whitePlayer {
    width: 45%;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    color: var(--color-5);
}

.blackPlayer {
    width: 45%;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    color: var(--color-5);
}

.versus {
    width: 10%;
    font-weight: 700;
    color: var(--color-5);
    font-family:sans-serif;
    padding-left: 10px;
    padding-right: 10px;
}

.username-name {
    padding-left: 2em;
    padding-top: 0.5em;
}

.gamesRow {
    background-color: var(--color-2);
    border-radius: 3px;
    height:80px;
    /* width: 60%; */
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    padding-left: 10px;
}

.gamesRow:hover {
    background-color: var(--color-3);
}

.gamePlayerImg {
    height: 100%;
    width: 100%;
    padding: 5%;
}

.activeWhite {
    border: 2px solid var(--color-5);
    border-radius: 9999px;
    box-shadow: 0 0 3px var(--color-5);
}

.activeBlack {
    border: 2px solid var(--color-5);
    border-radius: 9999px;
    box-shadow: 0 0 3px var(--color-5);
}


.avatar {
    height: 40px;
    width: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.avatar > img {
    height: 38px;
    width: 38px;
}

.paddedText {
    color: var(--color-5);
    font-family:sans-serif;
    padding-left: 10px;
    padding-right: 10px;
    font-weight: 500;
}

.gameInfo {
    width: 33.3333%;
    color: var(--color-5);
    font-family:sans-serif;
    padding-left: 10px;
    padding-right: 10px;
    font-weight: 500;
    display: flex;
    flex-direction: column;
}

.gameInfo > div {
    display: flex;
    gap: 0.2em;
}

.bold {
    font-weight: 700;
}

/* Tooltip container */
.tooltip {
  position: relative;
  display: inline-block;
}

/* Tooltip text */
.tooltip .tooltiptext {
  visibility: hidden;
  width: 140px;
  background-color: var(--color-4);
  color: var(--color-1);
  text-align: center;
  font-size: 0.8em  ;
  padding: 5px 0;
  border-radius: 3px;
 
  /* Position the tooltip text - see examples below! */
  position: absolute;
  width: 140px;
  top: 100%;
  left: 50%;
  margin-left: -70px;
  z-index: 1;
}

.tooltip .tooltiptext::after {
  content: " ";
  position: absolute;
  bottom: 100%; /* At the bottom of the tooltip */
  left: 50%;
  margin-left: -5px;
  border-width: 5px;
  border-style: solid;
  border-color: transparent transparent var(--color-4) transparent;
}

/* Show the tooltip text when you mouse over the tooltip container */
.tooltip:hover .tooltiptext {
  visibility: visible;
}

.menu {
    margin-bottom: 8px;
    margin-top: 7.5px;
    border-radius: 3px;
    background-color: transparent;
    position: relative;
    overflow-x: auto;
    overflow-y: hidden;
    height: 48px;
    width: 100%;
    margin: 0 auto;
    white-space: nowrap;
    margin-bottom: 8px;
    margin-top: 7.5px;
}


.menu .tab {
    float: left;
    background-color: var(--color-2);
    text-align: center;
    line-height: 48px;
    height: 48px;
    padding: 0;
    margin: 0;
    text-transform: uppercase;
    border-style: solid;
    border-color: var(--color-5);
}

.live {
    border-radius: 3px 0px 0px 3px;
    border-width: 1px 0 1px 1px;
}

.finished {
    border-radius: 0px 0px 0px 0px;
    border-width: 1px 0 1px 0px;
}

.open {
    border-radius: 0px 3px 3px 0px;
    border-width: 1px 1px 1px 0px;
}

.right {
    float:right;
    border-radius: 3px;
    border-width: 1px;
}

.right .material-icons {
    line-height: 1.9;
}

.menu .tab a {
    color: var(--color-5);
    display: block;
    width: 100%;
    height: 100%;
    padding: 0 24px;
    font-size: 1.1m;
    font-weight: 700;
    text-overflow: ellipsis;
    overflow: hidden;
}

.active {
    text-decoration: underline;
    text-decoration-thickness:2px;
    text-underline-offset: 5px;
}


.push-right {
    display:flex;
    justify-content: flex-end;
}

.push-center {
    display:flex;
    justify-content:center;
}


@media only screen and (max-width: 1110px) {
    .gamesCol {
        height: 100%;
    }
    .gamesRow {
        height:20vh;
    }
    .avatar {
        height: 5vh;
        width: 5vh;
    }

    .opponents {
        width: 50%;
        display: flex;
        flex-direction: column;
    }

    .blackPlayer {
        justify-content: flex-end;
        flex-direction: row-reverse;
    }

}

</style>