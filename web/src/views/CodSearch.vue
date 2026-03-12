<script setup lang="ts">
import { ref } from 'vue';
import axios from 'axios';
import XrdChart from '../components/XrDChart.vue';

const query = ref('');
const results = ref<any[]>([]);
const selected = ref<any>(null);

const mockData = {
  x: Array.from({length: 500}, (_, i) => 10 + i * 0.1),
  y: Array.from({length: 500}, () => Math.random() * 100 + Math.exp(-Math.pow(Math.random()-0.5, 2)))
};

const search = async () => {
  const res = await axios.get(`http://localhost:7071/api/search/${query.value}`);
  results.value = res.data;
};
</script>

<template>
  <div class="flex h-screen bg-slate-900 text-slate-100 overflow-hidden">
    <div class="w-80 border-r border-slate-800 p-4 flex flex-col gap-4">
      <h1 class="text-xl font-bold text-blue-400 italic">BRAGG SPECT</h1>
      <div class="flex flex-col gap-2">
        <input v-model="query" @keyup.enter="search" placeholder="Fórmula..." class="bg-slate-800 border border-slate-700 p-2 rounded w-full"/>
        <button @click="search" class="bg-blue-600 p-2 rounded font-bold hover:bg-blue-500 transition">Buscar en COD</button>
      </div>
      
      <div class="overflow-y-auto flex-1 space-y-2">
        <div v-for="res in results" :key="res.id" 
             @click="selected = res"
             :class="['p-3 rounded cursor-pointer border transition', selected?.id === res.id ? 'bg-blue-900/30 border-blue-500' : 'bg-slate-800 border-transparent hover:border-slate-600']">
          <p class="font-bold text-blue-300">COD: {{ res.id }}</p>
          <p class="text-sm">{{ res.formula }}</p>
          <p class="text-xs text-slate-400">{{ res.name }}</p>
        </div>
      </div>
    </div>

    <div class="flex-1 p-6 flex flex-col gap-6 overflow-y-auto">
      <div v-if="selected" class="grid grid-cols-1 gap-6">
        <div class="bg-slate-800 p-4 rounded-xl shadow-xl">
          <h2 class="text-lg font-bold mb-4 flex items-center gap-2">
            <span class="w-3 h-3 bg-blue-500 rounded-full"></span>
            Difractograma Experimental
          </h2>
          <XrdChart :twoTheta="mockData.x" :intensity="mockData.y" />
        </div>

        <div class="grid grid-cols-3 gap-4">
  <div v-for="val, key in { a: selected.a, b: selected.b, c: selected.c }" 
       class="bg-slate-800/50 p-4 rounded-xl border border-slate-700 text-center relative overflow-hidden group">
    <p class="text-[10px] text-blue-500 font-bold uppercase mb-1 tracking-tighter">{{ key }} (Å)</p>
    <p class="text-2xl font-mono text-white">{{ val?.toFixed(3) || '—' }}</p>
    <div class="absolute bottom-0 left-0 w-full h-1 bg-blue-600 opacity-20 group-hover:opacity-100 transition-opacity"></div>
  </div>

  <div v-for="val, key in { 'α': selected.alpha, 'β': selected.beta, 'γ': selected.gamma }" 
       class="bg-slate-800/50 p-4 rounded-xl border border-slate-700 text-center relative overflow-hidden group">
    <p class="text-[10px] text-orange-500 font-bold uppercase mb-1 tracking-tighter">{{ key }} (°)</p>
    <p class="text-2xl font-mono text-white">{{ val?.toFixed(2) || '—' }}</p>
    <div class="absolute bottom-0 left-0 w-full h-1 bg-orange-600 opacity-20 group-hover:opacity-100 transition-opacity"></div>
  </div>
</div>
      </div>

      <div v-else class="flex-1 flex items-center justify-center text-slate-600">
        <p class="text-xl">Selecciona un resultado de la COD para ver sus detalles</p>
      </div>
    </div>
  </div>
</template>