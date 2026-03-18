<template>
  <div class="flex h-full w-full overflow-hidden">
    
    <!-- BEGIN: LeftColumn (AI & Chat 占35%宽度) -->
    <section class="w-[35%] flex flex-col border-r border-[#333333] shrink-0">
      
      <!-- Top Section: AI Voice/Video Visualizer -->
      <!-- 后续这里会替换为你封装的 AudioVisualizer.vue 组件 -->
      <div class="h-1/2 p-6 flex flex-col items-center justify-center border-b border-[#333333] bg-[#121212]">
        <div class="text-xs text-gray-500 mb-6 uppercase tracking-widest">AI 面试官</div>
        
        <!-- Voice Waveform Placeholder (语音波形占位) -->
        <div class="flex items-end justify-center space-x-1 h-24 w-full max-w-xs">
          <div class="w-1 bg-blue-500 h-8 rounded-full opacity-60"></div>
          <div class="w-1 bg-blue-400 h-16 rounded-full opacity-70"></div>
          <div class="w-1 bg-blue-300 h-24 rounded-full opacity-90"></div>
          <div class="w-1 bg-white h-12 rounded-full"></div>
          <div class="w-1 bg-blue-300 h-20 rounded-full opacity-90"></div>
          <div class="w-1 bg-blue-400 h-14 rounded-full opacity-70"></div>
          <div class="w-1 bg-blue-500 h-6 rounded-full opacity-60"></div>
        </div>
        
        <div class="mt-8 text-center">
          <p class="text-sm font-medium text-gray-200">AI 面试官正在讲话...</p>
          <p class="text-[10px] text-gray-600 mt-1 italic">正在分析你的回答逻辑</p>
        </div>
      </div>

      <!-- Bottom Section: Chat/Transcript Log -->
      <div class="h-1/2 flex flex-col overflow-hidden bg-[#121212]">
        <div class="px-4 py-2 border-b border-[#333333] bg-gray-900/30 flex justify-between items-center shrink-0">
          <span class="text-[10px] font-bold uppercase text-gray-500 tracking-wider">实时对话记录</span>
          <span class="text-[10px] text-gray-600">已同步</span>
        </div>
        
        <!-- 聊天记录列表区域 -->
        <div class="flex-1 overflow-y-auto p-4 space-y-4">
          <ChatBubble 
            v-for="msg in chatHistory" 
            :key="msg.id"
            :role="msg.role"
            :content="msg.content"
            :status="msg.status"
          />
        </div>
        
        <!-- Chat Input Field -->
        <div class="p-4 border-t border-[#333333] shrink-0">
          <div class="relative">
            <input 
              type="text" 
              class="w-full bg-[#1E1E1E] border border-[#333333] rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500/50 text-gray-200" 
              placeholder="输入文字回复，或直接使用麦克风讲话..." 
            />
          </div>
        </div>
      </div>

    </section>
    <!-- END: LeftColumn -->

    <!-- BEGIN: RightColumn (IDE Panel 占65%宽度) -->
    <section class="w-[65%] bg-[#1E1E1E] flex flex-col shrink-0">
      
      <!-- Editor Header/Tabs -->
      <div class="h-9 border-b border-[#333333] flex items-center px-4 bg-[#121212] shrink-0">
        <div class="flex h-full">
          <div class="bg-[#1E1E1E] px-4 flex items-center border-t-2 border-blue-500 text-xs text-white">
            <span class="mr-2 text-orange-400 font-bold">J</span> Solution.java
          </div>
          <div class="px-4 flex items-center text-xs text-gray-600 hover:text-gray-400 cursor-pointer transition-colors">
            白板画图 (Whiteboard)
          </div>
        </div>
      </div>

      <!-- Code Area (真实编辑器组件) -->
      <div class="flex-1 relative overflow-hidden bg-[#1E1E1E]">
        <MonacoEditor v-model="code" :language="language" />
      </div>

      <!-- Editor Footer/Status -->
      <div class="h-6 border-t border-[#333333] bg-[#1a1a1a] flex items-center justify-between px-4 shrink-0">
        <div class="flex items-center space-x-4">
          <span class="text-[10px] text-gray-500 uppercase">UTF-8</span>
          <span class="text-[10px] text-gray-500 uppercase">Java 17</span>
        </div>
        <div class="flex items-center space-x-4">
          <span class="text-[10px] text-gray-500">Ln 11, Col 5</span>
          <span class="text-[10px] text-blue-400 flex items-center">
            <span class="w-1.5 h-1.5 rounded-full bg-blue-400 mr-1"></span>
            云端实时同步中
          </span>
        </div>
      </div>

    </section>
    <!-- END: RightColumn -->

  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import MonacoEditor from '@/components/business/MonacoEditor.vue'
import ChatBubble from '@/components/business/ChatBubble.vue'

// ==== 编辑器相关状态 ====
const language = ref('java')
const code = ref(`public class Solution {
  public static void main(String[] args) {
    // 请在此处编写你的代码...
    System.out.println("Hello, Interviewer");
  }

  /**
   * 解释 HashMap 的内部结构
   */
  public void analyzeHashMap() {
    
  }
}`)

// ==== 聊天对话相关状态 ====
// 模拟初次进入房间后的对话流
const chatHistory = ref([
  {
    id: 1,
    role: 'interviewer',
    content: '你好！我是今天的AI面试官。请介绍一下 Java 中 HashMap 的工作原理，特别是在 Java 8 之后有哪些重大的优化？',
    status: 'done'
  },
  {
    id: 2,
    role: 'candidate',
    content: '',
    status: 'typing' // 状态为 typing 时，将触发候选人气泡的呼吸灯动效
  }
])
</script>