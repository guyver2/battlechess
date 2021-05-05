<template>
<div>
    <div class="usercard large">
        <div class="card-panel lighten-5 z-depth-1 color-2 text-color-5  light-border">
            <div class="valign-wrapper">
                <div class="avatar">
                    <img :src="avatar" alt="" class="circle responsive-img">
                </div>
                <div class="userText">
                    <span class="username-name">
                        @{{username}}
                    </span>
                    <span class="username-name valign-wrapper">
                        <i class="material-icons">emoji_events</i>{{victories}}/{{games}} games
                    </span>
                    <span class="username-name valign-wrapper">
                        {{points}} points {{position}}/{{players}}
                    </span>
                </div>
            </div>
        </div>
    </div>

    <div class="usercard small">
        <div class=" valign-wrapper">
            <div class="avatar">
                <img :src="avatar" alt="" class="circle responsive-img">
            </div>
        </div>
    </div>
</div>
</template>

<script>
import * as utils from '../assets/js/utils.js'

export default {
  name: 'UserCard',
  props:{
      avatar: String,
      victories: Number,
      games: Number,
      points: Number,
      position: Number,
      players: Number,
  },
  created(){
      if (localStorage.token) {
          this.token = localStorage.token;
      }
      this.getUserInfo();
  },

  mounted() {
  },
  data() {
      return {
          username: '',
      }
  },

  methods: {
      async getUserInfo() {
        const result = await utils.getUserInfo(this.token);
        this.username = result.username;
        if (!this.username) {
            this.$router.push({name:'login', params: {incomingError: result.error}});
        }
    },
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.username-name {
    padding-left: 2em;
    padding-top: 0.5em;
    float: left;
}

.light-border{
    box-shadow: 0 0 3px var(--color-5);
}

.usercard {
    width: 100%;
    height: 100%;
}

.avatar {
    height: 100%;
    width: 25%;
}

.userText {
    height: 75%;
    width: 58.333333%;
}

@media only screen and (max-width: 1110px) {
    .large {
        display: none;
    }

    .small {
        display: inline;
    }

    .avatar {
        width: 100%;
    }

}


@media only screen and (min-width: 1111px) {
    .large {
        display: inline;
    }
    .small {
        display: none;
    }
}

</style>