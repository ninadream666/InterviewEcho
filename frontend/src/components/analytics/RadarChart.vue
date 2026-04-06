<template>
  <div ref="chartRef" class="w-full h-full min-h-[350px] animate-in zoom-in duration-1000"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  stats: {
    type: Object,
    default: () => ({
      technical_depth: 0,
      business_scenario: 0,
      problem_solving: 0,
      communication: 0
    })
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

  const option = {
    color: ['#4F46E5'],
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderWidth: 0,
      shadowBlur: 10,
      shadowColor: 'rgba(0, 0, 0, 0.1)',
      textStyle: { color: '#1F2937' }
    },
    radar: {
      indicator: [
        { name: '技术深度', max: 100 },
        { name: '业务场景', max: 100 },
        { name: '问题解决', max: 100 },
        { name: '表达沟通', max: 100 },
        { name: '综合匹配', max: 100 }
      ],
      shape: 'polygon',
      splitNumber: 5,
      axisName: {
        color: '#6B7280',
        fontWeight: 'bold',
        fontSize: 12
      },
      splitArea: {
        areaStyle: {
          color: [
            'rgba(79, 70, 229, 0.02)',
            'rgba(79, 70, 229, 0.04)',
            'rgba(79, 70, 229, 0.06)',
            'rgba(79, 70, 229, 0.08)',
            'rgba(79, 70, 229, 0.1)'
          ]
        }
      },
      axisLine: {
        lineStyle: { color: 'rgba(79, 70, 229, 0.1)' }
      },
      splitLine: {
        lineStyle: { color: 'rgba(79, 70, 229, 0.2)' }
      }
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: [
              props.stats.technical_depth || 0,
              props.stats.business_scenario || 0,
              props.stats.problem_solving || 0,
              props.stats.communication || 0,
              ((props.stats.technical_depth + props.stats.business_scenario + props.stats.problem_solving + props.stats.communication) / 4) || 0
            ],
            name: '能力分布'
          }
        ],
        symbolSize: 8,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(79, 70, 229, 0.4)' },
            { offset: 1, color: 'rgba(99, 102, 241, 0.1)' }
          ])
        },
        lineStyle: {
          width: 3,
          color: '#4F46E5'
        },
        itemStyle: {
          color: '#4F46E5',
          borderColor: '#fff',
          borderWidth: 2
        }
      }
    ]
  }

  chartInstance.setOption(option)
}

watch(() => props.stats, () => {
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
