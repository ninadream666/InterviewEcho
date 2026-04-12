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
  },
  filterRole: {
    type: String,
    default: 'All'
  },
  filterDifficulty: {
    type: String,
    default: 'All'
  }
})

const chartRef = ref(null)
let chartInstance = null

const NESTED_COLORS = {
  'Java后端开发工程师': { '简单': '#A5B4FC', '中等': '#6366F1', '困难': '#4338CA' },
  'Web前端开发工程师': { '简单': '#6EE7B7', '中等': '#10B981', '困难': '#047857' },
  'Python算法工程师': { '简单': '#FDE68A', '中等': '#F59E0B', '困难': '#B45309' }
}

const DEFAULT_COLOR = '#9CA3AF'

const initChart = () => {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

const updateChart = () => {
  if (!chartInstance) return

  // Sort history by date
  const sortedHistory = [...props.history].sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
  
  // Format X-axis: All unique timestamps
  const uniqueDates = Array.from(new Set(sortedHistory.map(item => {
    const d = new Date(item.created_at)
    return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  })))

  let series = []
  
  // Determine Grouping Mode
  if (props.filterRole === 'All' && props.filterDifficulty === 'All') {
    // Mode 1: 9 Lines (Role x Difficulty)
    const roles = ['Java后端开发工程师', 'Web前端开发工程师', 'Python算法工程师']
    const difficulties = ['简单', '中等', '困难']
    
    roles.forEach(role => {
      difficulties.forEach(diff => {
        const roleDiffData = sortedHistory.filter(item => item.role === role && item.difficulty === diff)
        if (roleDiffData.length > 0) {
          series.push({
            name: `${role}-${diff}`,
            type: 'line',
            data: uniqueDates.map(dateStr => {
              const matching = roleDiffData.find(item => {
                const d = new Date(item.created_at)
                return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}` === dateStr
              })
              return matching ? { value: matching.total_score, difficulty: matching.difficulty } : null
            }),
            smooth: true,
            connectNulls: true,
            itemStyle: { color: NESTED_COLORS[role]?.[diff] || DEFAULT_COLOR }
          })
        }
      })
    })
  } else if (props.filterRole !== 'All' && props.filterDifficulty === 'All') {
    // Mode 2: Specific Role -> Show 3 Difficulties
    const difficulties = ['简单', '中等', '困难']
    const roleData = sortedHistory.filter(item => item.role === props.filterRole)
    series = difficulties.map(diff => ({
      name: diff,
      type: 'line',
      data: uniqueDates.map(dateStr => {
        const matching = roleData.find(item => {
          const d = new Date(item.created_at)
          return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}` === dateStr && item.difficulty === diff
        })
        return matching ? { value: matching.total_score, difficulty: matching.difficulty } : null
      }),
      smooth: true,
      connectNulls: true,
      itemStyle: { color: NESTED_COLORS[props.filterRole]?.[diff] || DEFAULT_COLOR }
    }))
  } else if (props.filterDifficulty !== 'All' && props.filterRole === 'All') {
    // Mode 3: Specific Difficulty -> Show 3 Roles
    const roles = ['Java后端开发工程师', 'Web前端开发工程师', 'Python算法工程师']
    const diffData = sortedHistory.filter(item => item.difficulty === props.filterDifficulty)
    series = roles.map(role => ({
      name: role,
      type: 'line',
      data: uniqueDates.map(dateStr => {
        const matching = diffData.find(item => {
          const d = new Date(item.created_at)
          return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}` === dateStr && item.role === role
        })
        return matching ? { value: matching.total_score, difficulty: matching.difficulty } : null
      }),
      smooth: true,
      connectNulls: true,
      itemStyle: { color: NESTED_COLORS[role]?.[props.filterDifficulty] || DEFAULT_COLOR }
    }))
  } else {
    // Mode 4: Specific Role AND Specific Difficulty -> Single Line
    const filteredData = sortedHistory.filter(item => item.role === props.filterRole && item.difficulty === props.filterDifficulty)
    const baseColor = NESTED_COLORS[props.filterRole]?.[props.filterDifficulty] || DEFAULT_COLOR
    series = [{
      name: `${props.filterRole} (${props.filterDifficulty})`,
      type: 'line',
      data: uniqueDates.map(dateStr => {
        const matching = filteredData.find(item => {
          const d = new Date(item.created_at)
          return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}` === dateStr
        })
        return matching ? { value: matching.total_score, difficulty: matching.difficulty } : null
      }),
      smooth: true,
      connectNulls: true,
      itemStyle: { color: baseColor },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: baseColor + '33' },
          { offset: 1, color: 'transparent' }
        ])
      }
    }]
  }

  const option = {
    legend: {
      show: true,
      top: 0,
      icon: 'circle',
      textStyle: { color: '#9CA3AF', fontSize: 10 }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderWidth: 0,
      shadowBlur: 15,
      shadowColor: 'rgba(0, 0, 0, 0.05)',
      textStyle: { color: '#4B5563', fontSize: 12 },
      formatter: (params) => {
        let html = `<div class="p-2">
          <div class="text-[10px] text-gray-400 font-bold uppercase mb-2">${params[0].axisValue}</div>`
        params.forEach(p => {
          if (p.data !== null) {
            const diffTag = p.data.difficulty ? ` (${p.data.difficulty})` : ''
            const score = typeof p.data === 'object' ? p.data.value : p.data
            html += `<div class="flex items-center justify-between gap-4 mb-1">
              <span class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full" style="background-color: ${p.color}"></span>
                <span class="text-xs font-medium">${p.seriesName}${diffTag}</span>
              </span>
              <span class="text-sm font-black text-gray-800">${score}</span>
            </div>`
          }
        })
        html += `</div>`
        return html
      }
    },
    grid: {
      left: '2%',
      right: '6%',
      bottom: '5%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: true,
      data: uniqueDates,
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
    series: series.map(s => ({
      ...s,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { width: 3 }
    }))
  }

  chartInstance.setOption(option, true)
}

watch(() => [props.history, props.filterRole, props.filterDifficulty], () => {
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
