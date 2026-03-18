<template>
  <div class="w-full pb-12" data-purpose="home-page-main-content">
    
    <!-- BEGIN: HeroSection -->
    <section class="relative py-20 px-4 overflow-hidden bg-transparent rounded-2xl mb-8" data-purpose="hero-section">
      <!-- Decorative Background Element -->
      <div class="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full opacity-5 pointer-events-none">
        <svg class="w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 100">
          <defs>
            <pattern height="10" id="grid" patternUnits="userSpaceOnUse" width="10">
              <path d="M 10 0 L 0 0 0 10" fill="none" stroke="currentColor" stroke-width="0.5"></path>
            </pattern>
          </defs>
          <rect fill="url(#grid)" height="100" width="100"></rect>
        </svg>
      </div>
      <div class="max-w-5xl mx-auto text-center relative z-10">
        <h1 class="text-5xl md:text-6xl font-extrabold text-slate-900 tracking-tight mb-6">
          AI赋能，真实模拟，<span class="text-[#0066CC]">拿下面试</span>
        </h1>
        <p class="text-xl text-slate-600 mb-10 max-w-2xl mx-auto leading-relaxed">
          InterviewEcho 为大学生提供最真实的 AI 模拟面试体验，精准分析你的每一项能力，助你斩获心仪 Offer。
        </p>
        <div class="flex justify-center gap-4">
          <!-- 点击主按钮直接滚动到下方的岗位选择区，或者跳转默认岗位 -->
          <button 
            @click="scrollToJobs"
            class="px-8 py-4 bg-[#0066CC] hover:bg-[#0052a3] text-white font-semibold rounded-lg shadow-lg shadow-blue-200 transition-all duration-300 transform hover:-translate-y-1 active:scale-95"
          >
            立即开始面试
          </button>
        </div>
        <!-- Trust Badges / Stats -->
        <div class="mt-16 flex flex-wrap justify-center gap-8 text-slate-400 grayscale opacity-70">
          <div class="flex items-center gap-2">
            <span class="text-sm font-medium tracking-widest uppercase">Real-time Feedback</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-sm font-medium tracking-widest uppercase">Expert Evaluation</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-sm font-medium tracking-widest uppercase">Career Growth</span>
          </div>
        </div>
      </div>
    </section>
    <!-- END: HeroSection -->

    <!-- BEGIN: JobSelectionSection -->
    <section id="job-selection" class="py-12 px-4 max-w-7xl mx-auto" data-purpose="job-selection-grid">
      <div class="text-center mb-16">
        <h2 class="text-3xl font-bold text-slate-800 mb-4">选择你的目标职位</h2>
        <p class="text-slate-500">针对性模拟面试，覆盖核心技术栈，助你做好万全准备</p>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        
        <!-- Card 1: Java Backend -->
        <div 
          @click="goToSetup('java')"
          class="group relative bg-white p-8 rounded-2xl border border-slate-200 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl hover:border-[#0066CC] cursor-pointer" 
        >
          <div class="w-14 h-14 bg-blue-50 text-[#0066CC] rounded-xl flex items-center justify-center mb-6 group-hover:bg-[#0066CC] group-hover:text-white transition-colors duration-300">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3V7.5a3 3 0 013-3h13.5a3 3 0 013 3v3.75a3 3 0 01-3 3m-13.5 0h13.5m-13.5 0v3.75m13.5-3.75v3.75m-13.5 0a3 3 0 003 3h13.5a3 3 0 003-3v-3.75" stroke-linecap="round" stroke-linejoin="round"></path>
            </svg>
          </div>
          <h3 class="text-xl font-bold text-slate-800 mb-3">Java后端开发工程师</h3>
          <p class="text-slate-600 leading-relaxed mb-6">
            考察 Spring Boot, JVM, MySQL, 微服务架构等。深入理解高并发与分布式系统设计。
          </p>
          <div class="flex items-center text-sm font-semibold text-[#0066CC]">
            进入模拟 <svg class="h-4 w-4 ml-1 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M9 5l7 7-7 7" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path></svg>
          </div>
        </div>

        <!-- Card 2: Web Frontend -->
        <div 
          @click="goToSetup('frontend')"
          class="group relative bg-white p-8 rounded-2xl border border-slate-200 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl hover:border-[#0066CC] cursor-pointer" 
        >
          <div class="w-14 h-14 bg-blue-50 text-[#0066CC] rounded-xl flex items-center justify-center mb-6 group-hover:bg-[#0066CC] group-hover:text-white transition-colors duration-300">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" stroke-linecap="round" stroke-linejoin="round"></path>
            </svg>
          </div>
          <h3 class="text-xl font-bold text-slate-800 mb-3">Web前端开发工程师</h3>
          <p class="text-slate-600 leading-relaxed mb-6">
            考察 React/Vue, CSS 布局, 性能优化, 浏览器原理等。侧重前端工程化与用户交互体验。
          </p>
          <div class="flex items-center text-sm font-semibold text-[#0066CC]">
            进入模拟 <svg class="h-4 w-4 ml-1 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M9 5l7 7-7 7" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path></svg>
          </div>
        </div>

        <!-- Card 3: Python AI -->
        <div 
          @click="goToSetup('python')"
          class="group relative bg-white p-8 rounded-2xl border border-slate-200 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl hover:border-[#0066CC] cursor-pointer" 
        >
          <div class="w-14 h-14 bg-blue-50 text-[#0066CC] rounded-xl flex items-center justify-center mb-6 group-hover:bg-[#0066CC] group-hover:text-white transition-colors duration-300">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M9.75 3.104v1.607a1 1 0 01-.521.87l-4.106 2.155a2 2 0 00-1.123 1.785V14.5a2 2 0 001.123 1.785l4.106 2.155a1 1 0 01.521.87v1.607c0 .59.616.999 1.15.744l9.508-4.562a2 2 0 001.122-1.785V7.712a2 2 0 00-1.122-1.785l-9.508-4.562a.847.847 0 00-1.15.74z" stroke-linecap="round" stroke-linejoin="round"></path>
            </svg>
          </div>
          <h3 class="text-xl font-bold text-slate-800 mb-3">Python算法工程师</h3>
          <p class="text-slate-600 leading-relaxed mb-6">
            考察 机器学习, 深度学习, 数据结构与算法, 模型调优等。专注数学逻辑与前沿 AI 技术。
          </p>
          <div class="flex items-center text-sm font-semibold text-[#0066CC]">
            进入模拟 <svg class="h-4 w-4 ml-1 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M9 5l7 7-7 7" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path></svg>
          </div>
        </div>

      </div>
    </section>
    <!-- END: JobSelectionSection -->
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

// 平滑滚动到岗位选择区域
const scrollToJobs = () => {
  const jobSection = document.getElementById('job-selection')
  if (jobSection) {
    jobSection.scrollIntoView({ behavior: 'smooth' })
  }
}

// 携带目标岗位参数跳转到面试配置页
const goToSetup = (jobType: string) => {
  router.push({
    path: '/interview/setup',
    query: { target: jobType }
  })
}
</script>

<style scoped>
/* 保证 SVG 兼容性 */
svg {
  display: block;
}
</style>