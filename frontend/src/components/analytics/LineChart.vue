<template>
  <div ref="chartRef" class="w-full h-80 animate-in fade-in slide-in-from-bottom duration-1000"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  history: {
    type: Array,
    default: () => []
  }
})

const chartRef = ref(null)
let chartInstance = null

const initChart = () => {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

const updateChart = () => {
  if (!chartInstance) return

  // Sort history by created_at date
  const sortedHistory = [...props.history].sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
  
  const dates = sortedHistory.map(item => new Date(item.created_at).toLocaleDateString())
  const scores = sortedHistory.map(item => item.total_score)

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderWidth: 0,
      shadowBlur: 15,
      shadowColor: 'rgba(79, 70, 229, 0.1)',
      textStyle: { color: '#4B5563', fontSize: 12 },
      formatter: (params) => {
        const item = params[0]
        return `<div class="p-2">
          <div class="text-[10px] text-gray-400 font-bold uppercase mb-1">${item.axisValue}</div>
          <div class="text-lg font-black text-primary">${item.data} <small class="text-[10px] font-normal opacity-60">分</small></div>
        </div>`
      }
    },
    grid: {
      left: '2%',
      right: '6%',
      bottom: '10%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: true,
      data: dates,
      axisLine: { lineStyle: { color: '#F3F4F6' } },
      axisTick: { show: false },
      axisLabel: { color: '#9CA3AF', fontSize: 10, margin: 15 }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      splitLine: { lineStyle: { color: '#F9FAFB', type: 'dashed' } },
      axisLine: { show: false },
      axisLabel: { color: '#D1D5DB', fontSize: 10 }
    },
    series: [
      {
        name: '评估得分',
        type: 'line',
        data: scores,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        itemStyle: {
          color: '#4F46E5',
          borderColor: '#fff',
          borderWidth: 2,
          shadowBlur: 10,
          shadowColor: 'rgba(79, 70, 229, 0.3)'
        },
        lineStyle: {
          width: 4,
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#6366F1' },
            { offset: 1, color: '#4F46E5' }
          ])
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(79, 70, 229, 0.15)' },
            { offset: 1, color: 'rgba(79, 70, 229, 0)' }
          ])
        }
      }
    ]
  }

  chartInstance.setOption(option)
}

watch(() => props.history, () => {
  updateChart()
}, { deep: true })

onMounted(() => {
  initChart()
  window.addEventListener('resize', () => chartInstance?.resize())
})

onUnmounted(() => {
  chartInstance?.dispose()
})
</script>
