<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const file = ref<File | null>(null);
const kAlpha2Stripped = ref(false);
const selectedAnode = ref('Cu');
const isProcessing = ref(false);

const anodes = ['Cu', 'Mo', 'Co', 'Cr', 'Fe', 'W'];

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement;
  file.value = target.files?.[0] ?? null;
};

const startAnalysis = async () => {
  if (!file.value) return;
  isProcessing.value = true;
  
  const formData = new FormData();
  formData.append('file', file.value);
  formData.append('anode', selectedAnode.value);
  formData.append('isStripped', kAlpha2Stripped.value.toString());

  try {
    const response = await axios.post('http://localhost:7071/api/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    const drxData = response.data;
    
    router.push({
      path: '/analysis',
      state: { drxData: JSON.stringify(drxData) }
    });

  } catch (error) {
    console.error("Error en el flujo:", error);
    alert("Hubo un error procesando el archivo.");
  } finally {
    isProcessing.value = false;
  }
};
</script>

<template>
  <div class="p-8 max-w-3xl mx-auto h-full flex flex-col justify-center">
    <h1 class="text-4xl font-bold text-white mb-2 tracking-tight">Nuevo Experimento</h1>
    <p class="text-slate-400 mb-10">Sube tu archivo RAW/CSV y configura los parámetros del equipo.</p>

    <div class="bg-slate-800/50 p-8 rounded-2xl border border-slate-700 shadow-2xl">
      
      <div class="border-2 border-dashed border-slate-600 rounded-xl p-10 flex flex-col items-center justify-center bg-slate-900/50 hover:border-blue-500 transition-colors group">
        <input type="file" @change="handleFileUpload" accept=".csv,.txt" class="hidden" id="file-upload" />
        <label for="file-upload" class="cursor-pointer flex flex-col items-center w-full">
          <svg class="w-12 h-12 text-slate-500 group-hover:text-blue-400 mb-4 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
          <span class="text-lg font-bold text-slate-300 group-hover:text-white">{{ file ? file.name : 'Selecciona o arrastra tu archivo' }}</span>
        </label>
      </div>

      <div class="mt-8 grid grid-cols-2 gap-6 bg-slate-900/50 p-6 rounded-xl border border-slate-700/50">
        
        <div>
          <h3 class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Material del Ánodo</h3>
          <div class="flex flex-wrap gap-2">
            <button 
              v-for="anode in anodes" :key="anode"
              @click="selectedAnode = anode"
              :class="['px-4 py-2 rounded font-bold font-mono transition-all', 
                       selectedAnode === anode ? 'bg-blue-600 text-white shadow-[0_0_10px_rgba(37,99,235,0.5)]' : 'bg-slate-800 text-slate-400 hover:bg-slate-700']"
            >
              {{ anode }}
            </button>
          </div>
        </div>

        <div>
          <h3 class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Preprocesamiento</h3>
          <label class="flex items-center gap-3 cursor-pointer group mt-2">
            <div class="relative flex items-center justify-center">
              <input type="checkbox" v-model="kAlpha2Stripped" class="peer sr-only" />
              <div class="w-6 h-6 bg-slate-800 border-2 border-slate-600 rounded peer-checked:bg-blue-600 peer-checked:border-blue-600 transition"></div>
              <svg class="absolute w-4 h-4 text-white opacity-0 peer-checked:opacity-100 transition" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg>
            </div>
            <span class="text-slate-300 text-sm group-hover:text-white transition">El espectro ya tiene Stripping de <span class="font-mono text-blue-400 font-bold">K<sub>α2</sub></span></span>
          </label>
        </div>
      </div>

      <button 
        @click="startAnalysis" 
        :disabled="!file || isProcessing"
        class="mt-8 w-full bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 text-white font-bold py-4 rounded-xl transition shadow-lg disabled:shadow-none"
      >
        {{ isProcessing ? 'Iniciando Motor Matemático...' : 'Procesar Difractograma' }}
      </button>

    </div>
  </div>
</template>