<template>
  <div class="py-8 animate-in fade-in duration-700">
    <div class="flex justify-between items-end mb-10">
      <div>
        <h1 class="text-4xl font-extrabold text-gray-900 tracking-tight">亲爱的面试者,</h1>
        <p class="text-gray-500 mt-2 text-lg">准备好开始今天的挑战了吗？选择一个岗位开启 AI 模拟面试。</p>
      </div>
    </div>
    
    <!-- Role Selection -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
      <div 
        v-for="role in roles" 
        :key="role.id"
        class="group relative bg-white rounded-3xl p-1 shadow-sm hover:shadow-2xl transition-all duration-500 cursor-pointer overflow-hidden border border-gray-100"
        @click="startInterview(role.name)"
      >
        <div :class="`absolute inset-0 bg-gradient-to-br ${role.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-500 shadow-inner text-center` "></div>
        <div class="relative p-8 flex flex-col items-center text-center">
          <div :class="`w-20 h-20 rounded-2xl bg-gradient-to-br ${role.gradient} flex items-center justify-center text-4xl mb-6 shadow-lg group-hover:scale-110 transition-transform duration-500 shadow-inner text-center` ">
            {{ role.icon }}
          </div>
          <h3 class="text-2xl font-bold text-gray-800 mb-3">{{ role.name }}</h3>
          <p class="text-gray-500 leading-relaxed mb-6">{{ role.desc }}</p>
          <div class="w-full h-px bg-gray-100 mb-6"></div>
          <el-button 
            type="primary" 
            class="!rounded-xl !px-10 !py-6 !text-lg !font-bold !bg-opacity-90 hover:!bg-opacity-100 !border-none transition-all shadow-md active:scale-95"
          >
            立即开启
          </el-button>
        </div>
      </div>
    </div>

    <!-- Growth Trend -->
    <div class="bg-white p-10 rounded-[2.5rem] shadow-xl border border-gray-50 overflow-hidden relative">
      <div class="absolute top-0 right-0 w-64 h-64 bg-primary opacity-5 rounded-full -mr-32 -mt-32"></div>
      <div class="relative z-10">
        <div class="flex items-center justify-between mb-8">
          <h2 class="text-2xl font-black text-gray-800">能力成长趋势</h2>
          <div class="flex gap-2" v-if="history.length > 0">
            <span class="px-3 py-1 bg-blue-50 text-blue-600 text-xs font-bold rounded-full">综合评分</span>
          </div>
        </div>

        <div v-if="history.length === 0" class="flex flex-col items-center justify-center h-64 bg-gray-50/50 rounded-3xl border border-dashed border-gray-200">
          <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <el-icon class="text-gray-300 text-2xl"><DataLine /></el-icon>
          </div>
          <p class="text-gray-400 font-medium">完成第一次面试后，系统将为您分析多维能力曲线</p>
        </div>

        <!-- Dynamic History List -->
        <div v-else class="space-y-6">
          <div 
            v-for="(item, index) in history.slice(-5)" 
            :key="index" 
            class="relative group cursor-pointer hover:translate-x-1 transition-transform"
            @click="router.push({ name: 'Report', params: { id: item.id } })"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-bold text-gray-600 group-hover:text-primary transition-colors">{{ item.role }}</span>
              <span class="text-sm font-black text-primary">{{ item.total_score.toFixed(1) }} <small class="font-normal opacity-60">分</small></span>
            </div>
            <div class="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
              <div 
                class="h-full bg-gradient-to-r from-primary to-indigo-400 rounded-full transition-all duration-1000 ease-out"
                :style="{ width: `${item.total_score}%` }"
              ></div>
            </div>
            <div class="mt-1 text-[10px] text-gray-400 font-medium uppercase tracking-tighter">
              {{ new Date(item.created_at).toLocaleDateString() }} · <span class="text-primary opacity-0 group-hover:opacity-100 transition-opacity">点击查看详情 →</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { DataLine } from '@element-plus/icons-vue'
import api from '@/api'

const router = useRouter()
const history = ref([])
const roles = ref([])

onMounted(async () => {
  try {
    const [historyRes, rolesRes] = await Promise.all([
      api.get('/interview/history'),
      api.get('/interview/roles')
    ])
    history.value = historyRes.data
    roles.value = rolesRes.data
  } catch (err) {
    console.error('Failed to fetch data:', err)
  }
})

const startInterview = (roleName) => {
  router.push(`/interview/${encodeURIComponent(roleName)}`)
}
</script>
