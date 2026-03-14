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

const isScored = ref(false);
const isRanking = ref(false);

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

const runFastMatch = async () => {
  if (!drxData.value) return;
  
  isRanking.value = true;
  try {
    const res = await axios.post('http://localhost:8000/api/math/fast-match', {
      x: drxData.value.twoTheta,
      y: drxData.value.intensity,
      candidates: candidates.value,
      anode: drxData.value.anode || 'Cu'
    });
    
    candidates.value = res.data; 
    isScored.value = true;
  } catch (e) {
    console.error("Error en Fast Match:", e);
    alert("Error al procesar el ranking de candidatos.");
  } finally {
    isRanking.value = false;
  }
};

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
      <div>
        <h1 class="text-3xl font-bold text-white italic">Candidatos Hanawalt</h1>
        <p class="text-slate-400 text-sm mt-1">Total encontrados: {{ candidates.length }}</p>
      </div>
      
      <div class="flex items-center gap-6">
        <button 
          @click="runFastMatch" 
          :disabled="isRanking || candidates.length === 0"
          class="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2.5 rounded-lg font-bold transition shadow-[0_0_15px_rgba(37,99,235,0.4)] flex items-center gap-2 disabled:opacity-50 disabled:shadow-none"
        >
          <svg v-if="isRanking" class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ isScored ? 'Actualizar Ranking' : 'Ranking por Intensidad' }}
        </button>
        
        <button @click="$router.back()" class="text-slate-400 hover:text-white transition">← Volver al Análisis</button>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div v-for="c in candidates" :key="c.id" 
           @click="openComparison(c)"
           class="bg-slate-800 p-4 rounded-xl border border-slate-700 hover:border-blue-500 cursor-pointer transition transform hover:-translate-y-1 shadow-lg relative">
        
        <div v-if="c.match_score !== undefined" class="absolute top-4 right-4 text-right">
           <p class="text-[9px] text-slate-500 uppercase font-bold tracking-wider mb-0.5">Match</p>
           <p :class="['text-xl font-bold leading-none', c.match_score >= 70 ? 'text-green-400' : (c.match_score >= 40 ? 'text-yellow-400' : 'text-orange-500')]">
             {{ c.match_score }}%
           </p>
        </div>

        <p class="text-[10px] font-mono text-blue-400 mb-1">COD: {{ c.id }}</p>
        <h3 class="text-lg font-bold text-white leading-tight mb-2 pr-16">{{ c.name || 'Fase Desconocida' }}</h3>
        <p class="text-xs text-slate-400 italic mb-3">{{ c.formula }}</p>
        
        <div class="flex gap-2 text-[10px] font-mono text-slate-500">
            <span>a: {{c.a?.toFixed(2) || '--'}}</span> 
            <span>b: {{c.b?.toFixed(2) || '--'}}</span> 
            <span>c: {{c.c?.toFixed(2) || '--'}}</span>
        </div>
      </div>
    </div>

    <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div class="bg-slate-900 border border-slate-700 w-full max-w-5xl max-h-[90vh] rounded-2xl shadow-2xl flex flex-col">
        
        <div class="p-6 border-b border-slate-800 flex justify-between items-center">
          <div>
            <h2 class="text-2xl font-bold text-white">{{ selectedCandidate?.name || 'Fase Desconocida' }}</h2>
            <p class="text-sm text-slate-400 font-mono">{{ selectedCandidate?.formula }} | COD ID: {{ selectedCandidate?.id }}</p>
          </div>
          <button @click="isModalOpen = false" class="text-slate-500 hover:text-white text-3xl font-light">&times;</button>
        </div>

        <div class="p-6 overflow-y-auto">
          <div class="bg-slate-950 p-4 rounded-xl border border-slate-800 relative">
            <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-slate-950/50 z-10 rounded-xl backdrop-blur-[2px]">
               <span class="text-blue-400 font-bold animate-pulse font-mono uppercase tracking-widest">Calculando Curva Teórica...</span>
            </div>
            
            <h3 class="text-xs font-bold text-slate-500 mb-4 uppercase tracking-widest flex items-center gap-4">
               <span class="flex items-center gap-1"><i class="w-3 h-3 bg-blue-500 rounded-full inline-block shadow-[0_0_5px_#3b82f6]"></i> Experimental</span>
               <span class="flex items-center gap-1"><i class="w-3 h-3 bg-red-500 rounded-full inline-block shadow-[0_0_5px_#ef4444]"></i> Teórico (Bragg)</span>
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