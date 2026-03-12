<script setup lang="ts">
import { ref } from 'vue';

const file = ref<File | null>(null);
const kAlpha2Stripped = ref(false); 
const isProcessing = ref(false);

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) file.value = target.files[0];
};

const startAnalysis = async () => {
  if (!file.value) return;
  isProcessing.value = true;
  
  
  setTimeout(() => {
    isProcessing.value = false;
    alert(`Flujo iniciado. Archivo: ${file.value?.name}. Stripped K-a2: ${kAlpha2Stripped.value}`);
  }, 1000);
};
</script>

<template>
  <div class="p-8 max-w-3xl mx-auto h-full flex flex-col justify-center">
    <h1 class="text-4xl font-bold text-white mb-2 tracking-tight">Nuevo Experimento</h1>
    <p class="text-slate-400 mb-10">Sube tu archivo RAW/CSV y configura los parámetros del difractómetro.</p>

    <div class="bg-slate-800/50 p-8 rounded-2xl border border-slate-700 shadow-2xl">
      
      <div class="border-2 border-dashed border-slate-600 rounded-xl p-10 flex flex-col items-center justify-center bg-slate-900/50 hover:border-blue-500 transition-colors group">
        <input type="file" @change="handleFileUpload" accept=".csv,.txt" class="hidden" id="file-upload" />
        <label for="file-upload" class="cursor-pointer flex flex-col items-center">
          <svg class="w-12 h-12 text-slate-500 group-hover:text-blue-400 mb-4 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
          <span class="text-lg font-bold text-slate-300 group-hover:text-white">{{ file ? file.name : 'Selecciona o arrastra tu archivo' }}</span>
          <span class="text-sm text-slate-500 mt-1">Soporta .CSV, .TXT (Formato 2Theta, Intensidad)</span>
        </label>
      </div>

      <div class="mt-8 bg-slate-900/50 p-6 rounded-xl border border-slate-700/50">
        <h3 class="text-sm font-bold text-slate-300 uppercase tracking-widest mb-4">Preprocesamiento</h3>
        
        <label class="flex items-center gap-3 cursor-pointer group">
          <div class="relative flex items-center justify-center">
            <input type="checkbox" v-model="kAlpha2Stripped" class="peer sr-only" />
            <div class="w-6 h-6 bg-slate-800 border-2 border-slate-600 rounded peer-checked:bg-blue-600 peer-checked:border-blue-600 transition"></div>
            <svg class="absolute w-4 h-4 text-white opacity-0 peer-checked:opacity-100 transition" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg>
          </div>
          <span class="text-slate-300 group-hover:text-white transition">El espectro ya tiene Stripping de <span class="font-mono text-blue-400 font-bold">K<sub>α2</sub></span></span>
        </label>
        <p class="text-xs text-slate-500 mt-2 ml-9">Si no está marcado, el motor matemático modelará un perfil Pseudo-Voigt para sustraer la contribución del doblete del Ánodo.</p>
      </div>

      <button 
        @click="startAnalysis" 
        :disabled="!file || isProcessing"
        class="mt-8 w-full bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-bold py-4 rounded-xl transition shadow-lg disabled:shadow-none"
      >
        {{ isProcessing ? 'Iniciando Motor...' : 'Procesar Difractograma' }}
      </button>

    </div>
  </div>
</template>