<template>
    <div class="main">
        <div class="mobileMenu">
            <div v-if="loading">
                <h1 class="text-color-5">Loading...</h1>
            </div>
            <div v-if="myturn">
                <h5 class="text-color-5">{{color}} turn (you)</h5>
            </div>
            <div v-else>
                <h5 class="text-color-5">{{otherColor}} turn (not you)</h5>
            </div>
            <div v-if="gameover">
                <h5 class="text-color-5">Game is Over {{winner}} won ({{(winner === color)?"you":"not you"}})</h5>
            </div>
        </div>
            <div v-if="data.value" class="taken">
                <img v-for="index in data.value.taken.length" :key="index" 
                    :src="'./img/pieces/' + data.value.taken.substring(index-1, index) + '.svg'"
                    :class= "{'hidden': data.value.taken.substring(index-1, index).toUpperCase() == data.value.taken.substring(index-1, index) }"
                    > 
            </div>
        <div class="gridGame">
            <div class="board">
                <div v-for="index in 64" :key="index"
                class="boardCell" 
                :ref="'c'+String(index-1)"
                :id="'c'+String(index-1)"
                :class="{ 'blackCell': ((index-1)%8)%2 != (Math.floor((index-1)/8))%2,
                        'whiteCell': ((index-1)%8)%2 === (Math.floor((index-1)/8))%2 }"
                v-on:click="selectCell($event)"> 
                {{"ABCDEFGH"[Math.floor(((index-1)%8))]}}{{Math.ceil(8-(index-1)/8)}} 
                </div>           
            </div>
            <div class="rightPanel">
                <div class="gameInfo">
                    <div v-if="myturn">
                        {{color}} turn (you)
                    </div>
                    <div v-else>
                        {{otherColor}} turn (not you)
                    </div>
                    <div v-if="gameover">
                        Game is Over {{winner}} won ({{(winner === color)?"you":"not you"}})
                    </div>
                </div>
                <div class="moves">
                    <div v-for="snap in snaps" :key="snap" class="moveItem">
                        <div>
                            {{snap.move_number}}.
                        </div>
                        <div> 
                            {{snap.move?snap.move.substring(0,2)+" - "+snap.move.substring(2,4):"?"}}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="taken">
            <div v-if="data.value" >
            <img v-for="index in data.value.taken.length" :key="index" 
                 :src="'./img/pieces/' + data.value.taken.substring(index-1, index) + '.svg'"
                 :class= "{'hidden': data.value.taken.substring(index-1, index).toLowerCase() == data.value.taken.substring(index-1, index) }"
                 > 
            </div>
        </div>
    </div>
</template>

<script>
import * as utils from '../assets/js/utils.js';
import { ref, watch } from 'vue';

export default {

    created(){

        if (localStorage.token) {
            this.token = localStorage.token;
        } else {
            this.$router.push({name:'login', params: {incomingError: "invalid credentials"}});
        }
        if (localStorage.activeGame) {
            this.gameID = localStorage.activeGame;
        } else {
            this.$router.push({name:'home', params: {incomingError: "invalid game id"}});
        }
        watch(this.data, () => {
            this.drawBoard();
        })
        
        this.init();
      },  

    mounted() {
        },
    
    beforeUnmount() {
        if(this.timer) {
            clearTimeout(this.timer);
            this.timer = null;
        }
    },


    data () {
        return {
            myturn: false,
            loading: false,
            gameID: String,
            snaps: Array,
            data: ref({}),
            color: String,
            otherColor: String,
            timer: null,
            board: {},
            selectedCell: null,
            possibleMoves: [],
            gameover: false,
            winner: null,
        }
    },

    methods: {
        
        startTimer() {
            this.timer = setTimeout(async () => {
                if (!this.myturn){
                    await this.getLastSnap();
                } else {
                    //await this.getGameInfo();
                }
                this.startTimer();
            }, 1000);
        },
       
        async init() {
            this.loading = true
            await this.getGameInfo();
            await this.getSnaps();
            this.loading = false;
            this.startTimer();
        },

        async getGameInfo() {
           const {game, error} = await utils.getGame(this.token, this.gameID);
          if(error) {
              console.log("error while getting game info", error);
              this.$router.push({name:'home', params: {incomingError: "error while fetching game status"}});
          }
          this.game = game;
          this.color = game.white_id == localStorage.userId? "white":"black";
          this.otherColor = this.color === "white"? "black":"white";
          if (game.winner != null){
                this.gameover = true;
                this.winner = game.winner;
          }

        },

        async getSnaps() {
           const {snaps, error} = await utils.getGameSnaps(this.token, this.gameID);
          if(error) {
              console.log("error while getting snaps", error);
              this.$router.push({name:'home', params: {incomingError: "error while fetching game status"}});
          }
          this.snaps = snaps;
          this.data.value = this.snaps[0];
          this.myturn = (((this.data.value.move_number % 2) == 0) && this.color === "white") 
                        ||(((this.data.value.move_number % 2) == 1) && this.color === "black");
        },

        async getLastSnap() {
            const promise1 = utils.getGame(this.token, this.gameID);
            const promise2 = utils.getLastGameSnap(this.token, this.gameID);
            const data = await Promise.all([promise1, promise2])
            const { game, _ } = data[0];
            if (game.winner != null){
                this.gameover = true;
                this.winner = game.winner;
            }
            const {snap, error} = data[1];
            if(error) {
                console.log("error while getting snap", error);
                this.$router.push({name:'home', params: {incomingError: "error while fetching game status"}});
            }
            const found = this.snaps.find(elt => elt.id === snap.id);
            if(!found){
                this.snaps.unshift(snap);
                this.data.value = this.snaps[0];
                this.myturn = (((this.data.value.move_number % 2) == 0) && this.color === "white") 
                            ||(((this.data.value.move_number % 2) == 1) && this.color === "black");
            }
        },

        isSelectable(cell) {
           if (cell in this.board) {
               let content = this.board[cell];
                if (this.color === "white") {
                    return "prnbqk".indexOf(content) != -1;
                } else {
                    return "PRNBQK".indexOf(content) != -1;
                }
               }
           return false;
        },

        index2board(cell) {
            const idx = parseInt(cell.substring(1,3));
            return "abcdefgh"[Math.floor(((idx)%8))] + String(Math.ceil(8-(idx)/8));
        },

        board2index(cell) {
            const col = "abcdefgh".indexOf(cell.substring(0,1));
            const row = 8-parseInt(cell.substring(1,2));
            return col+row*8;
        },

        async selectCell(event) {
            // remove selected class
            for (let idx = 0; idx < 64; idx++) {
                let cellid = "c"+String(idx)
                let cell = this.$refs[cellid];
                cell.classList.remove("selected");
            }
            let targetId = event.currentTarget.id;
            let previousSelected = this.selectedCell != null;
            if(this.isSelectable(targetId)) {
                let cell = this.$refs[targetId];
                cell.classList.add("selected")
                this.selectedCell = targetId;
                console.log(this.selectedCell);
                let source = this.index2board(this.selectedCell);
                const {moves, error} = await utils.getPossibleMoves(this.token, this.gameID, source);
                if (error) {
                    console.log(error);
                }
                this.possibleMoves = moves;
                this.drawPossibleMoves();
            } else if(previousSelected) {
                let origin = this.$refs[this.selectedCell];
                let target = this.$refs[targetId];
                origin = this.index2board(origin.id);
                target = this.index2board(target.id);
                const {snap, error} = await utils.move(this.token, this.gameID, origin, target);
                if(error == null) {
                    this.data.value = snap;
                    this.myturn = false;
                } else {
                    console.log(error);
                }
               this.selectedCell = null;
               this.possibleMoves = [];
               this.drawPossibleMoves();
            }
            this.drawFog();
        },
        
        drawBoard() {            
            this.board = {};
            [...this.data.value.board].forEach((element, idx) => {
                let cellid = "c"+String(idx)
                let cell = this.$refs[cellid];
                this.board[cellid] = element;
            
                // clear
                Array.from(cell.getElementsByTagName('img')).forEach((element) => {
                        cell.removeChild(element);
                });
                // draw
                if (element != "_" && element != "x" && element != "X") {
                    let img = document.createElement("img");
                    img.classList.add("imgaeInCell")
                    img.src = "./img/pieces/" + element + ".svg";
                    cell.appendChild(img);
                }
            });
            this.drawFog();
            this.drawPossibleMoves();
        },

        drawFog() {
            for (let idx = 0; idx < 64; idx++) {
                let cellid = "c"+String(idx)
                let cell = this.$refs[cellid];
                cell.classList.remove("fog");
            }
            const pieces = {"white":"rnbkqp", "black": "RNBKQP"};
            for(let i=0; i<64; i++){
                let neighbors = [-9, -8, -7, -1, 0, 1, 7, 8, 9];
                if (i%8 == 0){
                    neighbors = [-8, -7, 0, 1, 8, 9];
                } else if (i%8 == 7){
                    neighbors = [-9, -8, -1, 0, 7, 8];
                }
                let fog = true;
                neighbors.forEach(n => {
                    const cellid = i + n;
                    if (cellid < 64 && cellid >= 0) {
                        if (pieces[this.color].includes(this.board["c"+String(cellid)])) {
                            fog = false;
                        }
                    }
                });
                if (fog) {
                    let cell = this.$refs["c"+String(i)];
                    cell.classList.add("fog");
                }
            }
        },

        drawPossibleMoves() {
            for (let idx = 0; idx < 64; idx++) {
                let cellid = "c"+String(idx)
                let cell = this.$refs[cellid];
                cell.classList.remove("possible");
            }
            for(const pos of this.possibleMoves){
                const cellId = this.board2index(pos);
                let cell = this.$refs["c"+String(cellId)];
                cell.classList.remove("fog");
                cell.classList.add("possible");
            }
        },
    }
}
</script>

<style scoped>

.hidden {
    display: none;
}

.main {
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    height: 100%;
    /* margin-top: -40px; */
    margin-left: 10px;
}

@media all and (orientation:portrait) {

    .main {
        align-items: center;
        justify-content: center;
    }

    .board {
        /* border: 10px solid red; */
        display: grid;
        grid-template-columns: repeat(8, 1fr);
        width: 80vmin;
        height: 80vmin;
        position: relative;
    }

    .boardCell {
        font-family: sans-serif;
        font-weight: bold;
        position: relative;
        padding-left: 0.2vmin;
        height: 10vmin;
        width: 10vmin;
    }

    .rightPanel {
        display: none;
    }

    .taken {
        display: block;
        color: var(--color-5);
        background-color: var(--color-2);
        width: 80vmin;
        height: 5vmin;
        display: flex;
        flex-direction: row;
        justify-content: flex-start;
    }

    .taken img {
        width: 5vmin;
        height: 5vmin;
    }
}


@media all and (orientation:landscape) {
    .mobileMenu {
        display: none;
    }

    .gridGame {
        width: 100%;
        display: grid;
        grid-template-columns: 80vmin 35vmin;
        column-gap: 10px;
    }

    .board {
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    width: 80vmin;
    height: 80vmin;
    position: relative;
    }

    .boardCell {
    font-family: sans-serif;
    font-weight: bold;
    position: relative;
    padding-left: 0.2vmin;
    height: 10vmin;
    width: 10vmin;
    }

    .rightPanel {
        width: 100%;
        height: 80vmin;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    }

    .gameInfo {
        width: 100%;
        height: 20vmin;
        background-color: var(--color-2);
        color: var(--color-5);
        border-style: solid;
        border-color: var(--color-5);
        border-width: 1px;
        border-radius: 3px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        padding-left: 10px;
    }

    .moves {
        width: 100%;
        height: 40vmin;
        background-color: var(--color-1);
        padding: 5px;
        color: var(--color-5);
        border-style: solid;
        border-color: var(--color-5);
        border-width: 1px;
        border-radius: 3px;
        margin-bottom: 8px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        overflow-y: scroll
    }

    .moveItem {
        height: 30px;
        margin-bottom: 10px;
        background-color: var(--color-2);
        color: var(--color-5);
        margin:3px;
        padding: 5px;
        display: grid;
        grid-template-columns: 1fr 8fr;
        column-gap: 10px;
    }

    .taken {
        color: var(--color-5);
        background-color: var(--color-2);
        width: 80vmin;
        height: 5vmin;
        display: flex;
        flex-direction: row;
        justify-content: flex-start;
    }

    .taken img {
        width: 5vmin;
        height: 5vmin;
    }
}


.whiteCell {
  background: var(--color-5);
  color: var(--color-1);
}

.whiteCell.fog {
  background: var(--color-3-d);
  color: var(--color-5);
}

.blackCell {
    background: var(--color-3);
    color: var(--color-5);
}

.blackCell.fog {
  background: var(--color-2-d);
}

.selected {
  background: var(--color-0);
}

.whiteCell.possible {
  background: pink;
  color: var(--color-1);
}

.blackCell.possible {
    background-color: indianred;
    color: var(--color-5);
}


/* these two definitions have no effect, see the same definition in btch.css */
.boardCell img {
  position: absolute;
  top: 0;
  left: 0;
  height: 11.25vmin;
  width: 11.25vmin;
}

.boardCell.fog img {
  display: none;
}

</style>