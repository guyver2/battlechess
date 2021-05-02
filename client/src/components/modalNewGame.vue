<template>
  <transition name="modal-fade">
    <div class="modal-backdrop">
      <div class="modal">
        <header class="modal-header" id="modalTitle">
          <slot name="header">
            New Game creation
          </slot>
          <button type="button" class="btn-close" @click="close">
            <i class="material-icons">close</i>
          </button>
        </header>

        <section class="modal-body" id="modalDescription">
          <form>
              <label for="color">Choose a color:</label>
              <select class="colorSelect" id="color" name="color" v-model="color">
                <option value="random" selected>Random</option>
                <option value="white">White</option>
                <option value="black">Black</option>
              </select>
              Make game
              <label for="public_private">
              <input type="radio" id="public_private" value="public" class="ppradio" v-model="publicPrivate">
                Public
              </label>
              <label for="private_public">
              <input type="radio" id="private_public" value="private" class="ppradio" v-model="publicPrivate">
                Private
              </label>
          </form>
        </section>

        <footer class="modal-footer">
          <button type="button" class="btn-cancel" @click="close">
            Cancel
          </button>
          <button type="button" class="btn-confirm" @click="confirm">
            Confirm
          </button>
        </footer>
      </div>
    </div>
  </transition>
</template>

<script>
import * as utils from '../assets/js/utils.js'

  export default {
    name: 'Modal',
    props:{
      token: String,
  },
  created() {
      console.log("props", this.$props);
      this.localToken = this.$props.token;
  },
    data () {
        return {
            color: "random",
            publicPrivate: "private",
            localToken: null,
        };
    },
    methods: {
      close() {
        this.$emit('close');
      },
      async confirm() {
          console.log("token:", this.localToken);
          let error = await utils.createGame(this.localToken, this.color, this.publicPrivate);
          if (error) {
              console.log(error);
          }
      }
    },
  };
</script>


<style>
  .modal-backdrop {
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    right: 0;
    background-color: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .modal {
    background: var(--color-3);
    box-shadow: 2px 2px 20px 1px;
    overflow-x: auto;
    display: flex;
    flex-direction: column;
    height: 40%;
    width:30%;
  }

  .modal-header,
  .modal-footer {
    padding: 15px;
    display: flex;
    font-size: 1.5em;
    font-weight: 700;
  }

  .modal-header {
    position: relative;
    /* border-bottom: 1px solid #eeeeee; */
    color: var(--color-5);
    justify-content: space-between;
  }

  .modal .modal-footer {
    /* border-top: 1px solid #eeeeee; */
    flex-direction: row;
    justify-content: flex-end;
    background-color: var(--color-3);
    margin-bottom: 10px;
  }

  .modal-body {
    position: relative;
    padding: 20px 10px;
    height: 70%;
  }

  .btn-close {
    position: absolute;
    top: 0;
    right: 0;
    border: none;
    font-size: 20px;
    padding: 10px;
    cursor: pointer;
    font-weight: bold;
    color: var(--color-5);
    background: transparent;
  }

  .btn-confirm {
    color: var(--color-5);
    background: var(--color-2);
    border: 1px solid var(--color-5);
    border-radius: 3px;
    margin: 0px 10px 0px 10px;
  }

  .btn-cancel {
    color: var(--color-5);
    background: var(--color-2);
    border: 1px solid var(--color-5);
    border-radius: 3px;
    margin: 0px 10px 0px 10px;
  }

  .modal-fade-enter,
  .modal-fade-leave-to {
    opacity: 0;
  }

  .colorSelect {
      display: block;
  }

  .modal .ppradio{
      opacity: 1;
      position: relative;
      margin-right: 5px;
  }

  .modal-fade-enter-active,
  .modal-fade-leave-active {
    transition: opacity .5s ease;
  }
</style>