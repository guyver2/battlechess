<template>
    <div class="board">
        <div v-for="index in 64" :key="index"
        class="boardCell" 
        :ref="'c'+String(index-1)"
        :id="'c'+String(index-1)"
        :class="{ 'blackCell': ((index-1)%8)%2 != (Math.floor((index-1)/8))%2,
                'whiteCell': ((index-1)%8)%2 === (Math.floor((index-1)/8))%2 }"
        v-on:click="selectCell($event)"> 
        {{"ABCDEFGH"[Math.floor(((index-1)/8))]}}{{8-(index-1)%8}} 
        </div>            
    </div>
</template>

<script>
/*import * as utils from '../assets/js/utils.js'*/

export default {



    props: {
        game: String,
    },
    mounted() {
        this.drawBoard();
    },

    data () {
        return {
            data:{
                    "gameID": "sdhsahda5551",
                    "board":"RNBQKBNRPPPPPPPP________________________________pppppppprnbqkbnr",
                    "taken":[],
                    "castelable":[],
                    "turn":"w",
                    "status":"started",
                    "players": {
                        "white": {"username": "john doe", "userid":"1212151"},
                        "black": "mary moe",
                        }
                    },
            board:{},
            selectedCell:null,
        }
    }, 

    methods: {
        selectCell(event) {
            for (let idx = 0; idx < 64; idx++) {
                let cellid = "c"+String(idx)
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
            this.board = {};
            [...this.data.board].forEach((element, idx) => {
                let cellid = "c"+String(idx)
                let cell = this.$refs[cellid];
                this.board[cellid] = element;
                if (element != "_") {
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
            const myColor = this.data.players.white === this.username ? "white":"black";
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
  color: var(--color-2);
}

.whiteCell.fog {
  background: var(--color-4-d);
  color: var(--color-1);
}

.blackCell {
    background: var(--color-2);
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