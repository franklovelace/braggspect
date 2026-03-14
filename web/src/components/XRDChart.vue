<script setup lang="ts">
import { onMounted, ref, watch, onUnmounted } from 'vue';
import * as echarts from 'echarts';

const props = defineProps<{
  twoTheta: number[],
  intensity: number[],
  title?: string,
  theoreticalData?: {x: number[], y: number[]}
}>();

const chartRef = ref<HTMLElement | null>(null);
let chart: echarts.ECharts | null = null;

const getOptions = () => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'axis',
    backgroundColor: '#1e293b',
    borderColor: '#334155',
    textStyle: { color: '#f1f5f9' },
    axisPointer: { type: 'cross', label: { backgroundColor: '#475569' } }
  },
  grid: {
    top: 40,
    right: 30,
    bottom: 50,
    left: 70
  },
  xAxis: {
    name: '2θ (°)',
    nameLocation: 'middle',
    nameGap: 30,
    type: 'value',
    scale: true,
    splitLine: { show: false },
    axisLabel: { color: '#94a3b8' }
  },
  yAxis: {
    name: 'Intensidad (u.a.)',
    nameLocation: 'middle',
    nameGap: 50,
    type: 'value',
    splitLine: { lineStyle: { color: '#334155', type: 'dashed' } },
    axisLabel: { color: '#94a3b8' }
  },
  series: [
  {
    name: 'Experimental',
    type: 'line',
    data: props.twoTheta.map((val, i) => [val, props.intensity[i]]),
    lineStyle: { color: '#38bdf8', width: 1.5 }, 
    showSymbol: false,
    sampling: 'lttb'
  },
  ...(props.theoreticalData ? [{
    name: 'Teórico (COD)',
    type: 'line',
    data: props.theoreticalData?.x?.map((val, i) => [val, props.theoreticalData?.y?.[i]]) ?? [],
    lineStyle: { color: '#ef4444', width: 2, type: 'solid' }, 
    showSymbol: false
  }] : [])
]
});

const initChart = () => {
  if (!chartRef.value) return;
  chart = echarts.init(chartRef.value);
  chart.setOption(getOptions());
  
  window.addEventListener('resize', () => chart?.resize());
};

watch(() => props.intensity, () => {
  if (chart) {
    chart.setOption({
      series: [{
        data: props.twoTheta.map((val, i) => [val, props.intensity[i]])
      }]
    });
  }
}, { deep: true });

onMounted(initChart);

onUnmounted(() => {
  chart?.dispose();
  window.removeEventListener('resize', () => chart?.resize());
});
</script>

<template>
  <div class="relative w-full">
    <div v-if="title" class="absolute top-2 left-4 text-xs font-mono text-slate-500 uppercase tracking-widest z-10">
      {{ title }}
    </div>
    <div ref="chartRef" class="w-full h-[450px] bg-slate-900/40 rounded-xl border border-slate-800 shadow-inner"></div>
  </div>
</template>