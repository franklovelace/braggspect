import { createRouter, createWebHistory } from 'vue-router';
import Workflow from './views/Workflow.vue';
import CodSearch from './views/CodSearch.vue';
import Analysis from './views/Analysis.vue';

const routes = [
  { path: '/', component: Workflow },
  { path: '/search', component: CodSearch },
  { path: '/analysis', component: Analysis }
];

export const router = createRouter({
  history: createWebHistory(),
  routes
});