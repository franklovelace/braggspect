<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import XrdChart from '../components/XrDChart.vue'; 

const router = useRouter();
const candidates = ref<any[]>([]);
const drxData = ref<any>(null);
const selectedCandidate = ref<any>(null);
const theoreticalData = ref<any>(null);

const isModalOpen = ref(false);
const loading = ref(false);
const isRefining = ref(false);

const selectedIds = ref<Set<number>>(new Set());

onMounted(() => {
  const state = window.history.state;
  
  if (state && state.candidates) {
    candidates.value = typeof state.candidates === 'string' 
      ? JSON.parse(state.candidates) 
      : state.candidates;
      
    candidates.value.sort((a, b) => (b.matchScore || 0) - (a.matchScore || 0));
  }
  
  const savedData = localStorage.getItem('current_drx_data');
  if (savedData) {
    drxData.value = JSON.parse(savedData);
  }
});

const allSelected = computed(() => 
  candidates.value.length > 0 && selectedIds.value.size === candidates.value.length
);

const toggleSelectAll = () => {
  if (allSelected.value) {
    selectedIds.value.clear();
  } else {
    candidates.value.forEach(c => selectedIds.value.add(c.id));
  }
};

const toggleCandidate = (id: number, event: Event) => {
  event.stopPropagation();
  if (selectedIds.value.has(id)) selectedIds.value.delete(id);
  else selectedIds.value.add(id);
};

const runBatchRietveld = async () => {
  if (!drxData.value || selectedIds.value.size === 0) return;
  
  isRefining.value = true;
  const toRefine = candidates.value.filter(c => selectedIds.value.has(c.id));
  
  try {
    const res = await axios.post('http://localhost:8000/api/math/rietveld-pruning', {
      x: drxData.value.twoTheta,
      y: drxData.value.intensity,
      candidates: toRefine,
      anode: drxData.value.anode || 'Cu'
    });
    
    candidates.value = res.data;
    selectedIds.value.clear();
    
    if (candidates.value.length > 0) {
      alert(`Refinamiento exitoso. El mejor candidato tiene un FOM de ${candidates.value[0].fom}%`);
    } else {
      alert("La poda fue total: ningún candidato superó las pruebas de consistencia física.");
    }
    
  } catch (e) {
    console.error("Rietveld Error:", e);
    alert("Error crítico en el motor de refinamiento.");
  } finally {
    isRefining.value = false;
  }
};

const openComparison = async (c: any) => {
  if (!drxData.value) return;

  selectedCandidate.value = c;
  isModalOpen.value = true;
  loading.value = true;
  theoreticalData.value = null;

  if (c.is_refined && c.refined_y) {
    theoreticalData.value = { x: drxData.value.twoTheta, y: c.refined_y };
    loading.value = false;
    return;
  }

  try {
    const res = await axios.post('http://localhost:8000/api/math/simulate-peaks', {
      peaks: c.theoreticalPeaks || c.TheoreticalPeaks || [],
      anode: drxData.value.anode || 'Cu',
      tmin: drxData.value.twoTheta[0],
      tmax: drxData.value.twoTheta.at(-1)
    });
    theoreticalData.value = res.data;
  } catch (e) {
    console.error("Sim-Peaks Error:", e);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div v-if="isRefining" class="fixed inset-0 bg-slate-950/90 z-[200] flex flex-col items-center justify-center backdrop-blur-md">
    <div class="relative w-32 h-32 mb-10">
      <div class="absolute inset-0 border-8 border-red-500/10 rounded-full"></div>
      <div class="absolute inset-0 border-8 border-t-red-600 rounded-full animate-spin"></div>
      <div class="absolute inset-0 flex items-center justify-center">
        <span class="text-red-500 font-bold font-mono text-lg animate-pulse">HPC</span>
      </div>
    </div>
    <h2 class="text-3xl font-bold text-white mb-2 tracking-tight">Poda de Rietveld</h2>
    <p class="text-slate-400 font-mono text-sm">Validando consistencia física y topología de {{ selectedIds.size }} fases...</p>
    <div class="mt-12 flex gap-2">
       <div v-for="i in 3" :key="i" class="w-2 h-2 bg-red-600 rounded-full animate-bounce" :style="{animationDelay: `${i*0.2}s`}"></div>
    </div>
  </div>

  <div class="p-8 h-full bg-slate-900 overflow-y-auto relative">
    
    <div class="flex justify-between items-center mb-8 border-b border-slate-800 pb-6">
      <div>
        <h1 class="text-4xl font-black text-white tracking-tighter uppercase italic">Candidatos <span class="text-blue-500">Hanawalt</span></h1>
        <p class="text-slate-500 font-mono text-xs mt-1">Pool de identificación: {{ candidates.length }} estructuras</p>
      </div>
      
      <div class="flex items-center gap-3">
        <button @click="toggleSelectAll" class="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 font-bold hover:bg-slate-700 transition">
          {{ allSelected ? 'Deseleccionar' : 'Marcar Todos' }}
        </button>
        <button 
          @click="runBatchRietveld"
          :disabled="selectedIds.size === 0"
          class="px-6 py-2.5 rounded-lg bg-red-600 text-white font-black uppercase tracking-wider shadow-lg shadow-red-900/40 hover:bg-red-500 disabled:opacity-30 transition-all flex items-center gap-3"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
          Iniciar Poda ({{ selectedIds.size }})
        </button>
        <button @click="router.back()" class="ml-4 p-2 text-slate-500 hover:text-white transition">
           <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div v-for="c in candidates" :key="c.id" 
           @click="openComparison(c)"
           :class="[
             'group p-5 rounded-2xl border-2 transition-all duration-300 relative overflow-hidden',
             selectedIds.has(c.id) ? 'bg-blue-600/10 border-blue-500 shadow-2xl shadow-blue-900/20' : 'bg-slate-800/40 border-slate-800 hover:border-slate-600'
           ]">
        
        <div class="absolute top-4 left-4 z-10" @click.stop>
          <input type="checkbox" :checked="selectedIds.has(c.id)" @change="(e) => toggleCandidate(c.id, e)"
                 class="w-5 h-5 rounded border-slate-700 bg-slate-900 text-blue-500 focus:ring-0 cursor-pointer" />
        </div>

        <div class="absolute top-4 right-4 text-right">
           <p class="text-[10px] text-slate-500 font-black uppercase">{{ c.is_refined ? 'Confianza (FOM)' : 'Match Search' }}</p>
           <p :class="['text-2xl font-black italic leading-none', (c.matchScore) >= 80 ? 'text-green-400' : ((c.matchScore) >= 50 ? 'text-yellow-400' : 'text-orange-600')]">
             {{ (c.matchScore || 0).toFixed(1) }}%
           </p>
        </div>

        <div class="mt-6 ml-2">
            <span class="text-[10px] font-mono text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded">COD: {{ c.id }}</span>
            <h3 class="text-xl font-bold text-white mt-2 leading-tight truncate pr-16">{{ c.name || 'Fase Desconocida' }}</h3>
            <p class="text-xs text-slate-400 font-mono italic mb-4">{{ c.formula }}</p>
            
            <div class="flex gap-4 text-[11px] font-mono text-slate-500 border-t border-slate-700/50 pt-4">
                <span>a: <b class="text-slate-300">{{ c.a?.toFixed(2) }}</b></span> 
                <span>b: <b class="text-slate-300">{{ c.b?.toFixed(2) }}</b></span> 
                <span>c: <b class="text-slate-300">{{ c.c?.toFixed(2) }}</b></span>
            </div>

            <div v-if="c.is_refined" class="mt-4 grid grid-cols-2 gap-2 p-3 bg-slate-950/50 rounded-xl border border-blue-500/20">
               <div class="flex flex-col">
                  <span class="text-[9px] text-slate-500 uppercase">Goodness of Fit</span>
                  <span class="text-xs font-bold text-green-400">{{ c.gof?.toFixed(2) }}</span>
               </div>
               <div class="flex flex-col">
                  <span class="text-[9px] text-slate-500 uppercase">Correlación</span>
                  <span class="text-xs font-bold text-blue-400">{{ c.details?.intensity_corr?.toFixed(3) }}</span>
               </div>
            </div>
        </div>
      </div>
    </div>

    <div v-if="isModalOpen" class="fixed inset-0 z-[210] flex items-center justify-center p-6 bg-slate-950/90 backdrop-blur-sm">
      <div class="bg-slate-900 border border-slate-700 w-full max-w-6xl max-h-[95vh] rounded-3xl shadow-2xl flex flex-col overflow-hidden">
        
        <div class="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-800/20">
          <div>
            <div class="flex items-center gap-3">
                <h2 class="text-3xl font-black text-white tracking-tighter">{{ selectedCandidate?.name }}</h2>
                <span v-if="selectedCandidate?.is_refined" class="text-[10px] bg-green-500/20 text-green-400 px-2 py-1 rounded-full font-bold border border-green-500/30 uppercase tracking-widest">Físicamente Validado</span>
            </div>
            <p class="text-sm text-slate-400 font-mono mt-1">{{ selectedCandidate?.formula }} | COD ID: {{ selectedCandidate?.id }}</p>
          </div>
          <button @click="isModalOpen = false" class="text-slate-500 hover:text-white transition p-2">
             <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
          </button>
        </div>

        <div class="p-8 overflow-y-auto">
          <div class="bg-slate-950 p-6 rounded-2xl border border-slate-800 shadow-inner relative">
            <div v-if="loading" class="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/60 z-10 rounded-2xl">
               <div class="w-10 h-10 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin mb-4"></div>
               <span class="text-blue-400 font-bold font-mono text-xs uppercase tracking-widest">Generando Perfil...</span>
            </div>
            
            <XrdChart 
              v-if="drxData && !loading" 
              :two-theta="drxData.twoTheta" 
              :intensity="drxData.intensity"
              :theoretical-data="theoreticalData"
            />
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-8 mt-8">
            <div class="bg-slate-800/30 p-5 rounded-2xl border border-slate-700/50">
               <h4 class="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4">Estructura Cristalina (Å / °)</h4>
               <div class="grid grid-cols-3 gap-4">
                  <div v-for="v, k in {a:selectedCandidate.a, b:selectedCandidate.b, c:selectedCandidate.c, α:selectedCandidate.alpha, β:selectedCandidate.beta, γ:selectedCandidate.gamma}" :key="k">
                     <p class="text-[10px] text-slate-500 uppercase">{{k}}</p>
                     <p class="text-lg font-mono text-white">{{ v ? Number(v).toFixed(3) : '90' }}</p>
                  </div>
               </div>
            </div>

            <div class="bg-slate-800/30 p-5 rounded-2xl border border-slate-700/50 col-span-2">
               <h4 class="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4">Métricas de Calidad del Ajuste</h4>
               <div v-if="selectedCandidate.is_refined" class="grid grid-cols-4 gap-6">
                  <div>
                     <p class="text-[9px] text-slate-500 uppercase">Goodness of Fit</p>
                     <p class="text-xl font-bold text-green-400">{{ selectedCandidate.gof?.toFixed(2) }}</p>
                  </div>
                  <div>
                     <p class="text-[9px] text-slate-500 uppercase">Intensidad Corr.</p>
                     <p class="text-xl font-bold text-blue-400">{{ selectedCandidate.details?.intensity_corr?.toFixed(3) }}</p>
                  </div>
                  <div>
                     <p class="text-[9px] text-slate-500 uppercase">Penalización Densidad</p>
                     <p class="text-xl font-bold text-orange-400">{{ selectedCandidate.details?.density_penalty?.toFixed(2) }}</p>
                  </div>
                  <div>
                     <p class="text-[9px] text-slate-500 uppercase">Error Residuo (Rwp)</p>
                     <p class="text-xl font-bold text-white">{{ selectedCandidate.r_wp?.toFixed(1) }}%</p>
                  </div>
               </div>
               <p v-else class="text-slate-600 italic text-sm py-4">Inicie el proceso de Rietveld para ver el análisis de calidad detallado.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>