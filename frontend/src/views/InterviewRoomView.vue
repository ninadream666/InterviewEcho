<template>
  <!-- 使用原版的深色沉浸式 Layout 作为外层容器，并通过 @end-interview 触发后端的真正结束逻辑 -->
  <InterviewLayout ref="layoutRef" :role="role" @end-interview="endInterview">
    
    <!-- 内部容器：根据 isDarkMode 动态切换全局背景。采用 flex-col md:flex-row 以支持手机端上下分屏，电脑端左右分屏 -->
    <div class="flex flex-col md:flex-row h-full w-full overflow-hidden transition-colors duration-500" :class="isDarkMode ? 'bg-[#121212]' : 'bg-[#F3F4F6]'">
      
      <!-- 左侧/中央/上半部分：聊天面板。如果是代码模式，手机端高度缩为一半，电脑端宽度缩为 40% -->
      <!-- 增加 relative 属性，将悬浮按钮固定在这个面板层级，而不是随内容滚动 -->
      <div class="flex flex-col relative transition-all duration-500 ease-in-out" :class="[isCodeMode ? 'h-1/2 md:h-full md:w-[40%] border-b md:border-b-0 md:border-r' : 'h-full w-full', isDarkMode ? 'border-[#333333]' : 'border-gray-200']">
        
        <!-- 主题及模式切换悬浮按钮 (固定在当前面板的右上方，不随聊天内容滚动) -->
        <div class="absolute top-4 right-4 z-20 flex gap-2">
          <button 
            @click="isCodeMode = !isCodeMode"
            :class="isDarkMode ? 'bg-[#1E1E1E] text-gray-400 border-[#333333] hover:text-[#0066CC]' : 'bg-white text-gray-500 border-gray-200 hover:text-[#0066CC]'"
            class="px-3 py-1.5 rounded-full text-xs font-bold border shadow-sm transition-all flex items-center gap-1.5"
          >
            <el-icon><Monitor v-if="!isCodeMode" /><ChatLineRound v-else /></el-icon>
            {{ isCodeMode ? '退出代码模式' : '代码面试模式' }}
          </button>
          <button 
            @click="isDarkMode = !isDarkMode"
            :class="isDarkMode ? 'bg-[#1E1E1E] text-gray-400 border-[#333333] hover:text-white' : 'bg-white text-gray-500 border-gray-200 hover:text-[#0066CC]'"
            class="px-3 py-1.5 rounded-full text-xs font-bold border shadow-sm transition-all flex items-center gap-1.5"
          >
            <el-icon><Sunny v-if="isDarkMode" /><Moon v-else /></el-icon>
            {{ isDarkMode ? '浅色模式' : '深色沉浸' }}
          </button>
        </div>

        <!-- Chat Area (增加顶部内边距 pt-16 md:pt-20，防止内容被上方悬浮按钮遮挡) -->
        <div class="flex-grow p-6 md:p-10 pt-16 md:pt-20 overflow-y-auto space-y-6 transition-colors duration-500" :class="isDarkMode ? 'bg-[#121212]' : 'bg-[#F3F4F6]'" ref="chatArea">
          
          <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-gray-500">
            <el-icon class="is-loading text-4xl mb-4 text-[#0066CC]"><component :is="Loading" /></el-icon>
            <p class="text-sm font-medium tracking-wide">正在为您协调面试官，请稍候...</p>
          </div>

          <!-- 使用 ChatBubble 并传递主题状态 -->
          <div v-for="(msg, index) in messages" :key="index" class="w-full flex">
            <ChatBubble 
              :role="msg.sender === 'user' ? 'candidate' : 'interviewer'" 
              :content="msg.content" 
              :theme="isDarkMode ? 'dark' : 'light'"
            />
          </div>

          <!-- Thinking Indicator -->
          <div v-if="sending" class="w-full flex">
             <ChatBubble role="interviewer" status="typing" content="" :theme="isDarkMode ? 'dark' : 'light'" />
          </div>
        </div>

        <!-- Input Area (手机端适当缩小内边距) -->
        <div class="p-3 sm:p-4 md:px-10 border-t transition-colors duration-500" :class="isDarkMode ? 'bg-[#1E1E1E] border-[#333333]' : 'bg-white border-gray-200'">
          
          <div v-if="isRecording" class="flex items-center gap-2 mb-2 px-2 py-1 text-red-400 rounded animate-pulse">
            <div class="w-2 h-2 bg-red-500 rounded-full"></div>
            <span class="text-xs font-bold uppercase tracking-wider">正在录音中...</span>
          </div>
          <div v-if="isTranscribing" class="flex items-center gap-2 mb-2 px-2 py-1 text-[#0066CC] rounded animate-pulse">
            <el-icon class="is-loading"><component :is="Loading" /></el-icon>
            <span class="text-xs font-bold uppercase tracking-wider">AI 正在精准转录您的语音...</span>
          </div>

          <!-- 动态回答倒计时 -->
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
            placeholder="请输入您的回答，或点击麦克风开始语音输入..."
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
              :disabled="(!(inputMsg || '').trim() && !isRecording) || isTranscribing || ending"
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

      <!-- 右侧/下半部分面板：代码编辑器。仅在 isCodeMode 开启时渲染 (W4.3.6) -->
      <!-- 手机端高度占一半，电脑端宽度占 60% -->
      <div v-if="isCodeMode" class="h-1/2 md:h-full md:w-[60%] flex flex-col shadow-[-4px_0_15px_rgba(0,0,0,0.05)] z-20">
        <CodeEditor :theme="isDarkMode ? 'dark' : 'light'" @submit="handleCodeSubmit" />
      </div>

    </div>
  </InterviewLayout>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, Microphone, Sunny, Moon, Monitor, ChatLineRound } from '@element-plus/icons-vue'
import api from '@/api'
import ChatBubble from '@/components/business/ChatBubble.vue'
import InterviewLayout from '@/layouts/InterviewLayout.vue'
import CodeEditor from '@/components/business/CodeEditor.vue'

// 获取 Layout 组件实例，以便调用其暴露的方法
const layoutRef = ref(null)

// 核心主题状态：默认为深色暗黑风
const isDarkMode = ref(true)

// 代码面试模式状态 (W4.3.6)
const isCodeMode = ref(false)

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

// 动态超时：代码模式 30 分钟 (1800秒)，普通对话 1 分钟 (60秒)
const getTimeoutSec = () => isCodeMode.value ? 1800 : 60
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
    timeLeft.value--
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

const handleTimeout = async () => {
  if (sending.value || ending.value) return
  if (isRecording.value) {
    ElMessage.warning('回答时间到，自动结束录音并提交...')
    stopRecording()
    return
  }
  ElMessage.warning(`已超过${isCodeMode.value ? '三十' : '一'}分钟未回答，自动提交`)
  const content = (inputMsg.value || '').trim() || '（超时未回答）'
  messages.value.push({ sender: 'user', content })
  inputMsg.value = ''
  sending.value = true
  scrollToBottom()
  try {
    const { data } = await api.post(`/interview/${interviewId.value}/message`, { content })
    messages.value.push({ sender: 'ai', content: data.content })
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

const scrollToBottom = () => {
  nextTick(() => {
    if (chatArea.value) {
      chatArea.value.scrollTop = chatArea.value.scrollHeight
    }
  })
}

onMounted(async () => {
  const idFromQuery = route.query.interviewId
  if (idFromQuery) {
    interviewId.value = parseInt(idFromQuery)
    try {
      const { data } = await api.get(`/interview/${interviewId.value}/messages`)
      messages.value = data
      scrollToBottom()
    } catch (err) {
      console.error('Fetch messages error:', err)
      messages.value.push({ sender: 'ai', content: `你好，我是你的${role.value}面试官。准备好了吗？我们将针对性地展开面试。` })
    }
    return
  }

  try {
    const { data } = await api.post('/interview/start', { role: role.value })
    interviewId.value = data.id
    messages.value.push({ sender: 'ai', content: `你好，我是你的${role.value}面试官。我们马上开始面试，请先做个简单的自我介绍。` })
  } catch (err) {
    console.error('Start interview error:', err)
    ElMessage.error(`无法启动面试室: ${err.response?.data?.detail || err.message}`)
    router.push('/dashboard')
  }
})

const sendMessage = async () => {
  // 停止录音后，mediaRecorder.onstop会自动接管后续的上传和发送流程
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

// 接收来自 CodeEditor 组件的提交事件 (W4.3.6)
const handleCodeSubmit = async ({ code, language, output }) => {
  if (sending.value || ending.value) return
  
  // 将代码片段与运行结果包装为结构化文本发送给 AI
  const content = `我完成了代码编写（语言：${language}）。\n\n【我的代码】：\n\`\`\`${language}\n${code}\n\`\`\`\n\n【控制台运行结果】：\n${output || '无输出'}`
  
  inputMsg.value = content
  await sendMessage()
}

// 接收来自InterviewLayout组件的结束事件
const endInterview = async () => {
  ending.value = true
  clearTimeoutTimer() // 停止本地的回答动态倒计时
  
  // 停止顶栏的全局时间倒计时
  if (layoutRef.value && layoutRef.value.stopTimer) {
    layoutRef.value.stopTimer()
  }

  ElMessage.info('正在为整场面试进行深度评估，这可能需要几十秒，请勿关闭页面...')
  try {
    // LLM 评估通常 15-60s，单独覆盖全局 10s 超时，避免误报失败
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

// 监听代码模式切换，动态重置超时时间
watch(isCodeMode, () => {
  const last = messages.value[messages.value.length - 1]
  if (last && last.sender === 'ai' && !sending.value && !ending.value) {
    startTimeoutTimer()
  }
})

// 监听新 AI 消息 → 启动倒计时
watch(
  () => messages.value.length,
  () => {
    const last = messages.value[messages.value.length - 1]
    if (last && last.sender === 'ai') {
      startTimeoutTimer()
    }
  }
)

onBeforeUnmount(() => {
  clearTimeoutTimer()
})
</script>