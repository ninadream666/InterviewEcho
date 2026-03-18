<template>
  <div class="flex items-center justify-center p-6 w-full h-full">
    <!-- BEGIN: SetupContainer -->
    <main class="w-full max-w-2xl bg-white rounded-2xl shadow-xl overflow-hidden" data-purpose="setup-card">
      
      <!-- BEGIN: HeaderSection -->
      <header class="p-8 border-b border-gray-100 flex items-center justify-between">
        <div class="flex items-center gap-4">
          <h1 class="text-2xl font-bold text-gray-800">面试参数配置</h1>
        </div>
        <span class="px-3 py-1 bg-[#E6F0FA] text-[#0066CC] text-sm font-medium rounded-full border border-blue-200">
          {{ currentJobName }}
        </span>
      </header>
      <!-- END: HeaderSection -->

      <div class="p-8 space-y-10">
        
        <!-- BEGIN: DifficultySelection -->
        <section data-purpose="difficulty-selector">
          <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">难度选择</h2>
          <div class="grid grid-cols-3 gap-4">
            <button 
              v-for="diff in difficulties" 
              :key="diff.value"
              @click="selectedDifficulty = diff.value"
              :class="[
                'flex flex-col items-center p-4 border-2 rounded-xl transition-colors',
                selectedDifficulty === diff.value 
                  ? 'border-[#0066CC] bg-[#E6F0FA]' 
                  : 'border-gray-100 hover:border-blue-200'
              ]"
            >
              <span :class="['text-lg font-bold', selectedDifficulty === diff.value ? 'text-[#0066CC]' : 'text-gray-700']">
                {{ diff.label }}
              </span>
              <span :class="['text-xs mt-1', selectedDifficulty === diff.value ? 'text-blue-500' : 'text-gray-400']">
                {{ diff.desc }}
              </span>
            </button>
          </div>
        </section>
        <!-- END: DifficultySelection -->

        <!-- BEGIN: AssessmentFocus -->
        <section data-purpose="focus-tags">
          <h2 class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">考察重点 (多选)</h2>
          <div class="flex flex-wrap gap-3">
            <label v-for="tag in focusOptions" :key="tag.value" class="cursor-pointer">
              <input type="checkbox" :value="tag.value" v-model="selectedFocus" class="hidden peer" />
              <span class="px-4 py-2 rounded-lg border border-gray-200 text-sm peer-checked:bg-[#0066CC] peer-checked:text-white peer-checked:border-[#0066CC] transition-all select-none">
                {{ tag.label }}
              </span>
            </label>
          </div>
        </section>
        <!-- END: AssessmentFocus -->

        <!-- BEGIN: DeviceDetection -->
        <section class="bg-gray-50 rounded-xl p-5 border border-gray-100" data-purpose="mic-test">
          <h2 class="text-sm font-semibold text-gray-600 mb-4 flex items-center gap-2">
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path>
            </svg>
            麦克风环境检测
          </h2>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <!-- Voice Wave Animation -->
              <div class="flex items-center h-8 w-12 justify-center gap-0.5" data-purpose="voice-wave">
                <span class="voice-bar"></span>
                <span class="voice-bar"></span>
                <span class="voice-bar"></span>
                <span class="voice-bar"></span>
                <span class="voice-bar"></span>
              </div>
              <div class="flex items-center text-green-600 text-sm font-medium">
                <svg class="h-5 w-5 mr-1.5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                </svg>
                收音正常
              </div>
            </div>
            <button class="text-xs text-[#0066CC] hover:underline">重新检测</button>
          </div>
        </section>
        <!-- END: DeviceDetection -->

        <!-- BEGIN: ActionButton -->
        <footer class="pt-4">
          <button 
            @click="handleStartInterview"
            class="w-full bg-[#0066CC] hover:bg-blue-700 text-white font-bold py-4 px-6 rounded-xl shadow-lg shadow-blue-200 transition-all active:scale-[0.98]"
          >
            确认配置并进入面试房间
          </button>
          <p class="text-center text-gray-400 text-xs mt-4">
            准备好后点击上方按钮，AI面试官将在房间内等待您
          </p>
        </footer>
        <!-- END: ActionButton -->
        
      </div>
    </main>
    <!-- END: SetupContainer -->
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

// 1. 获取并映射岗位名称
const jobMap: Record<string, string> = {
  java: 'Java后端开发工程师',
  frontend: 'Web前端开发工程师',
  python: 'Python算法工程师'
}
// 从路由中获取 target 参数，如果没有则默认为软件工程师
const currentJobName = computed(() => {
  const target = route.query.target as string
  return jobMap[target] || '软件工程师'
})

// 2. 难度选择状态
const selectedDifficulty = ref('middle')
const difficulties = [
  { label: '初级', value: 'junior', desc: '1-3年经验' },
  { label: '中级', value: 'middle', desc: '3-5年经验' },
  { label: '高级', value: 'senior', desc: '5年以上经验' }
]

// 3. 考察重点多选状态
const selectedFocus = ref(['core', 'concurrency']) // 默认选中前两项
const focusOptions = [
  { label: '核心基础', value: 'core' },
  { label: '并发编程', value: 'concurrency' },
  { label: '系统设计', value: 'system' },
  { label: '算法数据结构', value: 'algorithm' }
]

// 4. 进入面试房间
const handleStartInterview = () => {
  // 实际开发中，可以在这里将用户的配置（岗位、难度、考察重点）发给后端初始化一次面试
  // 然后带着面试ID跳转到房间
  router.push('/interview/room')
}
</script>

<style scoped>
/* Custom animation for voice wave bars */
@keyframes wave-grow {
  0%, 100% { height: 8px; }
  50% { height: 24px; }
}

.voice-bar {
  display: inline-block;
  width: 4px;
  background-color: #0066CC;
  border-radius: 2px;
  margin: 0 1px;
  animation: wave-grow 1.2s ease-in-out infinite;
}

.voice-bar:nth-child(2) { animation-delay: 0.1s; }
.voice-bar:nth-child(3) { animation-delay: 0.2s; }
.voice-bar:nth-child(4) { animation-delay: 0.3s; }
.voice-bar:nth-child(5) { animation-delay: 0.4s; }
</style>