<template>
  <div class="w-full max-w-7xl mx-auto p-6 space-y-6 bg-transparent" data-purpose="dashboard-content-area">
    
    <!-- BEGIN: StatsGrid -->
    <section class="grid grid-cols-1 md:grid-cols-3 gap-6" data-purpose="top-stats-row">
      <!-- Total Interviews Card -->
      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex items-center justify-between" data-purpose="stat-card">
        <div>
          <p class="text-sm font-medium text-slate-500 uppercase tracking-wider">总面试次数</p>
          <h3 class="text-3xl font-bold text-slate-900 mt-1">{{ stats.totalInterviews }}</h3>
        </div>
        <div class="p-3 bg-blue-50 rounded-lg">
          <svg class="h-8 w-8 text-[#0066CC]" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
          </svg>
        </div>
      </div>
      
      <!-- Average Score Card -->
      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex items-center justify-between" data-purpose="stat-card">
        <div>
          <p class="text-sm font-medium text-slate-500 uppercase tracking-wider">平均综合得分</p>
          <h3 class="text-3xl font-bold text-slate-900 mt-1">{{ stats.averageScore }}</h3>
        </div>
        <div class="p-3 bg-blue-50 rounded-lg">
          <svg class="h-8 w-8 text-[#0066CC]" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
          </svg>
        </div>
      </div>
      
      <!-- Top Competency Card -->
      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex items-center justify-between" data-purpose="stat-card">
        <div>
          <p class="text-sm font-medium text-slate-500 uppercase tracking-wider">最强能力维度</p>
          <h3 class="text-xl font-bold text-slate-900 mt-1">{{ stats.topCompetency }}</h3>
        </div>
        <div class="p-3 bg-blue-50 rounded-lg">
          <svg class="h-8 w-8 text-[#0066CC]" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
          </svg>
        </div>
      </div>
    </section>
    <!-- END: StatsGrid -->

    <!-- BEGIN: ChartSection -->
    <section class="bg-white p-6 rounded-xl shadow-sm border border-slate-100" data-purpose="middle-chart-section">
      <div class="mb-4">
        <h2 class="text-lg font-bold text-slate-800">近期能力成长曲线</h2>
      </div>
      <!-- ECharts 渲染容器 -->
      <div ref="lineChartRef" class="h-80 w-full rounded-lg bg-slate-50" data-purpose="chart-container"></div>
    </section>
    <!-- END: ChartSection -->

    <!-- BEGIN: HistorySection -->
    <section class="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden" data-purpose="bottom-history-section">
      <div class="px-6 py-4 border-b border-slate-100">
        <h2 class="text-lg font-bold text-slate-800">面试历史记录</h2>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse" id="interview-history-table">
          <thead>
            <tr class="bg-slate-50">
              <th class="px-6 py-3 text-xs font-semibold text-slate-500 uppercase">日期</th>
              <th class="px-6 py-3 text-xs font-semibold text-slate-500 uppercase">目标岗位</th>
              <th class="px-6 py-3 text-xs font-semibold text-slate-500 uppercase">难度</th>
              <th class="px-6 py-3 text-xs font-semibold text-slate-500 uppercase">最终得分</th>
              <th class="px-6 py-3 text-xs font-semibold text-slate-500 uppercase text-right">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <!-- 使用 v-for 渲染历史记录列表 -->
            <tr v-for="item in historyList" :key="item.id" class="hover:bg-slate-50 transition-colors">
              <td class="px-6 py-4 text-sm text-slate-600">{{ item.date }}</td>
              <td class="px-6 py-4 text-sm font-medium text-slate-900">{{ item.position }}</td>
              <td class="px-6 py-4">
                <span :class="['px-2.5 py-0.5 rounded-full text-xs font-medium border', item.difficultyClass]">
                  {{ item.difficulty }}
                </span>
              </td>
              <td class="px-6 py-4 text-sm font-bold text-slate-900">{{ item.score }}</td>
              <td class="px-6 py-4 text-right">
                <button 
                  @click="goToReport(item.id)"
                  class="text-[#0066CC] text-sm font-semibold hover:underline decoration-2 underline-offset-4 cursor-pointer"
                >
                  查看评估报告
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
    <!-- END: HistorySection -->
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'

const router = useRouter()
const lineChartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

// 模拟顶部概览数据
const stats = ref({
  totalInterviews: 24,
  averageScore: 85,
  topCompetency: '系统设计与架构'
})

// 模拟面试历史数据
const historyList = ref([
  {
    id: 1,
    date: '2026-05-20',
    position: 'Java后端开发工程师',
    difficulty: '中级',
    difficultyClass: 'bg-amber-50 text-amber-700 border-amber-100',
    score: 88
  },
  {
    id: 2,
    date: '2026-05-15',
    position: 'Web前端开发工程师',
    difficulty: '高级',
    difficultyClass: 'bg-red-50 text-red-700 border-red-100',
    score: 79
  },
  {
    id: 3,
    date: '2026-05-10',
    position: 'Python算法工程师',
    difficulty: '初级',
    difficultyClass: 'bg-green-50 text-green-700 border-green-100',
    score: 92
  }
])

// 跳转到对应的评估报告页
const goToReport = (id: number) => {
  router.push(`/report/${id}`)
}

// 初始化折线图
const initChart = () => {
  if (lineChartRef.value) {
    chartInstance = echarts.init(lineChartRef.value)
    chartInstance.setOption({
      tooltip: {
        trigger: 'axis'
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: ['5月2日', '5月6日', '5月10日', '5月15日', '5月20日'],
        axisLine: { lineStyle: { color: '#E5E7EB' } },
        axisLabel: { color: '#6B7280' }
      },
      yAxis: {
        type: 'value',
        min: 60,
        max: 100,
        splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } },
        axisLabel: { color: '#6B7280' }
      },
      series: [
        {
          name: '综合得分',
          type: 'line',
          data: [72, 78, 92, 79, 88],
          smooth: true,
          symbolSize: 8,
          itemStyle: {
            color: '#0066CC',
            borderColor: '#fff',
            borderWidth: 2
          },
          lineStyle: {
            width: 3,
            color: '#0066CC'
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(0, 102, 204, 0.2)' },
              { offset: 1, color: 'rgba(0, 102, 204, 0)' }
            ])
          }
        }
      ]
    })
  }
}

// 处理窗口大小改变
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
/* 确保图表容器高度正常 */
</style>