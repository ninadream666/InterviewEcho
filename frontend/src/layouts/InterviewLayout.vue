<template>
  <!-- 外层容器：占满屏幕、深色背景、隐藏系统默认滚动条 -->
  <div class="bg-[#121212] text-gray-300 h-screen w-screen overflow-hidden font-sans flex flex-col">
    
    <!-- BEGIN: TopBar  -->
    <header class="h-10 border-b border-[#333333] bg-[#121212] flex items-center justify-between px-2 md:px-4 z-50 shrink-0 shadow-sm gap-2">
      
      <!-- Left Section: Job Position Tag -->
      <!-- 增加 flex-1 和 min-w-0 确保超长文字可以被正确截断，而不是撑爆屏幕 -->
      <div class="flex flex-1 min-w-0 items-center space-x-1 md:space-x-3">
        <div class="flex min-w-0 items-center space-x-1.5 md:space-x-2">
          <!-- 呼吸灯动效，增加 shrink-0 防止被挤压 -->
          <span class="shrink-0 w-1.5 h-1.5 md:w-2 md:h-2 rounded-full bg-green-500 animate-pulse"></span>
          <!-- 使用 flex 截断，自适应字体 -->
          <span class="text-xs sm:text-sm font-medium tracking-wide uppercase text-gray-400 truncate">
            {{ role || 'AI模拟面试中' }}
          </span>
        </div>
      </div>
      
      <!-- Center Section: Timer -->
      <div class="flex shrink-0 items-center justify-center">
        <!-- 手机端字体调小，内边距减小 -->
        <span class="text-xs md:text-sm font-mono font-bold text-white tracking-widest bg-gray-800 px-2 md:px-3 py-0.5 rounded border border-[#333333]">
          {{ formattedTime }}
        </span>
      </div>
      
      <!-- Right Section: Actions -->
      <!-- 增加 flex-1 和 justify-end 确保中间的计时器绝对居中，同时按钮靠右对齐 -->
      <div class="flex flex-1 shrink-0 items-center justify-end">
        <!-- 手机端按钮调整自适应字号，并保证良好的触控边距 -->
        <button 
          @click="$emit('end-interview')"
          class="bg-red-600 hover:bg-red-700 text-white text-xs sm:text-sm font-bold px-3 sm:px-4 py-1.5 rounded transition-colors duration-200 uppercase tracking-tight shadow-md whitespace-nowrap"
        >
          结束面试
        </button>
      </div>

    </header>
    <!-- END: TopBar -->

    <!-- BEGIN: MainContent -->
    <main class="flex-1 w-full overflow-hidden flex flex-col">
      <!-- 渲染具体的面试房间内容 -->
      <slot />
    </main>
    <!-- END: MainContent -->
    
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  role: {
    type: String,
    default: ''
  }
})
const emit = defineEmits(['end-interview'])

// --- 倒计时核心逻辑 ---
const timeLeft = ref(45 * 60) // 45分钟转换为秒
let timer = null

const formattedTime = computed(() => {
  const m = Math.floor(timeLeft.value / 60).toString().padStart(2, '0')
  const s = (timeLeft.value % 60).toString().padStart(2, '0')
  return `${m}:${s}`
})

// 抽出停止定时器的方法，暴露给外部组件调用
const stopTimer = () => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

onMounted(() => {
  timer = setInterval(() => {
    if (timeLeft.value > 0) {
      timeLeft.value--
    } else {
      // 时间归零时，自动触发交卷
      stopTimer()
      emit('end-interview')
    }
  }, 1000)
})

onUnmounted(() => {
  stopTimer()
})

// 暴露函数，供子组件 InterviewRoomView 结束面试时直接停止时间流动
defineExpose({
  stopTimer
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.font-sans {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

:deep(::-webkit-scrollbar) {
  width: 6px;
  height: 6px;
}
:deep(::-webkit-scrollbar-track) {
  background: #121212;
}
:deep(::-webkit-scrollbar-thumb) {
  background: #333333;
  border-radius: 3px;
}
:deep(::-webkit-scrollbar-thumb:hover) {
  background: #444444;
}
</style>