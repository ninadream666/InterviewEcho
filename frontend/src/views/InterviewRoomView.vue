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
      <el-input
        v-model="inputMsg"
        type="textarea"
        :rows="3"
        placeholder="请输入您的回答..."
        resize="none"
        @keydown.enter.prevent="sendMessage"
        :disabled="sending || ending"
      ></el-input>
      <div class="flex justify-between items-center mt-3">
        <el-button type="info" plain circle :icon="Microphone"></el-button>
        <el-button type="primary" @click="sendMessage" :loading="sending" :disabled="!inputMsg.trim() || ending">
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

const scrollToBottom = () => {
  nextTick(() => {
    if (chatArea.value) {
      chatArea.value.scrollTop = chatArea.value.scrollHeight
    }
  })
}

onMounted(async () => {
  try {
    const { data } = await api.post('/interview/start', { role: role.value })
    interviewId.value = data.id
    // Fetch initial message directly? Actually, we'd need a separate endpoint to fetch messages, but for MVP, let's pretend the mock AI gives first question soon
    // We should mock the first question by hardcoding or wait for another call if needed.
    // For now we'll fetch messages via a hypothetical endpoint or just show a default
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
