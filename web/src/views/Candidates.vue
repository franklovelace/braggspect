<script setup lang="ts">
import { ref, onMounted } from 'vue';

const candidates = ref<any[]>([]);
const searchPurity = ref<number>(0); 

onMounted(() => {
  const data = history.state.candidates;
  if (data) candidates.value = JSON.parse(data);
});
</script>

<template>
  <div class="p-8 h-full flex flex-col gap-6 overflow-y-auto">
    <div class="flex justify-between items-center border-b border-slate-700 pb-4">
      <div>
        <h1 class="text-3xl font-bold text-white">Candidatos Sugeridos</h1>
        <p class="text-slate-400">Resultados del Método de Hanawalt (Top 20)</p>
      </div>
      <button @click="$router.back()" class="bg-slate-800 px-4 py-2 rounded text-slate-300">Volver</button>
    </div>

    <div v-if="candidates.length" class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div v-for="c in candidates" :key="c.id" 
           class="bg-slate-800 p-5 rounded-xl border border-slate-700 hover:border-blue-500 transition-all cursor-pointer group">
        <div class="flex justify-between items-start mb-3">
          <span class="bg-blue-600/20 text-blue-400 text-xs font-mono px-2 py-1 rounded">COD: {{ c.id }}</span>
          <span class="text-slate-500 text-xs italic">{{ c.year || 'N/A' }}</span>
        </div>
        <h3 class="text-xl font-bold text-white group-hover:text-blue-400 transition">{{ c.name }}</h3>
        <p class="text-sm text-slate-400 font-mono mb-4">{{ c.formula }}</p>
        
        <div class="grid grid-cols-3 gap-2 border-t border-slate-700 pt-3 mt-3">
          <div class="text-center">
            <p class="text-[10px] text-slate-500 uppercase font-bold">a</p>
            <p class="text-sm font-mono text-slate-300">{{ c.a?.toFixed(2) }}</p>
          </div>
          <div class="text-center border-x border-slate-700">
            <p class="text-[10px] text-slate-500 uppercase font-bold">b</p>
            <p class="text-sm font-mono text-slate-300">{{ c.b?.toFixed(2) }}</p>
          </div>
          <div class="text-center">
            <p class="text-[10px] text-slate-500 uppercase font-bold">c</p>
            <p class="text-sm font-mono text-slate-300">{{ c.c?.toFixed(2) }}</p>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="flex-1 flex flex-col items-center justify-center text-slate-500 gap-4">
      <svg class="w-16 h-16 text-slate-700" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 9.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
      <p class="text-xl">No se encontraron candidatos con esas distancias interplanares.</p>
    </div>
  </div>
</template>