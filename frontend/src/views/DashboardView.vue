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
        @click="startInterview(role)"
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
            <span class="px-3 py-1 bg-blue-50 text-blue-600 text-xs font-bold rounded-full">综合评分曲线</span>
          </div>
        </div>

        <div v-if="history.length === 0" class="flex flex-col items-center justify-center h-64 bg-gray-50/50 rounded-3xl border border-dashed border-gray-200">
          <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <el-icon class="text-gray-300 text-2xl"><DataLine /></el-icon>
          </div>
          <p class="text-gray-400 font-medium">完成第一次面试后，系统将为您分析多维能力曲线</p>
        </div>

        <div v-else class="space-y-10">
          <!-- ECharts Line Chart -->
          <LineChart :history="history" />

          <!-- Dynamic History List (Recent 3) -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4 border-t border-gray-50">
            <div 
              v-for="(item, index) in history.slice(0, 3)" 
              :key="index" 
              class="bg-gray-50/50 p-6 rounded-3xl border border-gray-100 group cursor-pointer hover:bg-white hover:shadow-xl transition-all duration-500"
              @click="router.push({ name: 'Report', params: { id: item.id } })"
            >
              <div class="flex justify-between items-start mb-4">
                <span class="text-xs font-black text-gray-400 uppercase tracking-widest">{{ new Date(item.created_at).toLocaleDateString() }}</span>
                <span class="text-xl font-black text-primary">{{ item.total_score.toFixed(1) }}</span>
              </div>
              <h4 class="font-bold text-gray-800 mb-1 group-hover:text-primary transition-colors">{{ item.role }}</h4>
              <p class="text-[10px] text-gray-400 font-medium uppercase tracking-tighter">点击查看详情 →</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Interview Settings Dialog -->
    <InterviewSettingsDialog 
      ref="settingsDialogRef" 
      :role-name="selectedRole?.name" 
      :role-key="selectedRole?.key"
      @confirm="onSettingsConfirm"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { DataLine } from '@element-plus/icons-vue'
import api from '@/api'
import LineChart from '@/components/analytics/LineChart.vue'
import InterviewSettingsDialog from '@/components/business/InterviewSettingsDialog.vue'

const router = useRouter()
const history = ref([])
const roles = ref([])
const settingsDialogRef = ref(null)
const selectedRole = ref(null)

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

const startInterview = (role) => {
  selectedRole.value = role
  settingsDialogRef.value.open(role.key)
}

const onSettingsConfirm = async (settings) => {
  try {
    const { data } = await api.post('/interview/start', {
      role: selectedRole.value.name,
      ...settings
    })
    router.push({ 
      name: 'InterviewRoom', 
      params: { role: selectedRole.value.name },
      query: { interviewId: data.id }
    })
  } catch (err) {
    console.error('Failed to start interview:', err)
  }
}
</script>
