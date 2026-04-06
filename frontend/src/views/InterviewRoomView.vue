<template>
  <div class="flex flex-col h-[80vh] bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
    <!-- Header -->
    <div class="bg-primary px-6 py-4 flex justify-between items-center text-white">
      <div>
        <h2 class="text-xl font-bold">面试中: {{ role }}</h2>
        <span class="text-xs opacity-80">AI面试官已准备就绪</span>
      </div>
      <el-button type="danger" plain @click="endInterview" :loading="ending">结束面试</el-button>
    </div>

    <!-- Chat Area -->
    <div class="flex-grow p-8 overflow-y-auto bg-[#F8FAFC] space-y-6" ref="chatArea">
      <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-gray-400">
        <el-icon class="is-loading text-4xl mb-4 text-primary"><component :is="Loading" /></el-icon>
        <p class="text-sm font-medium tracking-wide">正在为您协调面试官，请稍候...</p>
      </div>

      <div 
        v-for="(msg, index) in messages" 
        :key="index"
        class="flex flex-col"
        :class="msg.sender === 'user' ? 'items-end' : 'items-start'"
      >
        <span class="text-[10px] font-bold text-gray-400 mb-1 px-2 uppercase tracking-widest">
          {{ msg.sender === 'user' ? '候选人' : 'AI 面试官' }}
        </span>
        <div 
          class="max-w-[75%] rounded-2xl px-6 py-4 shadow-sm text-[15px] leading-relaxed"
          :class="msg.sender === 'user' ? 'bg-gradient-to-br from-indigo-600 to-primary text-white rounded-tr-none shadow-indigo-100' : 'bg-white text-gray-800 border border-gray-100 rounded-tl-none shadow-sm'"
        >
          {{ msg.content }}
        </div>
      </div>

      <!-- Thinking Indicator -->
      <div v-if="sending" class="flex flex-col items-start animate-pulse">
        <span class="text-[10px] font-bold text-gray-400 mb-1 px-2 uppercase tracking-widest">AI 面试官</span>
        <div class="bg-white border border-gray-100 rounded-2xl rounded-tl-none px-6 py-4 shadow-sm flex gap-1">
          <div class="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce"></div>
          <div class="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce [animation-delay:0.2s]"></div>
          <div class="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce [animation-delay:0.4s]"></div>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="p-4 bg-white border-t border-gray-200">
      <div v-if="isRecording" class="flex items-center gap-2 mb-2 px-2 py-1 bg-red-50 text-red-500 rounded-lg animate-pulse">
        <div class="w-2 h-2 bg-red-500 rounded-full"></div>
        <span class="text-xs font-bold uppercase tracking-wider">正在录音中...</span>
      </div>
      <div v-if="isTranscribing" class="flex items-center gap-2 mb-2 px-2 py-1 bg-indigo-50 text-indigo-500 rounded-lg animate-pulse">
        <el-icon class="is-loading"><component :is="Loading" /></el-icon>
        <span class="text-xs font-bold uppercase tracking-wider">AI 正在精准转录您的语音...</span>
      </div>
      <el-input
        v-model="inputMsg"
        type="textarea"
        :rows="3"
        placeholder="请输入您的回答，或点击麦克风开始语音输入..."
        resize="none"
        @keydown.enter.prevent="sendMessage"
        :disabled="sending || ending"
      ></el-input>
      <div class="flex justify-between items-center mt-3">
        <el-button 
          :type="isRecording ? 'danger' : 'info'" 
          plain 
          circle 
          @click="toggleRecording"
          :class="{ 'animate-bounce shadow-lg shadow-red-100': isRecording }"
          :disabled="sending || ending"
        >
          <el-icon><Microphone /></el-icon>
        </el-button>
        <el-button type="primary" @click="sendMessage" :loading="sending" :disabled="(!inputMsg.trim() && !isRecording) || isTranscribing || ending">
          发送 (Enter)
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, Microphone } from '@element-plus/icons-vue'
import api from '@/api'

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
      // Release microphone
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
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 60000 // Voice processing on CPU can be slow, allow 60s
    })
    
    // Add user message to chat
    messages.value.push({ sender: 'user', content: data.transcription })
    
    // Add AI response to chat
    messages.value.push({ sender: 'ai', content: data.ai_message.content })
    
    if (data.ai_message.is_final) {
      ElMessage.warning('面试已达到建议轮数，正在为您生成评估报告...')
      setTimeout(() => {
        endInterview()
      }, 2500)
    }
  } catch (err) {
    console.error('Voice upload failed:', err)
    ElMessage.error('语音转录失败，请重试或手动输入')
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
  // Use interviewId from query if provided (from Dashboard Settings Dialog)
  const idFromQuery = route.query.interviewId
  if (idFromQuery) {
    interviewId.value = parseInt(idFromQuery)
    // Fetch and display initial messages (the one generated on start)
    try {
      const { data } = await api.get(`/interview/${interviewId.value}/messages`)
      messages.value = data
      scrollToBottom()
    } catch (e) {
      // Fallback if message fetch fails
      messages.value.push({ sender: 'ai', content: `你好，我是你的${role.value}面试官。准备好了吗？我们将针对性地展开面试。` })
    }
    return
  }

  // Fallback: If no id provided (direct navigation), start a fresh default interview
  try {
    const { data } = await api.post('/interview/start', { role: role.value })
    interviewId.value = data.id
    messages.value.push({ sender: 'ai', content: `你好，我是你的${role.value}面试官。我们马上开始面试，请先做个简单的自我介绍。` })
  } catch (err) {
    ElMessage.error('无法启动面试室')
    router.push('/dashboard')
  }
})

const sendMessage = async () => {
  if (!inputMsg.value.trim() || sending.value) return
  
  const content = inputMsg.value
  messages.value.push({ sender: 'user', content })
  inputMsg.value = ''
  sending.value = true
  scrollToBottom()

  try {
    const { data } = await api.post(`/interview/${interviewId.value}/message`, { content })
    messages.value.push({ sender: 'ai', content: data.content })
    
    if (data.is_final) {
      ElMessage.warning('面试已达到建议轮数，正在为您生成评估报告...')
      setTimeout(() => {
        endInterview()
      }, 2500)
    }
  } catch (err) {
    ElMessage.error('消息发送失败')
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

const endInterview = async () => {
  ending.value = true
  try {
    // Generate Report
    const { data } = await api.post(`/interview/${interviewId.value}/end`)
    ElMessage.success('面试结束，报告已生成！')
    
    // Pass the evaluation data to report view using state
    router.push({
      name: 'Report',
      params: { id: interviewId.value },
      state: { evaluation: data.evaluation }
    })
  } catch (err) {
    ElMessage.error('结束面试时发生错误')
    ending.value = false
  }
}
</script>
