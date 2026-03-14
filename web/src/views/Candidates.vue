<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import XrdChart from '../components/XrDChart.vue';

const candidates = ref<any[]>([]);
const experimentalData = ref<any>(null); 
const selectedCandidate = ref<any>(null);
const theoreticalData = ref<any>(null);
const loading = ref(false);

onMounted(() => {
  if (history.state.candidates) candidates.value = JSON.parse(history.state.candidates);
  if (history.state.drxData) experimentalData.value = JSON.parse(history.state.drxData);
});

const compare = async (c: any) => {
  selectedCandidate.value = c;
  loading.value = true;
  
  try {
    const params = {
      a: c.a, b: c.b, c: c.c, alpha: c.alpha, beta: c.beta, gamma: c.gamma,
      anode: experimentalData.value.anode,
      tmin: experimentalData.value.twoTheta[0],
      tmax: experimentalData.value.twoTheta[experimentalData.value.twoTheta.length - 1]
    };
    
    const res = await axios.get('http://localhost:8000/api/math/simulate', { params });
    theoreticalData.value = res.data;
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="p-8 h-full flex flex-col gap-6 overflow-y-auto">
    <div v-if="!selectedCandidate" class="grid grid-cols-2 gap-4">
        <div v-for="c in candidates" @click="compare(c)" class="...">...</div>
    </div>

    <div v-else class="flex flex-col gap-6">
      <button @click="selectedCandidate = null" class="self-start text-blue-400 font-bold underline">← Volver a la lista</button>
      
      <div class="grid grid-cols-2 gap-4">
        <div class="bg-slate-800 p-4 rounded-xl">
          <h3 class="text-xs font-bold text-slate-500 mb-2 uppercase">Experimental (Tu CSV)</h3>
          <XrdChart :twoTheta="experimentalData.twoTheta" :intensity="experimentalData.intensity" />
        </div>
        <div class="bg-slate-800 p-4 rounded-xl">
          <h3 class="text-xs font-bold mb-2 uppercase text-orange-400">Teórico (COD: {{ selectedCandidate.id }})</h3>
          <XrdChart :twoTheta="theoreticalData?.x || []" :intensity="theoreticalData?.y || []" />
        </div>
      </div>

      <div class="bg-slate-800 p-6 rounded-xl border-2 border-blue-500/30">
        <h3 class="text-lg font-bold mb-4">Superposición de Perfiles</h3>
        <p class="text-slate-400 italic">En el siguiente paso, haremos que XrdChart acepte múltiples series para ver el match perfecto.</p>
      </div>
    </div>
  </div>
</template>