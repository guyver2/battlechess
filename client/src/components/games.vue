<template>
<div class="games">
    <ul class="menu">
        <li class="tab live"
        v-bind:class="{active: currentList=== 'live'}"><a href="#" @click="showLive">Live</a></li>
        <li class="tab finished"
        v-bind:class="{active: currentList=== 'finished'}"><a href="#" @click="showFinished">Finished</a></li>
        <li class="tab right"
        v-bind:class="{active: currentList=== 'open'}"><a href="#" @click="showOpen">Open</a></li>
    </ul>

    <div v-if="games.length === 0" class="gamesCol">
        <div class="gamesRow">
            <div class="valign-wrapper col-12 text-color-5 push-center">
                So empty...
            </div>
        </div>
    </div>

    <div v-else class="gamesCol">
        <div class="gamesRow" v-for="game in games" v-bind:key="game">
            <div class="opponents">
                <div class="whitePlayer">
                    <div class="avatar"
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
                <div class="blackPlayer">
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
                    <span class="bold">{{game.moves}}</span> moves
                </div>
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
                    <span class="bold">{{game.moves}}</span> moves
                </div>
                <div>
                    <span v-if="game[game.turn].username === player.username" class="valign-wrapper">Won<i class="material-icons tiny">emoji_events</i></span>
                    <span v-else>Lost</span>
                </div>
            </div>
        </div>
    </div>
    
</div>
</template>

<script>
const users = [
{
    "username":"@Alerthcsa",
    "avatar":"./img/avatar_01.jpeg",
},
{
    "username":"@Anthent",
    "avatar":"./img/avatar_02.jpeg",
},
{
    "username":"@Baldervi",
    "avatar":"./img/avatar_03.jpeg",
},
{
    "username":"@Bencock",
    "avatar":"./img/avatar_04.jpeg",
},
{
    "username":"@Benthard",
    "avatar":"./img/avatar_05.jpeg",
},
{
    "username":"@BorgSomber",
    "avatar":"./img/avatar_06.jpeg",
},
{
    "username":"@Conciom",
    "avatar":"./img/avatar_07.jpeg",
}, 
{
    "username":"@Eyesas",
    "avatar":"./img/avatar_08.jpeg",
},
{
    "username":"@Minadisu",
    "avatar":"./img/avatar_09.jpeg",
},
{
    "username":"@Cribbin",
    "avatar":"./img/avatar_10.jpeg",
},
{
    "username":"@Paramti",
    "avatar":"./img/avatar_11.jpeg",
},
{
    "username":"@Peopen",
    "avatar":"./img/avatar_12.jpeg",
},
{
    "username":"@SaberGhoul",
    "avatar":"./img/avatar_13.jpeg",
},
];

const localUser = {
    "username": "@Antoine",
    "avatar": "./img/canti.png",
};

Array.prototype.sample = function(){
  return this[Math.floor(Math.random()*this.length)];
};

function diff_minutes(date) {
  const now = new Date(); 
  let diff =(now.getTime() - (new Date(date)).getTime()) / 1000;
  diff /= 60;
  return Math.abs(Math.round(diff));
 }

 function fancyDateText(date) {
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

function createGame(status="open") {
    var game = {}
    if (Math.floor(Math.random() * 2) == 0){
        game.white = users.sample();
        game.black = localUser;
    } else {
        game.black = users.sample();
        game.white = localUser;
    }
    game.moves = Math.floor(Math.random() * 50);
    game.turn = (Math.floor(Math.random() * 2) == 0) ? "white":"black";
    game.status = status;
    var d = new Date();
    d.setDate(d.getDate() - Math.floor(Math.random()*15));
    game.lastmove = d.toLocaleString();
    game.lastmoveText = fancyDateText(d);
    return game;
}

function sortGames(a, b) {
    const keyA = new Date(a.lastmove);
    const keyB = new Date(b.lastmove);
    if (keyA < keyB) return 1;
    if (keyA > keyB) return -1;
    return 0;
}


export default {
  name: 'Games',
  props:{
  },
  data() {
      return {
          player: localUser,
          games: [],
          liveGames: [],
          finishedGames: [],
          openGames: [],
          currentList: 'live',
      }
  },
  
  mounted () {
        for (let i=0; i< 5; i++) {
            this.liveGames.push(createGame());
        }
        for (let i=0; i< 20; i++) {
        this.finishedGames.push(createGame("over"));
        }
        this.liveGames.sort(sortGames);
        this.finishedGames.sort(sortGames);
        this.games = this.liveGames;
  },
  methods: {
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
          this.games = this.openGames;
      }
  },
  }




}
</script>


<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
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
}

.blackPlayer {
    width: 45%;
    display: flex;
    align-items: center;
    justify-content: flex-end;
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
    border-radius: 0px 3px 3px 0px;
    border-width: 1px 1px 1px 0px;
}

.right {
    float:right;
    border-radius: 3px;
    border-width: 1px;
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