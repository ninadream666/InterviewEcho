<template>
  <!-- 图表挂载容器，需设置基础高度 -->
  <div ref="chartRef" class="w-full h-full min-h-[300px]"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
// 引入 ECharts 核心模块
import * as echarts from 'echarts'

// 定义组件接收的属性 (Props)
const props = defineProps({
  // 雷达图的数据值数组
  data: {
    type: Array,
    default: () => [
      {
        value: [85, 90, 75, 88, 80],
        name: '能力评估'
      }
    ]
  },
  // 雷达图的指示器维度（例如：技术正确性、沟通表达等）
  indicators: {
    type: Array,
    default: () => [
      { name: '技术正确性', max: 100 },
      { name: '知识深度', max: 100 },
      { name: '逻辑严谨性', max: 100 },
      { name: '岗位匹配度', max: 100 },
      { name: '沟通表达', max: 100 }
    ]
  }
})

const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

// 初始化图表
const initChart = () => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
    updateChart()
  }
}

// 更新图表配置
const updateChart = () => {
  if (!chartInstance) return
  
  const option = {
    // 采用平台的主题蓝
    color: ['#0066CC'],
    tooltip: {
      trigger: 'item'
    },
    radar: {
      indicator: props.indicators,
      shape: 'polygon',
      splitNumber: 5,
      axisName: {
        color: '#4B5563', // text-gray-600
        fontWeight: 'bold',
        fontSize: 12
      },
      splitArea: {
        areaStyle: {
          // 渐变背景色，增加高级感
          color: [
            'rgba(0, 102, 204, 0.02)',
            'rgba(0, 102, 204, 0.05)',
            'rgba(0, 102, 204, 0.08)',
            'rgba(0, 102, 204, 0.12)',
            'rgba(0, 102, 204, 0.18)'
          ]
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(0, 102, 204, 0.2)'
        }
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(0, 102, 204, 0.3)'
        }
      }
    },
    series: [
      {
        name: '能力评估雷达图',
        type: 'radar',
        data: props.data,
        symbolSize: 6,
        areaStyle: {
          color: 'rgba(0, 102, 204, 0.3)'
        },
        lineStyle: {
          width: 2,
          color: '#0066CC'
        },
        itemStyle: {
          color: '#0066CC',
          borderColor: '#fff',
          borderWidth: 2
        }
      }
    ]
  }
  
  chartInstance.setOption(option)
}

// 监听数据变化，实现图表的动态重绘
watch(() => props.data, () => {
  updateChart()
}, { deep: true })

watch(() => props.indicators, () => {
  updateChart()
}, { deep: true })

// 处理窗口缩放事件，使图表响应式调整大小
const handleResize = () => {
  chartInstance?.resize()
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<style scoped>
/* 确保父容器可以正确的约束 ECharts 实例大小 */
</style>