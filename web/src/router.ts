import { createRouter, createWebHistory } from 'vue-router';
import Workflow from './views/Workflow.vue';
import CodSearch from './views/CodSearch.vue';

const routes = [
  { path: '/', component: Workflow },
  { path: '/search', component: CodSearch }
];

export const router = createRouter({
  history: createWebHistory(),
  routes
});