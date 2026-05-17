<template>
  <div class="max-w-7xl mx-auto px-4 py-4 sm:py-8 space-y-6">
    <section class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-5">
      <div>
        <p class="text-sm font-semibold text-[#0066CC] uppercase tracking-wider mb-2">Hot100 ACM</p>
        <h1 class="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">题库练习</h1>
        <p class="text-slate-500 mt-3 max-w-2xl leading-relaxed">
          使用完整程序读取 stdin、输出 stdout，贴近笔试与现场编码的练习方式。
        </p>
      </div>
      <button
        class="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-[#0066CC] text-[#0066CC] text-sm font-semibold hover:bg-[#E6F0FA] transition-colors"
        type="button"
        @click="refreshAll"
      >
        <el-icon><Refresh /></el-icon>
        刷新题库
      </button>
    </section>

    <section class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="bg-white p-4 sm:p-6 rounded-xl shadow-sm border border-slate-100 flex items-center justify-between">
        <div>
          <p class="text-sm font-medium text-slate-500 uppercase tracking-wider">题目总数</p>
          <h3 class="text-3xl font-bold text-slate-900 mt-1">{{ totalCount }}</h3>
        </div>
        <div class="p-3 bg-blue-50 rounded-lg text-[#0066CC]">
          <el-icon class="text-3xl"><Document /></el-icon>
        </div>
      </div>
      <div class="bg-white p-4 sm:p-6 rounded-xl shadow-sm border border-slate-100 flex items-center justify-between">
        <div>
          <p class="text-sm font-medium text-slate-500 uppercase tracking-wider">已开放判题</p>
          <h3 class="text-3xl font-bold text-slate-900 mt-1">{{ judgableCount }}</h3>
        </div>
        <div class="p-3 bg-blue-50 rounded-lg text-[#0066CC]">
          <el-icon class="text-3xl"><Cpu /></el-icon>
        </div>
      </div>
      <div class="bg-white p-4 sm:p-6 rounded-xl shadow-sm border border-slate-100 flex items-center justify-between">
        <div>
          <p class="text-sm font-medium text-slate-500 uppercase tracking-wider">当前通过</p>
          <h3 class="text-3xl font-bold text-slate-900 mt-1">{{ solvedCount }}</h3>
        </div>
        <div class="p-3 bg-blue-50 rounded-lg text-[#0066CC]">
          <el-icon class="text-3xl"><CircleCheck /></el-icon>
        </div>
      </div>
    </section>

    <section class="bg-white rounded-xl shadow-sm border border-slate-100 p-4 sm:p-5">
      <div class="grid grid-cols-1 md:grid-cols-[1fr_180px_220px] gap-3">
        <el-input v-model="keyword" clearable placeholder="搜索题名或 slug" size="large" @keyup.enter="fetchProblems">
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="difficulty" size="large" aria-label="筛选难度">
          <el-option v-for="item in difficultyOptions" :key="item" :label="item === '全部' ? '全部难度' : item" :value="item" />
        </el-select>
        <el-select v-model="tag" size="large" filterable aria-label="筛选主题">
          <el-option label="全部主题" value="全部" />
          <el-option v-for="item in tags" :key="item" :label="item" :value="item" />
        </el-select>
      </div>
    </section>

    <div class="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_360px] gap-6">
      <section class="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
        <div class="px-4 sm:px-6 py-3 sm:py-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 class="text-lg font-bold text-slate-800 flex items-center">
              <span class="w-1.5 h-5 bg-[#0066CC] rounded-full mr-2"></span>
              题目列表
            </h2>
            <p class="text-sm text-slate-500 mt-1">前 20 题已配置完整样例与隐藏测试。</p>
          </div>
          <span class="text-sm text-slate-400">{{ totalCount }} 题</span>
        </div>

        <div v-if="loading" class="py-12 sm:py-20 flex items-center justify-center text-slate-400">
          <el-icon class="is-loading text-2xl mr-2 text-[#0066CC]"><Loading /></el-icon>
          正在整理题库
        </div>

        <div v-else-if="visibleProblems.length" class="divide-y divide-slate-100">
          <button
            v-for="problem in visibleProblems"
            :key="problem.id"
            type="button"
            class="w-full px-4 sm:px-6 py-3 sm:py-4 text-left hover:bg-slate-50 transition-colors grid grid-cols-[48px_minmax(0,1fr)_auto] md:grid-cols-[56px_minmax(0,1fr)_120px_96px_24px] gap-3 items-center"
            @click="goProblem(problem.id)"
          >
            <span class="text-sm font-bold text-slate-400 tabular-nums">{{ String(problem.id).padStart(2, '0') }}</span>
            <span class="min-w-0">
              <strong class="block text-slate-900 font-semibold truncate">{{ problem.title }}</strong>
              <span class="mt-2 flex flex-wrap gap-1.5">
                <em
                  v-for="tagItem in problem.tags.slice(0, 4)"
                  :key="`${problem.id}-${tagItem}`"
                  class="not-italic px-2 py-0.5 rounded bg-slate-50 border border-slate-100 text-xs text-slate-500"
                >
                  {{ tagItem }}
                </em>
              </span>
            </span>
            <span :class="['hidden md:inline-flex justify-center px-2.5 py-1 rounded-full text-xs font-semibold border', difficultyClass(problem.difficulty)]">
              {{ problem.difficulty }}
            </span>
            <span :class="['hidden md:inline-flex justify-center px-2.5 py-1 rounded-full text-xs font-semibold border', statusClass(problem)]">
              {{ problem.solved ? '已通过' : problem.judgable ? '可练习' : '占位' }}
            </span>
            <el-icon class="text-slate-300 hidden md:block"><ArrowRight /></el-icon>
          </button>
        </div>

        <div v-else class="py-12 sm:py-20 text-center text-slate-400">没有匹配的题目</div>

        <div v-if="!loading && problemTotalPages > 1" class="px-4 sm:px-6 py-3 sm:py-4 border-t border-slate-100 flex items-center justify-between">
          <span class="text-sm text-slate-400">第 {{ problemPage }} / {{ problemTotalPages }} 页</span>
          <el-pagination v-model:current-page="problemPage" background layout="prev, pager, next" :page-size="pageSize" :total="problems.length" />
        </div>
      </section>

      <aside class="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden h-fit">
        <div class="px-4 sm:px-6 py-3 sm:py-4 border-b border-slate-100">
          <h2 class="text-lg font-bold text-slate-800 flex items-center">
            <span class="w-1.5 h-5 bg-[#0066CC] rounded-full mr-2"></span>
            最近提交
          </h2>
          <p class="text-sm text-slate-500 mt-1">只记录正式提交，样例运行不会进入历史。</p>
        </div>

        <div v-if="historyLoading" class="py-12 sm:py-16 flex items-center justify-center text-slate-400">
          <el-icon class="is-loading text-2xl mr-2 text-[#0066CC]"><Loading /></el-icon>
          正在读取历史
        </div>
        <div v-else-if="visibleSubmissions.length" class="divide-y divide-slate-100">
          <button v-for="item in visibleSubmissions" :key="item.id" type="button" class="w-full px-4 sm:px-6 py-3 sm:py-4 text-left hover:bg-slate-50 transition-colors" @click="goProblem(item.problem_id)">
            <div class="flex items-start gap-3">
              <span :class="['mt-1.5 w-2.5 h-2.5 rounded-full shrink-0', statusDotClass(item.status)]"></span>
              <div class="min-w-0">
                <strong class="block text-sm font-semibold text-slate-900 truncate">
                  {{ item.problem_title || `题目 ${item.problem_id}` }}
                </strong>
                <span class="block text-xs text-slate-500 mt-1">
                  {{ languageLabel(item.language) }} · {{ item.passed_count }}/{{ item.total_count }} · {{ formatDateTime(item.created_at) }}
                </span>
              </div>
            </div>
          </button>
        </div>
        <div v-else class="py-12 sm:py-16 text-center text-slate-400">还没有正式提交</div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowRight, CircleCheck, Cpu, Document, Loading, Refresh, Search } from '@element-plus/icons-vue'
import api from '@/api'

const pageSize = 12
const difficultyOptions = ['全部', '简单', '中等', '困难']
const router = useRouter()
const problems = ref([])
const tags = ref([])
const submissions = ref([])
const loading = ref(false)
const historyLoading = ref(false)
const keyword = ref('')
const difficulty = ref('全部')
const tag = ref('全部')
const problemPage = ref(1)
const totalCount = ref(0)

const fetchProblems = async () => {
  loading.value = true
  try {
    const params = {}
    if (difficulty.value !== '全部') params.difficulty = difficulty.value
    if (tag.value !== '全部') params.tag = tag.value
    if (keyword.value.trim()) params.q = keyword.value.trim()
    const { data } = await api.get('/code/problems', { params })
    problems.value = data.items || []
    tags.value = data.tags || []
    totalCount.value = data.total ?? problems.value.length
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '题库加载失败')
  } finally {
    loading.value = false
  }
}

const fetchSubmissions = async () => {
  historyLoading.value = true
  try {
    const { data } = await api.get('/code/submissions')
    submissions.value = Array.isArray(data) ? data : []
  } catch {
    submissions.value = []
  } finally {
    historyLoading.value = false
  }
}

const refreshAll = () => {
  fetchProblems()
  fetchSubmissions()
}

onMounted(refreshAll)

watch([difficulty, tag], () => {
  problemPage.value = 1
  fetchProblems()
})

let searchTimer = null
watch(keyword, () => {
  problemPage.value = 1
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(fetchProblems, 300)
})

const solvedCount = computed(() => problems.value.filter((item) => item.solved).length)
const judgableCount = computed(() => problems.value.filter((item) => item.judgable).length)
const problemTotalPages = computed(() => Math.max(1, Math.ceil(problems.value.length / pageSize)))
const visibleProblems = computed(() => problems.value.slice((problemPage.value - 1) * pageSize, problemPage.value * pageSize))
const visibleSubmissions = computed(() => submissions.value.slice(0, 12))

watch(problemTotalPages, (next) => {
  problemPage.value = Math.min(problemPage.value, next)
})

const goProblem = (id) => {
  router.push({ name: 'CodeProblem', params: { problemId: id } })
}

const difficultyClass = (value) => {
  if (value === '简单') return 'bg-green-50 text-green-700 border-green-100'
  if (value === '中等') return 'bg-amber-50 text-amber-700 border-amber-100'
  if (value === '困难') return 'bg-red-50 text-red-700 border-red-100'
  return 'bg-slate-50 text-slate-700 border-slate-200'
}

const statusClass = (problem) => {
  if (problem.solved) return 'bg-green-50 text-green-700 border-green-100'
  if (problem.judgable) return 'bg-blue-50 text-[#0066CC] border-blue-100'
  return 'bg-slate-50 text-slate-500 border-slate-100'
}

const statusDotClass = (status) => {
  if (status === 'Accepted') return 'bg-green-500'
  if (status === 'Running') return 'bg-blue-500'
  if (status === 'Judge Error' || status?.includes('Error')) return 'bg-red-500'
  return 'bg-amber-500'
}

const languageLabel = (language) => {
  const map = { python: 'Python', cpp: 'C++', java: 'Java', javascript: 'Node.js' }
  return map[language] || language
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>