<template>
  <div class="flexctn">
        <div class="loginContent">
            <div v-if="incomingMessage" class="alert alert-warning">
                <a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>
                <strong>Error!</strong> {{incomingMessage}}
            </div>
            <form class="myform">
               <h2 class="form-signin-heading text-color-5 center">Sign up</h2>
                <label for="inputUsername" class="text-color-5">username</label>
                <input type="text" id="inputUsername" class="bcinput text-color-5" placeholder="username" required autofocus  v-model="username">
                <label for="inputEmail" class="text-color-5">email address</label>
                <input type="text" id="inputEmail" class="bcinput text-color-5" placeholder="email" required autofocus  v-model="email">
                <label for="inputPassword" class="text-color-5">password</label>
                <input type="password" id="inputPassword" class="form-control text-color-5" placeholder="password" required v-model="password">
                <label for="inputPassword2" class="text-color-5">repeat password</label>
                <input type="password" id="inputPassword2" class="form-control text-color-5" placeholder="repeat password" required v-model="password2">
                <div class="text-color-5">
                    <button type="button" class="button" v-on:click="register">Sign up</button>
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
  name: 'Register',
  props: {
    incomingMessage: String
  },
  data() {
    return {
        username:'',
        email:'',
        password:'',
        password2:'',
        errorMessage:'',
    }
  },
  methods: {
      async register() {
        const { token, errorMessage } = await utils.register(this.username, this.email, this.password);
        this.token = token;
        if (this.token) {
            localStorage.token = this.token;
            const {username, userId, avatar, error} = await utils.getUserInfo(this.token);
            if (!error) {
                localStorage.username = username;
                localStorage.userId = userId;
                localStorage.userAvatar = avatar;
                this.$router.push({name:'home'});
            }
        }
    },
  },

  created () {
            document.title = "Battlechess -- New Account";
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
