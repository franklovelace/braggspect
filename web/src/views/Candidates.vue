<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import XrdChart from '../components/XrDChart.vue';

const candidates = ref<any[]>([]);
const drxData = ref<any>(null);
const selectedCandidate = ref<any>(null);
const theoreticalData = ref<any>(null);
const isModalOpen = ref(false);
const loading = ref(false);

onMounted(() => {
  const state = window.history.state;
  
  if (state && state.candidates) {
    candidates.value = typeof state.candidates === 'string' 
      ? JSON.parse(state.candidates) 
      : state.candidates;
  }
  
  const savedData = localStorage.getItem('current_drx_data');
  if (savedData) {
    drxData.value = JSON.parse(savedData);
    console.log("Datos recuperados con éxito:", drxData.value);
  } else {
    console.error("No se encontraron datos en localStorage");
  }
});

const openComparison = async (c: any) => {
  if (!drxData.value) {
    alert("Error: Datos experimentales no encontrados. Reintente la carga.");
    return;
  }

  selectedCandidate.value = c;
  isModalOpen.value = true;
  loading.value = true;
  theoreticalData.value = null;

  try {
    const res = await axios.get('http://localhost:8000/api/math/simulate', {
      params: {
        a: c.a || 1, b: c.b || 1, c: c.c || 1,
        alpha: c.alpha || 90, beta: c.beta || 90, gamma: c.gamma || 90,
        anode: drxData.value.anode || 'Cu',
        tmin: drxData.value.twoTheta?.[0] || 20,
        tmax: drxData.value.twoTheta?.[drxData.value.twoTheta.length - 1] || 70
      }
    });
    theoreticalData.value = res.data;
  } catch (e) {
    console.error("Error simulando:", e);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="p-8 h-full bg-slate-900 overflow-y-auto relative">
    <div class="flex justify-between items-center mb-8 border-b border-slate-800 pb-4">
      <h1 class="text-3xl font-bold text-white italic">Candidatos Hanawalt</h1>
      <button @click="$router.back()" class="text-slate-400 hover:text-white transition">← Volver al Análisis</button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div v-for="c in candidates" :key="c.id" 
           @click="openComparison(c)"
           class="bg-slate-800 p-4 rounded-xl border border-slate-700 hover:border-blue-500 cursor-pointer transition transform hover:-translate-y-1 shadow-lg">
        <p class="text-[10px] font-mono text-blue-400 mb-1">COD: {{ c.id }}</p>
        <h3 class="text-lg font-bold text-white leading-tight mb-2">{{ c.name }}</h3>
        <p class="text-xs text-slate-400 italic mb-3">{{ c.formula }}</p>
        <div class="flex gap-2 text-[10px] font-mono text-slate-500">
            <span>a:{{c.a?.toFixed(2)}}</span> <span>b:{{c.b?.toFixed(2)}}</span> <span>c:{{c.c?.toFixed(2)}}</span>
        </div>
      </div>
    </div>

    <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div class="bg-slate-900 border border-slate-700 w-full max-w-5xl max-h-[90vh] rounded-2xl shadow-2xl flex flex-col">
        
        <div class="p-6 border-b border-slate-800 flex justify-between items-center">
          <div>
            <h2 class="text-2xl font-bold text-white">{{ selectedCandidate?.name }}</h2>
            <p class="text-sm text-slate-400 font-mono">{{ selectedCandidate?.formula }} | COD ID: {{ selectedCandidate?.id }}</p>
          </div>
          <button @click="isModalOpen = false" class="text-slate-500 hover:text-white text-3xl font-light">&times;</button>
        </div>

        <div class="p-6 overflow-y-auto">
          <div class="bg-slate-950 p-4 rounded-xl border border-slate-800 relative">
            <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-slate-950/50 z-10 rounded-xl">
               <span class="text-blue-400 font-bold animate-pulse font-mono uppercase tracking-widest">Calculando Curva Teórica...</span>
            </div>
            
            <h3 class="text-xs font-bold text-slate-500 mb-4 uppercase tracking-widest flex items-center gap-4">
               <span class="flex items-center gap-1"><i class="w-3 h-3 bg-blue-500 rounded-full inline-block"></i> Experimental</span>
               <span class="flex items-center gap-1"><i class="w-3 h-3 bg-red-500 rounded-full inline-block"></i> Teórico (Bragg)</span>
            </h3>

            <XrdChart 
            v-if="drxData && !loading" 
            :two-theta="drxData.twoTheta" 
            :intensity="drxData.intensity"
            :theoretical-data="theoreticalData"
            />
          </div>

          <div class="grid grid-cols-6 gap-4 mt-6">
            <div v-for="v, k in {a:selectedCandidate.a, b:selectedCandidate.b, c:selectedCandidate.c, α:selectedCandidate.alpha, β:selectedCandidate.beta, γ:selectedCandidate.gamma}" 
                 class="bg-slate-800/50 p-2 rounded border border-slate-700 text-center">
               <p class="text-[9px] text-slate-500 uppercase">{{k}}</p>
               <p class="text-sm font-mono text-white">{{v || '--'}}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>