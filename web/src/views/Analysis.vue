<script setup lang="ts">
import { ref, onMounted } from 'vue';
import XrdChart from '../components/XrDChart.vue';
import axios from 'axios';
import { useRouter } from 'vue-router';

const drxData = ref<any>(null);
const step = ref(1);
const loading = ref(false);
const loadingStep = ref("");
const router = useRouter();

onMounted(() => {
  const stateData = history.state.drxData;
  if (stateData) {
    drxData.value = JSON.parse(stateData);
  }
});

const analyzePeaks = () => {
  step.value = 2; 
};

const searchInCOD = async () => {
  if (!drxData.value) return;

  loading.value = true;
  loadingStep.value = "Ejecutando Pipeline Adaptativo (C# + Python)...";

  const dValuesList = drxData.value.topPeaks.map((p: any) => {
    return Number(p.d_spacing || p.dSpacing || p.DSpacing || 0);
  }).filter((v: number) => v > 0); 

  const payload = {
    dValues: dValuesList,
    x: Array.from(drxData.value.twoTheta || []), 
    y: Array.from(drxData.value.intensity || []),
    anode: String(drxData.value.anode || 'Cu')
  };

  try {
    const response = await axios.post('http://localhost:7071/api/search/hanawalt', payload);
    
    localStorage.setItem('current_drx_data', JSON.stringify(drxData.value));

    router.push({
      path: '/candidates',
      state: { 
        candidates: JSON.stringify(response.data) 
      }
    });
  } catch (error) {
    console.error("Error en el pipeline:", error);
    alert("El servidor rechazó los datos o Python no responde.");
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="p-8 h-full flex flex-col gap-6 overflow-y-auto">
    
    <div class="flex justify-between items-center border-b border-slate-700 pb-4">
      <div>
        <h1 class="text-3xl font-bold text-white">Análisis de Difractograma</h1>
        <p class="text-slate-400">Archivo: <span class="text-blue-400 font-mono">{{ drxData?.sampleName || 'Desconocido' }}</span> | Ánodo: {{ drxData?.anode || 'Cu' }}</p>
      </div>
      <router-link to="/" class="bg-slate-800 px-4 py-2 rounded text-slate-300 hover:text-white hover:bg-slate-700 transition">
        Cargar otro archivo
      </router-link>
    </div>

    <div v-if="drxData" class="bg-slate-800 p-6 rounded-xl shadow-xl border border-slate-700">
      <h2 class="text-lg font-bold mb-4 flex items-center gap-2 text-white">
        <span class="w-3 h-3 bg-blue-500 rounded-full"></span> Patrón Experimental
      </h2>
      <XrdChart :twoTheta="drxData.twoTheta" :intensity="drxData.intensity" />
    </div>

    <div v-else class="flex-1 flex items-center justify-center text-slate-500">
      <p>No hay datos cargados. Vuelve al inicio.</p>
    </div>

    <div v-if="drxData && step === 1" class="flex justify-center my-4">
      <button @click="analyzePeaks" class="bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-8 rounded-full shadow-[0_0_15px_rgba(37,99,235,0.4)] transition transform hover:scale-105">
        Extraer Picos (Método Hanawalt)
      </button>
    </div>

    <div v-if="step >= 2 && drxData?.topPeaks?.length" class="bg-slate-800 p-6 rounded-xl border border-slate-700 animate-fade-in">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-lg font-bold text-white flex items-center gap-2">
          <span class="w-3 h-3 bg-orange-500 rounded-full"></span> Picos Principales (Ley de Bragg)
        </h2>
        
        <button v-if="step === 2" @click="searchInCOD" class="bg-orange-600 hover:bg-orange-500 text-white font-bold py-2 px-6 rounded-lg transition shadow-lg">
          Buscar Fase en COD
        </button>
      </div>

      <div class="grid grid-cols-3 gap-6">
        <div v-for="(peak, index) in drxData.topPeaks" :key="index" class="bg-slate-900/50 p-4 rounded-lg border border-slate-600/50 relative overflow-hidden">
          <div class="absolute top-0 left-0 w-full h-1 bg-orange-500 opacity-50"></div>
          <span class="text-xs text-slate-500 font-bold uppercase tracking-widest block mb-4">Pico {{ Number(index) + 1 }}</span>
          
          <div class="flex justify-between items-end border-b border-slate-700/50 pb-2 mb-2">
            <span class="text-sm text-slate-400">Ángulo 2θ</span>
            <span class="text-lg text-white font-mono">{{ peak.two_theta.toFixed(2) }}°</span>
          </div>
          <div class="flex justify-between items-end border-b border-slate-700/50 pb-2 mb-2">
            <span class="text-sm text-slate-400">Distancia (d)</span>
            <span class="text-2xl text-orange-400 font-mono font-bold">{{ peak.d_spacing.toFixed(4) }} <span class="text-sm">Å</span></span>
          </div>
          <div class="flex justify-between items-end">
            <span class="text-sm text-slate-400">Intensidad</span>
            <span class="text-sm text-slate-300 font-mono">{{ peak.intensity.toFixed(0) }} u.a.</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="step === 3" class="bg-slate-800 p-6 rounded-xl border border-green-700/50 animate-fade-in mb-10">
      <h2 class="text-lg font-bold text-white flex items-center gap-2 mb-4">
        <span class="w-3 h-3 bg-green-500 rounded-full"></span> Candidatos Encontrados
      </h2>
      <p class="text-slate-400 italic">Aquí conectaremos el Query de C# para buscar estructuras con d1 ≈ {{ drxData.topPeaks[0].d_spacing.toFixed(2) }} Å y d2 ≈ {{ drxData.topPeaks[1].d_spacing.toFixed(2) }} Å...</p>
    </div>

  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.5s ease-out forwards;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>