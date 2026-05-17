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
          <option value="go">Go</option>
        </select>
      </div>
      <button @click="resetCode" class="text-xs px-3 py-1.5 rounded-md border hover:opacity-80 transition-opacity" :class="theme === 'dark' ? 'border-[#444] bg-[#2A2A2A] text-gray-300' : 'border-gray-200 bg-gray-50 text-gray-600'">
        重置代码
      </button>
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
  theme: { type: String, default: 'dark' }
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
  go: 'package main\n\nimport "fmt"\n\nfunc main() {\n    // 在此处编写你的算法逻辑\n}'
}

const resetCode = () => {
  code.value = defaultCodes[language.value]
  output.value = ''
  outputError.value = false
}

// 语言改变时，如果代码为空或还是旧语言的默认代码，则自动切换为新语言的默认代码
watch(language, (newLang, oldLang) => {
  if (!code.value || code.value === defaultCodes[oldLang]) {
    code.value = defaultCodes[newLang]
  }
}, { immediate: true })

const runCode = async () => {
  if (!code.value.trim()) {
    ElMessage.warning('代码不能为空，请输入代码后再运行')
    return
  }
  isRunning.value = true
  output.value = '代码提交给 Judge0 评测沙箱运行中，请稍候...'
  outputError.value = false
  try {
    const { data } = await codeApi.run({
      language: language.value,
      source_code: code.value
    })
    
    // 兼容后端 Judge0 封装的可能返回结构 (stdout, stderr, compile_output 等)
    if (data.stderr || data.compile_output) {
      outputError.value = true
      output.value = data.compile_output || data.stderr
    } else {
      let resultStr = ''
      if (data.status && data.status.description) {
        resultStr += `[执行状态] ${data.status.description}\n`
      }
      if (data.time) resultStr += `[执行时间] ${data.time} s\n`
      if (data.memory) resultStr += `[内存消耗] ${data.memory} KB\n\n`
      
      resultStr += `[标准输出]\n${data.stdout || '（无输出）'}`
      output.value = resultStr
    }
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