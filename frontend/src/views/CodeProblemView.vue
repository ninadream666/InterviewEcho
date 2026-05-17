<template>
  <div class="max-w-7xl mx-auto px-4 py-4 sm:py-8 space-y-6">
    <button class="inline-flex items-center gap-2 text-sm font-semibold text-[#0066CC] hover:underline decoration-2 underline-offset-4" type="button" @click="router.push('/code')">
      <el-icon><Back /></el-icon>
      返回题库
    </button>

    <div v-if="loading" class="bg-white rounded-xl shadow-sm border border-slate-100 py-12 sm:py-24 flex items-center justify-center text-slate-400">
      <el-icon class="is-loading text-2xl mr-2 text-[#0066CC]"><Loading /></el-icon>
      正在加载题目
    </div>

    <div v-else-if="!problem" class="bg-white rounded-xl shadow-sm border border-slate-100 py-12 sm:py-24 text-center text-slate-400">
      没有找到这道题
    </div>

    <template v-else>
      <section class="bg-white rounded-xl shadow-sm border border-slate-100 p-4 sm:p-6">
        <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-5">
          <div class="min-w-0">
            <p class="text-sm font-semibold text-[#0066CC] uppercase tracking-wider mb-2">Hot100 / ACM</p>
            <h1 class="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">{{ problem.title }}</h1>
            <p class="text-slate-600 mt-4 leading-relaxed max-w-4xl">{{ problem.description }}</p>
          </div>
          <div class="flex flex-wrap gap-2 shrink-0">
            <span :class="['px-2.5 py-1 rounded-full text-xs font-semibold border', difficultyClass(problem.difficulty)]">
              {{ problem.difficulty }}
            </span>
            <span :class="['px-2.5 py-1 rounded-full text-xs font-semibold border', problem.solved ? 'bg-green-50 text-green-700 border-green-100' : 'bg-blue-50 text-[#0066CC] border-blue-100']">
              {{ problem.solved ? '已通过' : problem.judgable ? `${problem.test_count} 组测试` : '暂未开放' }}
            </span>
          </div>
        </div>
      </section>

      <div class="grid grid-cols-1 xl:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)] gap-6 items-start">
        <article class="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
          <div class="px-4 sm:px-6 py-3 sm:py-4 border-b border-slate-100">
            <h2 class="text-lg font-bold text-slate-800 flex items-center">
              <span class="w-1.5 h-5 bg-[#0066CC] rounded-full mr-2"></span>
              题面
            </h2>
          </div>
          <div class="p-4 sm:p-6 space-y-6">
            <StatementBlock title="输入格式" :text="problem.input_format" />
            <StatementBlock title="输出格式" :text="problem.output_format" />

            <section>
              <h3 class="text-base font-bold text-slate-800 mb-3">样例</h3>
              <div class="space-y-4">
                <div v-for="(sample, index) in problem.samples" :key="`${problem.id}-sample-${index}`" class="rounded-xl border border-slate-100 bg-slate-50 overflow-hidden">
                  <div class="px-4 py-2 text-xs font-semibold text-slate-500 border-b border-slate-100 bg-white">Sample {{ index + 1 }}</div>
                  <div class="p-4 space-y-3">
                    <div>
                      <p class="text-xs font-semibold text-slate-500 mb-1">输入</p>
                      <pre class="code-block">{{ sample.input || '(空输入)' }}</pre>
                    </div>
                    <div>
                      <p class="text-xs font-semibold text-slate-500 mb-1">输出</p>
                      <pre class="code-block">{{ sample.output || '(空输出)' }}</pre>
                    </div>
                    <p v-if="sample.explanation" class="text-sm text-slate-500 leading-relaxed">{{ sample.explanation }}</p>
                  </div>
                </div>
              </div>
            </section>

            <section>
              <h3 class="text-base font-bold text-slate-800 mb-3">约束</h3>
              <ul class="space-y-2">
                <li v-for="item in problem.constraints" :key="item" class="flex gap-2 text-sm text-slate-600 leading-relaxed">
                  <span class="mt-2 w-1.5 h-1.5 rounded-full bg-[#0066CC] shrink-0"></span>
                  <span>{{ item }}</span>
                </li>
              </ul>
            </section>
          </div>
        </article>

        <section class="space-y-6">
          <div class="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
            <div class="px-4 sm:px-6 py-3 sm:py-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <h2 class="text-lg font-bold text-slate-800 flex items-center">
                <span class="w-1.5 h-5 bg-[#0066CC] rounded-full mr-2"></span>
                代码编辑
              </h2>
              <div class="flex items-center gap-2">
                <el-select :model-value="language" size="large" class="!w-36" @change="handleLanguageChange">
                  <el-option v-for="item in languageOptions" :key="item.value" :label="item.label" :value="item.value" />
                </el-select>
                <button class="inline-flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-slate-200 text-slate-600 text-sm font-semibold hover:border-[#0066CC] hover:text-[#0066CC] transition-colors" type="button" @click="resetStarter">
                  <el-icon><RefreshLeft /></el-icon>
                  重置
                </button>
              </div>
            </div>

            <textarea v-model="sourceCode" spellcheck="false" class="w-full min-h-[460px] resize-y bg-[#0f172a] text-slate-100 p-5 font-mono text-sm leading-6 outline-none border-0 block"></textarea>

            <div class="px-4 sm:px-6 py-3 sm:py-4 border-t border-slate-100 flex flex-col sm:flex-row gap-3 sm:justify-end">
              <button class="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg border border-[#0066CC] text-[#0066CC] text-sm font-semibold hover:bg-[#E6F0FA] transition-colors disabled:opacity-60 disabled:cursor-not-allowed" type="button" :disabled="busy || !problem.sample_count" @click="runCode">
                <el-icon :class="{ 'is-loading': running }"><Loading v-if="running" /><VideoPlay v-else /></el-icon>
                运行样例
              </button>
              <button class="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-[#0066CC] hover:bg-blue-700 text-white text-sm font-semibold transition-colors disabled:opacity-60 disabled:cursor-not-allowed" type="button" :disabled="busy || !problem.judgable" @click="submitCode">
                <el-icon :class="{ 'is-loading': submitting }"><Loading v-if="submitting" /><Upload v-else /></el-icon>
                提交评测
              </button>
            </div>
          </div>

          <div class="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
            <div class="px-4 sm:px-6 py-3 sm:py-4 border-b border-slate-100">
              <h2 class="text-lg font-bold text-slate-800 flex items-center">
                <span class="w-1.5 h-5 bg-[#0066CC] rounded-full mr-2"></span>
                运行结果
              </h2>
            </div>

            <div v-if="!result" class="py-8 sm:py-14 text-center text-slate-400">运行样例或提交后，结果会显示在这里</div>

            <div v-else class="p-4 sm:p-6 space-y-4">
              <div :class="['rounded-xl border p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2', resultSummaryClass(result.status)]">
                <div>
                  <p class="text-xs font-semibold uppercase tracking-wider opacity-70">{{ resultMode === 'submit' ? 'Submit' : 'Run' }}</p>
                  <strong class="text-lg">{{ result.status }}</strong>
                </div>
                <span class="text-sm font-semibold">{{ result.passed_count }}/{{ result.total_count }} 通过</span>
              </div>

              <div v-if="result.results?.length" class="space-y-3">
                <div v-for="item in result.results" :key="`${item.index}-${item.status}`" :class="['rounded-xl border p-4', item.passed ? 'border-green-100 bg-green-50/50' : 'border-red-100 bg-red-50/40']">
                  <div class="flex items-center justify-between gap-3 mb-3">
                    <strong class="text-sm text-slate-800">Case {{ item.index }}{{ item.is_sample ? ' · Sample' : '' }}</strong>
                    <span :class="['inline-flex items-center gap-1.5 text-xs font-semibold', item.passed ? 'text-green-700' : 'text-red-700']">
                      <el-icon><CircleCheck v-if="item.passed" /><CircleClose v-else /></el-icon>
                      {{ item.status }}
                    </span>
                  </div>
                  <p v-if="item.message" class="text-sm text-slate-600 mb-3">{{ item.message }}</p>
                  <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div v-if="item.input !== null && item.input !== undefined" class="min-w-0">
                      <p class="text-xs font-semibold text-slate-500 mb-1">输入</p>
                      <pre class="code-block">{{ item.input || '(空输入)' }}</pre>
                    </div>
                    <div v-if="item.expected_output !== null && item.expected_output !== undefined" class="min-w-0">
                      <p class="text-xs font-semibold text-slate-500 mb-1">期望</p>
                      <pre class="code-block">{{ item.expected_output || '(空输出)' }}</pre>
                    </div>
                    <div v-if="item.actual_output !== null && item.actual_output !== undefined" class="min-w-0">
                      <p class="text-xs font-semibold text-slate-500 mb-1">实际</p>
                      <pre class="code-block">{{ item.actual_output || '(空输出)' }}</pre>
                    </div>
                  </div>
                  <pre v-if="item.stderr" class="code-block mt-3 text-red-200">{{ item.stderr }}</pre>
                  <pre v-if="item.compile_output" class="code-block mt-3 text-amber-200">{{ item.compile_output }}</pre>
                </div>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
            <div class="px-4 sm:px-6 py-3 sm:py-4 border-b border-slate-100">
              <h2 class="text-lg font-bold text-slate-800 flex items-center">
                <span class="w-1.5 h-5 bg-[#0066CC] rounded-full mr-2"></span>
                本题提交
              </h2>
            </div>
            <div v-if="submissionLoading" class="py-8 sm:py-12 flex items-center justify-center text-slate-400">
              <el-icon class="is-loading text-2xl mr-2 text-[#0066CC]"><Loading /></el-icon>
              正在读取提交
            </div>
            <div v-else-if="submissions.length" class="divide-y divide-slate-100">
              <div v-for="item in submissions.slice(0, 6)" :key="item.id" class="px-4 sm:px-6 py-3 sm:py-4 flex items-center justify-between gap-3">
                <div class="min-w-0">
                  <strong class="block text-sm text-slate-900">{{ item.status }}</strong>
                  <span class="text-xs text-slate-500">{{ languageLabel(item.language) }} · {{ item.passed_count }}/{{ item.total_count }} · {{ formatDateTime(item.created_at) }}</span>
                </div>
                <span :class="['shrink-0 px-2.5 py-1 rounded-full text-xs font-semibold border', statusPillClass(item.status)]">{{ item.status }}</span>
              </div>
            </div>
            <div v-else class="py-8 sm:py-12 text-center text-slate-400">本题还没有正式提交</div>
          </div>
        </section>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back, CircleCheck, CircleClose, Loading, RefreshLeft, Upload, VideoPlay } from '@element-plus/icons-vue'
import api from '@/api'

const StatementBlock = defineComponent({
  props: {
    title: { type: String, required: true },
    text: { type: String, default: '' },
  },
  setup(props) {
    return () =>
      h('section', [
        h('h3', { class: 'text-base font-bold text-slate-800 mb-3' }, props.title),
        h('p', { class: 'text-sm text-slate-600 leading-relaxed whitespace-pre-line' }, props.text),
      ])
  },
})

const route = useRoute()
const router = useRouter()
const problem = ref(null)
const submissions = ref([])
const loading = ref(false)
const submissionLoading = ref(false)
const running = ref(false)
const submitting = ref(false)
const language = ref('python')
const sourceCode = ref('')
const codeByLanguage = ref({})
const result = ref(null)
const resultMode = ref('')
const pollTimers = new Set()

const languageOptions = [
  { value: 'python', label: 'Python 3' },
  { value: 'cpp', label: 'C++17' },
  { value: 'java', label: 'Java' },
  { value: 'javascript', label: 'Node.js' },
]

const busy = computed(() => running.value || submitting.value)

const sleep = (ms) =>
  new Promise((resolve) => {
    const timer = window.setTimeout(() => {
      pollTimers.delete(timer)
      resolve()
    }, ms)
    pollTimers.add(timer)
  })

const getErrorMessage = (err, fallback) => err.response?.data?.detail || err.message || fallback

const fetchProblem = async () => {
  loading.value = true
  try {
    const { data } = await api.get(`/code/problems/${route.params.problemId}`)
    problem.value = data
    const starter = data.starter_code || {}
    const preferred = starter[language.value] !== undefined ? language.value : 'python'
    language.value = preferred
    codeByLanguage.value = { ...starter }
    sourceCode.value = starter[preferred] || ''
    result.value = null
    resultMode.value = ''
  } catch (err) {
    problem.value = null
    ElMessage.error(getErrorMessage(err, '题目加载失败'))
  } finally {
    loading.value = false
  }
}

const fetchSubmissions = async () => {
  if (!route.params.problemId) return
  submissionLoading.value = true
  try {
    const { data } = await api.get('/code/submissions', { params: { problem_id: route.params.problemId } })
    submissions.value = Array.isArray(data) ? data : []
  } catch {
    submissions.value = []
  } finally {
    submissionLoading.value = false
  }
}

const loadPage = async () => {
  await fetchProblem()
  await fetchSubmissions()
}

onMounted(loadPage)

watch(
  () => route.params.problemId,
  () => loadPage(),
)

onBeforeUnmount(() => {
  pollTimers.forEach((timer) => window.clearTimeout(timer))
  pollTimers.clear()
})

const handleLanguageChange = (nextLanguage) => {
  if (nextLanguage === language.value) return
  const previous = language.value
  codeByLanguage.value = { ...codeByLanguage.value, [previous]: sourceCode.value }
  sourceCode.value = codeByLanguage.value[nextLanguage] ?? problem.value?.starter_code?.[nextLanguage] ?? ''
  language.value = nextLanguage
}

const resetStarter = () => {
  const starter = problem.value?.starter_code?.[language.value] || ''
  sourceCode.value = starter
  codeByLanguage.value = { ...codeByLanguage.value, [language.value]: starter }
  result.value = null
  resultMode.value = ''
}

const makeErrorResult = (message, totalCount) => ({
  status: 'Judge Error',
  passed_count: 0,
  total_count: totalCount || 0,
  results: [{ index: 1, is_sample: false, passed: false, status: 'Judge Error', message }],
})

const runCode = async () => {
  if (!problem.value) return
  running.value = true
  result.value = null
  resultMode.value = 'run'
  try {
    const { data } = await api.post(`/code/problems/${problem.value.id}/run`, { language: language.value, source_code: sourceCode.value }, { timeout: 45000 })
    result.value = data
    ElMessage({ type: data.status === 'Accepted' ? 'success' : 'warning', message: data.status === 'Accepted' ? '样例已通过' : `样例结果：${data.status}` })
  } catch (err) {
    const message = getErrorMessage(err, '样例运行失败')
    result.value = makeErrorResult(message, problem.value.sample_count || 0)
    ElMessage.error(message)
  } finally {
    running.value = false
  }
}

const toSubmissionResult = (detail) => {
  const results = detail.results?.length
    ? detail.results
    : detail.stderr
      ? [{ index: 1, is_sample: false, passed: false, status: detail.status, message: detail.stderr }]
      : []
  return {
    submission_id: detail.id,
    status: detail.status,
    passed_count: detail.passed_count,
    total_count: detail.total_count,
    results,
  }
}

const waitForSubmission = async (submissionId) => {
  let latest = null
  for (let index = 0; index < 30; index += 1) {
    if (index > 0) await sleep(1000)
    const { data } = await api.get(`/code/submissions/${submissionId}`, { timeout: 45000 })
    latest = toSubmissionResult(data)
    result.value = latest
    resultMode.value = 'submit'
    if (latest.status !== 'Running') return latest
  }
  return latest
}

const submitCode = async () => {
  if (!problem.value) return
  submitting.value = true
  result.value = null
  resultMode.value = 'submit'
  codeByLanguage.value = { ...codeByLanguage.value, [language.value]: sourceCode.value }
  try {
    const { data } = await api.post(`/code/problems/${problem.value.id}/submit`, { language: language.value, source_code: sourceCode.value }, { timeout: 45000 })
    result.value = data
    const finalResult = data.submission_id ? await waitForSubmission(data.submission_id) : data
    await fetchSubmissions()
    if (finalResult?.status === 'Accepted') {
      ElMessage.success('提交通过')
      problem.value.solved = true
    } else {
      ElMessage.warning(finalResult?.status ? `提交结果：${finalResult.status}` : '提交已进入评测队列')
    }
  } catch (err) {
    const message = getErrorMessage(err, '提交失败')
    result.value = makeErrorResult(message, problem.value.test_count || 0)
    await fetchSubmissions()
    ElMessage.error(message)
  } finally {
    submitting.value = false
  }
}

const difficultyClass = (value) => {
  if (value === '简单') return 'bg-green-50 text-green-700 border-green-100'
  if (value === '中等') return 'bg-amber-50 text-amber-700 border-amber-100'
  if (value === '困难') return 'bg-red-50 text-red-700 border-red-100'
  return 'bg-slate-50 text-slate-700 border-slate-200'
}

const resultSummaryClass = (status) => {
  if (status === 'Accepted') return 'bg-green-50 text-green-800 border-green-100'
  if (status === 'Running') return 'bg-blue-50 text-[#0066CC] border-blue-100'
  if (status === 'Judge Error' || status?.includes('Error')) return 'bg-red-50 text-red-800 border-red-100'
  return 'bg-amber-50 text-amber-800 border-amber-100'
}

const statusPillClass = (status) => {
  if (status === 'Accepted') return 'bg-green-50 text-green-700 border-green-100'
  if (status === 'Running') return 'bg-blue-50 text-[#0066CC] border-blue-100'
  if (status === 'Judge Error' || status?.includes('Error')) return 'bg-red-50 text-red-700 border-red-100'
  return 'bg-amber-50 text-amber-700 border-amber-100'
}

const languageLabel = (value) => {
  const map = { python: 'Python', cpp: 'C++', java: 'Java', javascript: 'Node.js' }
  return map[value] || value
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.code-block {
  overflow-x: auto;
  border-radius: 0.5rem;
  background: #0f172a;
  color: #e2e8f0;
  padding: 0.75rem;
  font-size: 0.8125rem;
  line-height: 1.45;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>