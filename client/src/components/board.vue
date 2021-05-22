<template>
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
</template>

<script>
import * as utils from '../assets/js/utils.js'

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
      this.init();
      },  

    mounted() {
    },

    data () {
        return {
            gameID: String,
            snaps: Array,
            data: Map,
            color: String,
            // data:{
            //         "gameID": "sdhsahda5551",
            //         "board":"RNBQKBNRPPPPPPPP________________________________pppppppprnbqkbnr",
            //         "taken":[],
            //         "castelable":[],
            //         "turn":"w",
            //         "status":"started",
            //         "players": {
            //             "white": {"username": "john doe", "userid":"1212151"},
            //             "black": "mary moe",
            //             }
            //         },
            board:{},
            selectedCell:null,
            possibleMoves:[],
        }
    },

    methods: {
        
        async init() {
            await this.getGameInfo();
            await this.getSnaps();
            this.drawBoard();
        },

        async getGameInfo() {
           const {game, error} = await utils.getGame(this.token, this.gameID);
          if(error) {
              console.log("error while getting game info", error);
              this.$router.push({name:'home', params: {incomingError: "error while fetching game status"}});
          }
          this.game = game;
          this.color = game.white_id == localStorage.userId? "white":"black";
          console.log(this.color);
          console.log(game);
        },

        async getSnaps() {
           const {snaps, error} = await utils.getGameSnaps(this.token, this.gameID);
          if(error) {
              console.log("error while getting snaps", error);
              this.$router.push({name:'home', params: {incomingError: "error while fetching game status"}});
          }
          console.log(snaps);
          this.snaps = snaps;
          this.data = this.snaps[0];
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
                    this.data = snap;
                    this.drawBoard();
                } else {
                    console.log(error);
                }

                /*
                Array.from(target.getElementsByTagName('img')).forEach((element) => {
                    target.removeChild(element);
                });
                this.board[targetId] = this.board[this.selectedCell];
                delete this.board[this.selectedCell];
                console.log("moving piece from " + origin + " to " + target);
                target.appendChild(origin.getElementsByTagName('img')[0]);
                */
               this.selectedCell = null;
            }
            this.drawFog();
        },

        drawBoard() {
            this.board = {};
            [...this.data.board].forEach((element, idx) => {
                let cellid = "c"+String(idx)
                let cell = this.$refs[cellid];
                this.board[cellid] = element;
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