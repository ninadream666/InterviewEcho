<template>
  <!-- 外层容器：占满屏幕、深色背景、隐藏系统默认滚动条 -->
  <div class="bg-[#121212] text-gray-300 h-screen w-screen overflow-hidden font-sans flex flex-col">
    
    <!-- BEGIN: TopBar (沉浸式顶部状态条) -->
    <header class="h-10 border-b border-[#333333] bg-[#121212] flex items-center justify-between px-4 z-50 shrink-0">
      
      <!-- Left Section: Job Position Tag -->
      <div class="flex items-center space-x-3">
        <div class="flex items-center space-x-2">
          <!-- 呼吸灯动效，暗示面试正在进行中 -->
          <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
          <span class="text-xs font-medium tracking-wide uppercase text-gray-400">Java后端开发工程师</span>
        </div>
      </div>
      
      <!-- Center Section: Timer -->
      <div class="flex items-center justify-center">
        <span class="text-sm font-mono font-bold text-white tracking-widest bg-gray-800 px-3 py-0.5 rounded border border-[#333333]">
          45:00
        </span>
      </div>
      
      <!-- Right Section: Actions -->
      <div class="flex items-center">
        <button 
          @click="handleEndInterview"
          class="bg-red-600 hover:bg-red-700 text-white text-xs font-bold px-4 py-1 rounded transition-colors duration-200 uppercase tracking-tight"
        >
          结束面试
        </button>
      </div>

    </header>
    <!-- END: TopBar -->

    <!-- BEGIN: MainContent (路由出口) -->
    <main class="flex-1 w-full overflow-hidden flex">
      <!-- 渲染具体的面试房间内容 -->
      <slot />
    </main>
    <!-- END: MainContent -->
    
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

// 结束面试的处理逻辑
const handleEndInterview = () => {
  // 实际开发中这里应该弹出一个 ElMessageBox 确认框
  // 确认后调用后端接口结束面试，然后跳转到报告页
  router.push('/profile') // 临时跳转到个人中心
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.font-sans {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

/* 针对深色模式的自定义滚动条 */
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