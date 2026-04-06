<template>
  <div class="py-8 max-w-4xl mx-auto">
    <div class="mb-6 flex items-center justify-between">
      <h1 class="text-3xl font-bold text-gray-800">评估报告</h1>
      <el-button @click="router.push('/dashboard')" plain>返回仪表盘</el-button>
    </div>

    <div v-if="report" class="space-y-6">
      <!-- Score Overview -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="bg-white p-8 rounded-[2rem] shadow-xl flex flex-col justify-center text-center border border-gray-100 relative overflow-hidden">
          <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-400 to-primary"></div>
          <div class="grid grid-cols-2 gap-y-8 gap-x-4">
            <div class="col-span-2 border-b border-gray-50 pb-6 mb-2">
              <p class="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-1">综合平均得分</p>
              <p class="text-6xl font-black text-primary">{{ Number(report.total_score || 0).toFixed(1) }}</p>
            </div>
            <div>
              <p class="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-1">技术深度</p>
              <p class="text-3xl font-bold text-gray-800">{{ report.content_score }}</p>
            </div>
            <div>
              <p class="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-1">表达沟通</p>
              <p class="text-3xl font-bold text-gray-800">{{ report.expression_score }}</p>
            </div>
            <div>
              <p class="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-1">业务场景</p>
              <p class="text-3xl font-bold text-gray-800">{{ report.business_scenario_score }}</p>
            </div>
            <div>
              <p class="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-1">问题解决</p>
              <p class="text-3xl font-bold text-gray-800">{{ report.problem_solving_score }}</p>
            </div>
          </div>
        </div>

        <!-- Radar Chart -->
        <div class="bg-white p-6 rounded-[2rem] shadow-xl border border-gray-100 flex items-center justify-center">
          <RadarChart :stats="{
            technical_depth: report.content_score,
            communication: report.expression_score,
            business_scenario: report.business_scenario_score,
            problem_solving: report.problem_solving_score
          }" />
        </div>
      </div>

      <!-- Strengths and Weaknesses -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="bg-white p-6 rounded-xl shadow-sm border border-green-100">
          <h3 class="text-lg font-bold text-green-600 mb-4 flex items-center">
            <span class="mr-2">✨</span> 亮点与优势
          </h3>
          <ul class="list-disc pl-5 space-y-2 text-gray-700">
            <li v-for="(highlight, idx) in parsedReportData.highlights" :key="idx">{{ highlight }}</li>
          </ul>
        </div>
        <div class="bg-white p-6 rounded-xl shadow-sm border border-red-100">
          <h3 class="text-lg font-bold text-red-500 mb-4 flex items-center">
            <span class="mr-2">🎯</span> 不足与改进点
          </h3>
          <ul class="list-disc pl-5 space-y-2 text-gray-700">
            <li v-for="(weakness, idx) in parsedReportData.weaknesses" :key="idx">{{ weakness }}</li>
          </ul>
        </div>
      </div>

      <!-- Recommendations -->
      <div class="bg-white p-6 rounded-xl shadow-md">
        <h3 class="text-xl font-bold text-gray-800 mb-4">个性化提升建议</h3>
        <p class="text-gray-700 leading-relaxed bg-blue-50 p-4 rounded-lg border border-blue-100">
          {{ report.recommendations || report.improvement_suggestions || parsedReportData.recommendations || '暂无具体建议，请继续保持练习。' }}
        </p>
      </div>
    </div>
    
    <div v-else class="text-center text-gray-500 py-12">
      暂未查找到评估报告数据，或报告正在生成中...
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api'
import { ElMessage } from 'element-plus'
import RadarChart from '@/components/analytics/RadarChart.vue'

const route = useRoute()
const router = useRouter()
const report = ref(null)
const loading = ref(false)

onMounted(async () => {
  // 1. Try to read from history state (immediate navigation from interview room)
  if (history.state && history.state.evaluation) {
    report.value = history.state.evaluation
    return
  }

  // 2. Try to fetch by ID from URL params (from dashboard navigation or direct link)
  const evalId = route.params.id
  if (evalId) {
    loading.value = true
    try {
      const { data } = await api.get(`/interview/${evalId}/evaluation`)
      report.value = data
    } catch (err) {
      ElMessage.error('无法加载评估报告')
      router.push('/dashboard')
    } finally {
      loading.value = false
    }
  }
})

const parsedReportData = computed(() => {
  if (!report.value) return { highlights: [], weaknesses: [], recommendations: '' }
  
  // If it's a DB record with report_json
  if (report.value.report_json) {
    try {
      const data = typeof report.value.report_json === 'string' 
        ? JSON.parse(report.value.report_json) 
        : report.value.report_json
      return {
        highlights: data.highlights || data.strengths || [],
        weaknesses: data.weaknesses || [],
        recommendations: data.recommendations || data.improvement_suggestions || ''
      }
    } catch(e) {
      return { highlights: ['评估数据解析异常'], weaknesses: [], recommendations: '' }
    }
  }
  
  // If it's already the parsed evaluation_data (raw JSON from LLM)
  return {
    highlights: report.value.highlights || report.value.strengths || [],
    weaknesses: report.value.weaknesses || [],
    recommendations: report.value.recommendations || report.value.improvement_suggestions || ''
  }
})
</script>
