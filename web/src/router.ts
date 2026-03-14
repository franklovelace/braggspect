import { createRouter, createWebHistory } from 'vue-router';
import Workflow from './views/Workflow.vue';
import CodSearch from './views/CodSearch.vue';
import Analysis from './views/Analysis.vue';
import Candidates from './views/Candidates.vue';

const routes = [
  { path: '/', component: Workflow },
  { path: '/search', component: CodSearch },
  { path: '/analysis', component: Analysis },
  { path: '/candidates', component: Candidates }
];

export const router = createRouter({
  history: createWebHistory(),
  routes
});