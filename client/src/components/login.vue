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
                <input type="password" id="inputPassword" class="form-control text-color-4" placeholder="password" required v-model="password">
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
      token: null,
      user: null,
      errorMessage: '',
    }
  },
  mounted() {
      localStorage.removeItem('username');
      localStorage.removeItem('userId');
      localStorage.removeItem('userAvatar');
      localStorage.removeItem('token');
      localStorage.removeItem('activeGame');
  },
  methods: {
    async login() {
        const { token, errorMessage } = await utils.login(this.username, this.password);
        this.token = token;
        this.errorMessage = errorMessage;
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



/* on small screen */

@media only screen and (hover: none) {
    .loginContent {
        width:100%;
    }
}

@media only screen and (max-width: 1110px) {
    .loginContent {
        width:100%;
    }
}


</style>
