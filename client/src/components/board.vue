<template>
    <div>
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
                    await this.getGameInfo();
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
          console.log(snaps);
          this.snaps = snaps;
          this.data.value = this.snaps[0];
          console.log((this.data.value.move_number % 2) == 0, parseInt(localStorage.userId), parseInt(this.game.white_id), parseInt(this.game.black_id));
          this.myturn = (((this.data.value.move_number % 2) == 0) && this.color === "white") 
                        ||(((this.data.value.move_number % 2) == 1) && this.color === "black");
        },

        async getLastSnap() {
            const promise1 = utils.getGame(this.token, this.gameID);
            const promise2 = utils.getLastGameSnap(this.token, this.gameID);
            const data = await Promise.all([promise1, promise2])
            const { game, _ } = data[0];
            console.log(game);
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

        index2board(cell){
            const idx = parseInt(cell.substring(1,3));
            return "abcdefgh"[Math.floor(((idx)%8))] + String(Math.ceil(8-(idx)/8));
        },

        async selectCell(event) {
            // remove selected class
            for (let idx = 0; idx < 64; idx++) {
                let cellid = "c"+String(idx)
                let cell = this.$refs[cellid];
                cell.classList.remove("selected");
            }
            let targetId = event.currentTarget.id;
            console.log("selecting ", targetId);
            console.log(this.board);
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
                console.log(this.possibleMoves);
            } else if(previousSelected) {
                let origin = this.$refs[this.selectedCell];
                let target = this.$refs[targetId];
                console.log(origin.id, typeof(origin.id));
                console.log(target.id, typeof(target.id));
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
    },

}
</script>

<style scoped>

.board {
  /* border: 10px solid red; */
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  grid-template-columns: repeat(8, 1fr);
  width: 90vmin;
  height: 90vmin;
  position: relative;
}

.boardCell {
  font-family: sans-serif;
  font-weight: bold;
  position: relative;
  padding-left: 0.2vmin;
  height: 11.25vmin;
  width: 11.25vmin;
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
  background: var(--color-0);/*rgb(168, 119, 119);*/
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