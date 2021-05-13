import { createApp } from 'vue'

import App from './App.vue'
import Login from './components/login.vue'
import Register from './components/register.vue'
import Home from  './components/home.vue'
import Board from './components/board.vue'



import { createRouter, createWebHistory } from 'vue-router'
const routes = [
  { path: '/', name: 'login', component: Login, props: true },
  { path: '/home', name: 'home', component: Home, props: true },
  { path: '/register', name: 'register', component: Register, props: true },
  { path: '/game', name: 'game', component: Board, props: true }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
});
 
import '@/assets/css/btch.css';
createApp(App).use(router).mount('#app')
