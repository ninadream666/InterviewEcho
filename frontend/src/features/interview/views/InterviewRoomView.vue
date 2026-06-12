<!--
  组件名称：InterviewRoomView（面试房间视图）
  功能描述：面试的核心交互界面，包含：
  - 与 AI 面试官的实时对话（聊天气泡）
  - 语音录音和 Whisper 转录
  - 深色/浅色主题切换
  - 代码题面板（CodeEditor 集成）
  - 回答倒计时
  - 阶段自动流转（自我介绍 → 简历深挖 → 项目深挖 → 代码题 → 知识问答）
-->
<template>
  <InterviewLayout ref="layoutRef" :role="role" @end-interview="endInterview">
    <div class="flex flex-col md:flex-row h-full w-full overflow-hidden transition-colors duration-500" :class="isDarkMode ? 'bg-[#121212]' : 'bg-[#F3F4F6]'">
      <div class="flex flex-col relative transition-all duration-500 ease-in-out" :class="[showCodePanel ? 'h-1/2 md:h-full md:w-[40%] border-b md:border-b-0 md:border-r' : 'h-full w-full', isDarkMode ? 'border-[#333333]' : 'border-gray-200']">
        <div class="absolute top-4 right-4 z-20 flex items-center gap-2">
          <span
            class="px-3 py-1.5 rounded-full text-[11px] font-bold tracking-wider border shadow-sm"
            :class="isDarkMode ? 'bg-[#1E1E1E] text-[#9CC7FF] border-[#333333]' : 'bg-white text-[#0066CC] border-gray-200'"
          >
            {{ phaseLabel }}
          </span>
          <button
            @click="isDarkMode = !isDarkMode"
            :class="isDarkMode ? 'bg-[#1E1E1E] text-gray-400 border-[#333333] hover:text-white' : 'bg-white text-gray-500 border-gray-200 hover:text-[#0066CC]'"
            class="px-3 py-1.5 rounded-full text-xs font-bold border shadow-sm transition-all flex items-center gap-1.5"
          >
            <el-icon><Sunny v-if="isDarkMode" /><Moon v-else /></el-icon>
            {{ isDarkMode ? '浅色模式' : '深色沉浸' }}
          </button>
        </div>

        <div class="flex-grow p-6 md:p-10 pt-16 md:pt-20 overflow-y-auto space-y-6 transition-colors duration-500" :class="isDarkMode ? 'bg-[#121212]' : 'bg-[#F3F4F6]'" ref="chatArea">
          <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-gray-500">
            <el-icon class="is-loading text-4xl mb-4 text-[#0066CC]"><component :is="Loading" /></el-icon>
            <p class="text-sm font-medium tracking-wide">正在为您协调面试官，请稍候...</p>
          </div>

          <div v-for="(msg, index) in messages" :key="index" class="w-full flex">
            <ChatBubble
              :role="msg.sender === 'user' ? 'candidate' : 'interviewer'"
              :content="msg.content"
              :theme="isDarkMode ? 'dark' : 'light'"
            />
          </div>

          <div v-if="sending" class="w-full flex">
            <ChatBubble role="interviewer" status="typing" content="" :theme="isDarkMode ? 'dark' : 'light'" />
          </div>
        </div>

        <div class="p-3 sm:p-4 md:px-10 border-t transition-colors duration-500" :class="isDarkMode ? 'bg-[#1E1E1E] border-[#333333]' : 'bg-white border-gray-200'">
          <div v-if="isRecording" class="flex items-center gap-2 mb-2 px-2 py-1 text-red-400 rounded animate-pulse">
            <div class="w-2 h-2 bg-red-500 rounded-full"></div>
            <span class="text-xs font-bold uppercase tracking-wider">正在录音中...</span>
          </div>
          <div v-if="isTranscribing" class="flex items-center gap-2 mb-2 px-2 py-1 text-[#0066CC] rounded animate-pulse">
            <el-icon class="is-loading"><component :is="Loading" /></el-icon>
            <span class="text-xs font-bold uppercase tracking-wider">AI 正在精准转录您的语音...</span>
          </div>

          <div
            v-if="!sending && !ending && messages.length > 0 && messages[messages.length - 1].sender === 'ai'"
            class="flex items-center gap-2 mb-2 px-2 py-1 rounded"
            :class="timeLeft <= 10 ? 'text-red-400' : timeLeft <= 20 ? 'text-yellow-400' : 'text-gray-400'"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span class="text-xs font-mono font-bold tracking-wider">
              {{ Math.floor(timeLeft / 60) }}:{{ String(timeLeft % 60).padStart(2, '0') }}
            </span>
            <span class="text-xs">剩余回答时间</span>
          </div>

          <textarea
            v-model="inputMsg"
            rows="3"
            :placeholder="showCodePanel ? '当前处于代码题阶段，如需补充说明可在此输入；正式作答请使用右侧编辑器。' : '请输入您的回答，或点击麦克风开始语音输入...'"
            :class="isDarkMode ? 'bg-[#2A2A2A] text-gray-200 border-[#444444] focus:border-[#0066CC]' : 'bg-gray-50 text-gray-800 border-gray-200 focus:border-[#0066CC]'"
            class="w-full rounded-lg p-4 text-sm focus:outline-none resize-none transition-colors duration-300 shadow-inner"
            @keydown.enter.prevent="sendMessage"
            :disabled="sending || ending"
          ></textarea>

          <div class="flex justify-between items-center mt-3">
            <button
              @click="toggleRecording"
              :disabled="sending || ending"
              :class="[
                'w-11 h-11 rounded-full flex items-center justify-center transition-all',
                isRecording
                  ? 'bg-red-500/20 text-red-500 border border-red-500/50 animate-pulse shadow-lg shadow-red-500/20'
                  : (isDarkMode ? 'bg-[#2A2A2A] text-gray-400 hover:text-white border border-[#444444]' : 'bg-gray-100 text-gray-500 hover:text-[#0066CC] border border-gray-200')
              ]"
            >
              <el-icon class="text-xl"><Microphone /></el-icon>
            </button>

            <button
              @click="sendMessage"
              :disabled="(!(inputMsg || '').trim() && !isRecording) || isTranscribing || ending || sending"
              :class="[
                'px-8 py-2.5 rounded-lg text-sm font-bold transition-all shadow-md active:scale-95',
                (!(inputMsg || '').trim() && !isRecording) || isTranscribing || ending || sending
                  ? (isDarkMode ? 'bg-[#2A2A2A] text-gray-600 cursor-not-allowed shadow-none' : 'bg-gray-100 text-gray-400 cursor-not-allowed shadow-none')
                  : 'bg-[#0066CC] hover:bg-blue-700 text-white'
              ]"
            >
              {{ sending ? '发送中...' : '发送 (Enter)' }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="showCodePanel" class="h-1/2 md:h-full md:w-[60%] flex flex-col shadow-[-4px_0_15px_rgba(0,0,0,0.05)] z-20">
        <CodeEditor :theme="isDarkMode ? 'dark' : 'light'" :problem="currentProblem" @submit="handleCodeSubmit" />
      </div>
    </div>
  </InterviewLayout>
</template>

<script setup>
// ============================================================
// 面试房间 — 核心交互逻辑
// ============================================================
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, Microphone, Sunny, Moon } from '@element-plus/icons-vue'
import api, { interviewApi } from '@/api'
import ChatBubble from '@/components/business/ChatBubble.vue'
import InterviewLayout from '@/layouts/InterviewLayout.vue'
import CodeEditor from '@/components/business/CodeEditor.vue'

const layoutRef = ref(null)
const isDarkMode = ref(true)
const currentProblem = ref(null)
const interviewState = ref(null)

const route = useRoute()
const router = useRouter()
const role = ref(route.params.role)
const interviewId = ref(null)
const messages = ref([])
const inputMsg = ref('')
const chatArea = ref(null)

const sending = ref(false)
const ending = ref(false)
const isRecording = ref(false)
const isTranscribing = ref(false)
let mediaRecorder = null
let audioChunks = []

const isCodePhase = computed(() => interviewState.value?.phase === 'code')
const showCodePanel = computed(() => isCodePhase.value && !!currentProblem.value)
const phaseLabel = computed(() => {
  const phase = interviewState.value?.phase
  const map = {
    introduction: '当前阶段：自我介绍',
    resume: '当前阶段：简历深挖',
    repo: '当前阶段：项目深挖',
    code: '当前阶段：代码题作答',
    knowledge: `当前阶段：知识问答 ${interviewState.value?.knowledge_round_index || 0}/${interviewState.value?.knowledge_round_total || 0}`,
    completed: '当前阶段：面试收尾'
  }
  return map[phase] || '当前阶段：准备中'
})

const getTimeoutSec = () => (isCodePhase.value ? 1800 : 60)
const timeLeft = ref(getTimeoutSec())
let timeoutTimer = null
let countdownInterval = null

const stopCountdown = () => {
  if (countdownInterval) {
    clearInterval(countdownInterval)
    countdownInterval = null
  }
}

const startCountdown = () => {
  stopCountdown()
  timeLeft.value = getTimeoutSec()
  countdownInterval = setInterval(() => {
    timeLeft.value -= 1
    if (timeLeft.value <= 0) {
      stopCountdown()
    }
  }, 1000)
}

const clearTimeoutTimer = () => {
  if (timeoutTimer) {
    clearTimeout(timeoutTimer)
    timeoutTimer = null
  }
  stopCountdown()
}

const startTimeoutTimer = () => {
  clearTimeoutTimer()
  if (ending.value) return
  startCountdown()
  timeoutTimer = setTimeout(() => {
    handleTimeout()
  }, getTimeoutSec() * 1000)
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatArea.value) {
      chatArea.value.scrollTop = chatArea.value.scrollHeight
    }
  })
}

const refreshState = async () => {
  if (!interviewId.value) return
  const { data } = await interviewApi.getState(interviewId.value)
  interviewState.value = data
  currentProblem.value = data.active_code_problem || null
}

const refreshMessages = async () => {
  if (!interviewId.value) return
  const { data } = await api.get(`/interview/${interviewId.value}/messages`)
  messages.value = Array.isArray(data) ? data : []
  scrollToBottom()
}

const hydrateInterview = async () => {
  await Promise.all([refreshState(), refreshMessages()])
}

const handleTimeout = async () => {
  if (sending.value || ending.value) return
  if (isRecording.value) {
    ElMessage.warning('回答时间到，自动结束录音并提交...')
    stopRecording()
    return
  }
  ElMessage.warning(`已超过${isCodePhase.value ? '三十' : '一'}分钟未回答，自动提交`)
  const content = (inputMsg.value || '').trim() || '（超时未回答）'
  messages.value.push({ sender: 'user', content })
  inputMsg.value = ''
  sending.value = true
  scrollToBottom()
  try {
    const { data } = await api.post(`/interview/${interviewId.value}/message`, { content })
    messages.value.push({ sender: 'ai', content: data.content })
    await refreshState()
    if (data.is_final) {
      ElMessage.warning('面试已完成，正在为您生成评估报告...')
      setTimeout(() => { endInterview() }, 2500)
    }
  } catch (err) {
    console.error('Timeout send error:', err)
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new MediaRecorder(stream)
    audioChunks = []

    mediaRecorder.ondataavailable = (event) => {
      audioChunks.push(event.data)
    }

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
      await uploadVoice(audioBlob)
      stream.getTracks().forEach(track => track.stop())
    }

    mediaRecorder.start()
    isRecording.value = true
    ElMessage.info('正在录音，请说话...')
  } catch (err) {
    console.error('Failed to start recording:', err)
    ElMessage.error('无法访问麦克风，请检查权限设置')
  }
}

const stopRecording = () => {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
    isRecording.value = false
  }
}

const uploadVoice = async (blob) => {
  isTranscribing.value = true
  sending.value = true

  const formData = new FormData()
  formData.append('file', blob, 'voice.webm')

  try {
    const { data } = await api.post(`/interview/${interviewId.value}/voice`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 180000
    })

    messages.value.push({ sender: 'user', content: data.transcription })
    messages.value.push({ sender: 'ai', content: data.ai_message.content })
    await refreshState()

    if (data.ai_message.is_final) {
      ElMessage.warning('面试已完成，正在为您生成评估报告...')
      setTimeout(() => { endInterview() }, 2500)
    }
  } catch (err) {
    console.error('Voice upload failed:', err)
    ElMessage.error(`语音转录或回复失败: ${err.response?.data?.detail || err.message}`)
  } finally {
    isTranscribing.value = false
    sending.value = false
    scrollToBottom()
  }
}

const toggleRecording = async () => {
  if (isRecording.value) {
    stopRecording()
  } else {
    await startRecording()
  }
}

onMounted(async () => {
  const idFromQuery = route.query.interviewId
  if (idFromQuery) {
    interviewId.value = parseInt(idFromQuery, 10)
    try {
      await hydrateInterview()
    } catch (err) {
      console.error('Hydrate interview error:', err)
      ElMessage.error('恢复面试状态失败，请返回重试')
    }
    return
  }

  try {
    const { data } = await api.post('/interview/start', { role: role.value })
    interviewId.value = data.id
    await hydrateInterview()
  } catch (err) {
    console.error('Start interview error:', err)
    ElMessage.error(`无法启动面试室: ${err.response?.data?.detail || err.message}`)
    router.push('/dashboard')
  }
})

const sendMessage = async () => {
  if (isRecording.value) {
    stopRecording()
    return
  }

  if (!(inputMsg.value || '').trim() || sending.value) return

  const content = inputMsg.value
  messages.value.push({ sender: 'user', content })
  inputMsg.value = ''
  sending.value = true
  scrollToBottom()

  try {
    const { data } = await api.post(`/interview/${interviewId.value}/message`, { content })
    messages.value.push({ sender: 'ai', content: data.content })
    await refreshState()

    if (data.is_final) {
      ElMessage.warning('面试已完成，正在为您生成评估报告...')
      setTimeout(() => { endInterview() }, 2500)
    }
  } catch (err) {
    console.error('Send message error:', err)
    ElMessage.error(`消息发送失败: ${err.response?.data?.detail || err.message}`)
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

const handleCodeSubmit = async ({ code, language }) => {
  if (sending.value || ending.value) return

  sending.value = true
  try {
    const { data } = await interviewApi.submitCode(interviewId.value, {
      language,
      source_code: code
    })
    await refreshMessages()
    await refreshState()

    if (data.status === 'Accepted') {
      ElMessage.success('代码提交通过，面试官已继续追问')
    } else {
      ElMessage.warning(`代码提交结果：${data.status}`)
    }

    if (data.ai_message?.is_final) {
      ElMessage.warning('面试已完成，正在为您生成评估报告...')
      setTimeout(() => { endInterview() }, 2500)
    }
  } catch (err) {
    console.error('Submit interview code error:', err)
    ElMessage.error(`代码提交失败: ${err.response?.data?.detail || err.message}`)
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

const endInterview = async () => {
  if (ending.value) return
  ending.value = true
  clearTimeoutTimer()

  if (layoutRef.value && layoutRef.value.stopTimer) {
    layoutRef.value.stopTimer()
  }

  ElMessage.info('正在为整场面试进行深度评估，这可能需要几十秒，请勿关闭页面...')
  try {
    const { data } = await api.post(`/interview/${interviewId.value}/end`, null, { timeout: 180000 })
    ElMessage.success('面试结束，报告已生成！')

    router.push({
      name: 'Report',
      params: { id: interviewId.value },
      state: { evaluation: data.evaluation }
    })
  } catch (err) {
    console.error('End interview error:', err)
    ElMessage.error(`生成评估报告失败: ${err.response?.data?.detail || err.message}`)
    ending.value = false
  }
}

watch(
  () => messages.value.length,
  () => {
    const last = messages.value[messages.value.length - 1]
    if (last && last.sender === 'ai' && !ending.value) {
      startTimeoutTimer()
    }
  }
)

watch(() => interviewState.value?.phase, () => {
  const last = messages.value[messages.value.length - 1]
  if (last && last.sender === 'ai' && !sending.value && !ending.value) {
    startTimeoutTimer()
  }
})

onBeforeUnmount(() => {
  clearTimeoutTimer()
})
</script>
