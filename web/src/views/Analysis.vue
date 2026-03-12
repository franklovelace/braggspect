<script setup lang="ts">
import { ref, onMounted } from 'vue';
import XrdChart from '../components/XrDChart.vue';

const drxData = ref<any>(null);

onMounted(() => {
  const stateData = history.state.drxData;
  if (stateData) {
    drxData.value = JSON.parse(stateData);
  }
});
</script>

<template>
  <div class="p-8 h-full flex flex-col gap-6 overflow-y-auto">
    <div class="flex justify-between items-center border-b border-slate-700 pb-4">
      <div>
        <h1 class="text-3xl font-bold text-white">Análisis de Difractograma</h1>
        <p class="text-slate-400">Archivo: {{ drxData?.sampleName || 'Desconocido' }} | Ánodo: {{ drxData?.anode || 'Cu' }}</p>
      </div>
      <router-link to="/" class="bg-slate-800 px-4 py-2 rounded text-slate-300 hover:text-white hover:bg-slate-700 transition">
        Cargar otro archivo
      </router-link>
    </div>

    <div v-if="drxData" class="bg-slate-800 p-6 rounded-xl shadow-xl border border-slate-700">
      <h2 class="text-lg font-bold mb-4 flex items-center gap-2 text-white">
        <span class="w-3 h-3 bg-blue-500 rounded-full"></span>
        Patrón de Difracción
      </h2>
      
      <XrdChart 
        :twoTheta="drxData.twoTheta" 
        :intensity="drxData.intensity" 
      />
    </div>

    <div v-else class="flex-1 flex items-center justify-center text-slate-500">
      <p>No hay datos cargados. Vuelve al inicio y sube un archivo.</p>
    </div>

  </div>
</template>