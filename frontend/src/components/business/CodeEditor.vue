<template>
  <div class="flex flex-col h-full w-full" :class="theme === 'dark' ? 'bg-[#1E1E1E] text-white' : 'bg-white text-gray-800'">
    <!-- Editor Header -->
    <div class="flex justify-between items-center px-4 py-3 border-b" :class="theme === 'dark' ? 'border-[#333333]' : 'border-gray-200'">
      <div class="flex items-center gap-3">
        <span class="font-bold text-sm">代码编辑器</span>
        <select v-model="language" class="text-xs px-2 sm:px-3 py-1.5 rounded-md border focus:outline-none transition-colors" :class="theme === 'dark' ? 'bg-[#2A2A2A] border-[#444] text-gray-200 focus:border-[#0066CC]' : 'bg-gray-50 border-gray-200 focus:border-[#0066CC]'">
          <option value="python">Python</option>
          <option value="java">Java</option>
          <option value="cpp">C++</option>
          <option value="javascript">JavaScript</option>
        </select>
      </div>
      <button @click="resetCode" class="text-xs px-3 py-1.5 rounded-md border hover:opacity-80 transition-opacity" :class="theme === 'dark' ? 'border-[#444] bg-[#2A2A2A] text-gray-300' : 'border-gray-200 bg-gray-50 text-gray-600'">
        重置代码
      </button>
    </div>

    <!-- Problem Description Area (展示题目要求) -->
    <div v-if="problem" class="px-4 py-3 border-b overflow-y-auto max-h-40 shadow-inner" :class="theme === 'dark' ? 'border-[#333333] bg-[#1A1A1A]' : 'border-gray-200 bg-gray-50'">
      <div class="font-bold text-base mb-1">{{ problem.title }}</div>
      <div class="text-xs mb-3 flex gap-2">
        <span class="px-2 py-0.5 rounded font-medium" :class="theme === 'dark' ? 'bg-blue-900/40 text-blue-300' : 'bg-blue-100 text-blue-700'">{{ problem.difficulty }}</span>
        <span v-for="tag in problem.tags" :key="tag" class="px-2 py-0.5 rounded" :class="theme === 'dark' ? 'bg-[#2A2A2A] text-gray-400' : 'bg-gray-200 text-gray-600'">{{ tag }}</span>
      </div>
      <div class="text-sm whitespace-pre-wrap leading-relaxed" :class="theme === 'dark' ? 'text-gray-300' : 'text-gray-600'" v-html="problem.description"></div>
    </div>

    <!-- Monaco Editor Container -->
    <div class="flex-grow relative overflow-hidden">
      <vue-monaco-editor
        v-model:value="code"
        :language="language"
        :theme="theme === 'dark' ? 'vs-dark' : 'vs'"
        :options="{
          automaticLayout: true,
          minimap: { enabled: false },
          fontSize: 14,
          tabSize: 4,
          scrollBeyondLastLine: false,
          padding: { top: 16 }
        }"
      />
    </div>

    <!-- Console/Output Area -->
    <div class="h-56 border-t flex flex-col shadow-[0_-4px_10px_rgba(0,0,0,0.02)]" :class="theme === 'dark' ? 'border-[#333333] bg-[#121212]' : 'border-gray-200 bg-white'">
      <div class="flex justify-between items-center px-4 py-2 border-b" :class="theme === 'dark' ? 'border-[#333333]' : 'border-gray-50 bg-gray-50/50'">
        <span class="text-xs font-bold uppercase tracking-wider text-gray-500">控制台输出</span>
        <div class="flex flex-wrap gap-2">
          <button @click="runCode" :disabled="isRunning" class="text-xs px-3 sm:px-4 py-1.5 rounded-lg font-bold transition-all border border-[#0066CC] text-[#0066CC] hover:bg-blue-50 dark:hover:bg-[#0066CC]/10 disabled:opacity-50">
            <span class="flex items-center gap-1">
              <svg v-if="!isRunning" class="w-3 h-3" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
              <svg v-else class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
              {{ isRunning ? '运行中...' : '运行测试' }}
            </span>
          </button>
          <button @click="submitCode" class="text-xs px-3 sm:px-4 py-1.5 rounded-lg font-bold transition-all bg-[#0066CC] text-white hover:bg-blue-700 active:scale-95 shadow-sm">
            提交代码给面试官
          </button>
        </div>
      </div>
      <div class="flex-grow p-4 overflow-y-auto font-mono text-xs whitespace-pre-wrap leading-relaxed" :class="outputError ? 'text-red-500' : (theme === 'dark' ? 'text-gray-300' : 'text-gray-700')">
        {{ output || '（暂无输出。请编写代码并点击“运行测试”进行本地评测）' }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'
import { codeApi } from '@/api'
import { ElMessage } from 'element-plus'

const props = defineProps({
  theme: { type: String, default: 'dark' },
  problem: { type: Object, default: null }
})

const emit = defineEmits(['submit'])

const code = ref('')
const language = ref('python')
const output = ref('')
const outputError = ref(false)
const isRunning = ref(false)

const defaultCodes = {
  python: 'def solution():\n    # 在此处编写你的算法逻辑\n    pass\n\nif __name__ == "__main__":\n    solution()',
  java: 'public class Main {\n    public static void main(String[] args) {\n        // 在此处编写你的算法逻辑\n    }\n}',
  cpp: '#include <iostream>\nusing namespace std;\n\nint main() {\n    // 在此处编写你的算法逻辑\n    return 0;\n}',
  javascript: 'function solution() {\n    // 在此处编写你的算法逻辑\n}\n\nsolution();',
}

const resetCode = () => {
  code.value = props.problem?.starter_code?.[language.value] || defaultCodes[language.value]
  output.value = ''
  outputError.value = false
}

// 语言或题目改变时，如果代码为空或还是旧的默认代码，则自动切换为新代码模板
watch([language, () => props.problem], ([newLang, newProblem], [oldLang, oldProblem] = []) => {
  const defaultCode = defaultCodes[newLang]
  const backendCode = newProblem?.starter_code?.[newLang]
  
  const oldDefaultCode = oldLang ? defaultCodes[oldLang] : null
  const oldBackendCode = oldProblem?.starter_code?.[oldLang]

  if (!code.value || code.value === oldDefaultCode || code.value === oldBackendCode) {
    code.value = backendCode || defaultCode
  }
}, { immediate: true, deep: true })

const displayText = (value) => {
  if (value === null || value === undefined || value === '') return '（无输出）'
  return String(value)
}

const formatCaseResult = (item) => {
  const lines = [
    `[用例 ${item.index}] ${item.passed ? '通过' : '未通过'}（${item.status || 'Unknown'}）`
  ]
  if (item.input !== null && item.input !== undefined) {
    lines.push(`[输入]\n${displayText(item.input)}`)
  }
  if (item.expected_output !== null && item.expected_output !== undefined) {
    lines.push(`[期望输出]\n${displayText(item.expected_output)}`)
  }
  if (item.actual_output !== null && item.actual_output !== undefined) {
    lines.push(`[实际输出]\n${displayText(item.actual_output)}`)
  }
  if (item.message) {
    lines.push(`[提示]\n${item.message}`)
  }
  if (item.stderr) {
    lines.push(`[运行错误]\n${item.stderr}`)
  }
  if (item.compile_output) {
    lines.push(`[编译输出]\n${item.compile_output}`)
  }
  if (item.runtime !== null && item.runtime !== undefined) {
    lines.push(`[运行时间] ${item.runtime} s`)
  }
  if (item.memory !== null && item.memory !== undefined) {
    lines.push(`[内存] ${item.memory} KB`)
  }
  return lines.join('\n')
}

const formatRunResponse = (data) => {
  const results = Array.isArray(data?.results) ? data.results : []
  const passed = data?.passed_count ?? results.filter((item) => item.passed).length
  const total = data?.total_count ?? results.length
  const lines = [
    `[运行状态] ${data?.status || 'Unknown'}`,
    `[通过用例] ${passed}/${total}`
  ]
  if (!results.length) {
    lines.push('', '（暂无测试结果）')
    return lines.join('\n')
  }
  lines.push('', ...results.map(formatCaseResult))
  return lines.join('\n\n')
}

const runCode = async () => {
  if (!code.value.trim()) {
    ElMessage.warning('代码不能为空，请输入代码后再运行')
    return
  }
  if (!props.problem) {
    ElMessage.warning('暂无题目信息，无法运行测试')
    return
  }
  
  isRunning.value = true
  output.value = '代码提交给 Judge0 评测沙箱运行中，请稍候...'
  outputError.value = false
  try {
    const { data } = await codeApi.run(props.problem.id, {
      language: language.value,
      source_code: code.value
    })
    outputError.value = data.status !== 'Accepted' || (data.results || []).some((item) => !item.passed)
    output.value = formatRunResponse(data)
  } catch (err) {
    outputError.value = true
    output.value = err.response?.data?.detail || err.message || '运行请求失败，请检查后端 Judge0 评测服务是否已启动。'
  } finally {
    isRunning.value = false
  }
}

const submitCode = () => {
  if (!code.value.trim()) {
    ElMessage.warning('不能提交空代码')
    return
  }
  emit('submit', {
    code: code.value,
    language: language.value,
    output: output.value
  })
}
</script>
