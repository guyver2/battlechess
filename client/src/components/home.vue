<template>
  <div class="center">
    <div class="home">
            <div class="row-12 col-12">
                <div class="userCard"><UserCard v-bind:token="token" avatar="./img/canti.png" games="53" victories="27" points="1257" position="17" players="153"/></div>
                <div class="row-8 cell">SCORES</div>
            </div>
                    <div class="row-12 cell">
                        <Games/>
                    </div>

    </div>
  </div>
</template>

<script>
import UserCard from '@/components/userCard.vue';
import Games from '@/components/games.vue';
export default {
    name: 'Home',
  props: {
    token: String,
  },
  components: {
    UserCard,
    Games
  },
  data() {
      return {
          msg: "hello",
      }
  },
  mounted() {
  },
  created() {
      console.log(this.$props.token);
      if (this.$props.token == null) {
          console.log("invalid token", this.$props.token);
          this.$router.push({name:'login', params: {}});
      }
  },
}
</script>


<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

.home {
    display: grid;
    grid-template-columns: 400px 650px;
    column-gap: 30px;
}

.cell {
  margin: 2em;
}


.userCard {
    margin:2em;
    height: 33.3333%;
}

@media only screen and (max-width: 1110px) {
    .home {
        -webkit-box-sizing: border-box;
           -moz-box-sizing: border-box;
                box-sizing: border-box;
        display: grid;
        grid-template-columns: 75px 650px;
        column-gap: 0px;
    }

    .userCard {
        margin: 2em 0 2em 0;
    }
}


.center {
    display: flex;
    justify-content: center;
}

</style>
