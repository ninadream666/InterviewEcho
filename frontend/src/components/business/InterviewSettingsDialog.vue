<template>
  <el-dialog
    v-model="visible"
    :title="`开始 ${roleName} 面试`"
    width="500px"
    class="!rounded-[2rem] !p-8 shadow-2xl overflow-hidden"
    :show-close="false"
    destroy-on-close
  >
    <div class="space-y-8 py-4">
      <!-- Difficulty Selection -->
      <div class="animate-in fade-in slide-in-from-left duration-300">
        <label class="block text-sm font-black text-gray-400 uppercase tracking-widest mb-4">选择面试难度</label>
        <div class="flex gap-3">
          <button
            v-for="d in ['简单', '中等', '困难']"
            :key="d"
            @click="difficulty = d"
            :class="[
              'flex-1 py-4 rounded-2xl font-bold transition-all border-2 active:scale-95',
              difficulty === d 
                ? 'bg-primary border-primary text-white shadow-lg shadow-indigo-200' 
                : 'bg-white border-gray-100 text-gray-500 hover:border-indigo-200'
            ]"
          >
            {{ d }}
          </button>
        </div>
      </div>

      <!-- Rounds Selection -->
      <div class="animate-in fade-in slide-in-from-left duration-400">
        <label class="block text-sm font-black text-gray-400 uppercase tracking-widest mb-4 flex justify-between">
          面试轮次 (不含开场)
          <span class="text-primary">{{ totalRounds }} 轮</span>
        </label>
        <div class="px-2">
          <el-slider 
            v-model="totalRounds" 
            :min="2" 
            :max="10" 
            :step="1"
            :marks="{ 2: '短', 6: '中', 10: '长' }"
          />
        </div>
      </div>

      <!-- Knowledge Points Selection -->
      <div class="animate-in fade-in slide-in-from-left duration-500">
        <label class="block text-sm font-black text-gray-400 uppercase tracking-widest mb-4">重点考察领域 (多选)</label>
        <div v-if="loading" class="flex items-center justify-center py-6">
          <el-icon class="is-loading text-primary text-2xl"><Loading /></el-icon>
        </div>
        <div v-else-if="sections.length === 0" class="text-sm text-gray-400 py-2">
          该岗位暂无可选考察方向，面试官将按全流程进行。
        </div>
        <div v-else class="flex flex-wrap gap-2">
          <button
            v-for="s in sections"
            :key="s"
            @click="toggleSection(s)"
            :class="[
              'px-4 py-2 rounded-xl text-sm font-semibold transition-all border active:scale-95',
              selectedSections.includes(s)
                ? 'bg-indigo-50 border-indigo-200 text-indigo-600 shadow-sm'
                : 'bg-gray-50 border-gray-100 text-gray-400 hover:bg-gray-100'
            ]"
          >
            {{ s }}
          </button>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex gap-4 pt-4">
        <el-button @click="visible = false" class="!rounded-xl !px-6 !border-none !bg-gray-100 !text-gray-500 hover:!bg-gray-200 !font-bold">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleConfirm" 
          class="flex-1 !rounded-xl !h-12 !text-lg !font-bold !bg-primary !border-none !shadow-lg hover:!scale-[1.02] active:!scale-95 transition-all"
        >
          立即开始面试 →
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import api from '@/api'

const props = defineProps({
  roleName: String,
  roleKey: String
})

const emit = defineEmits(['confirm'])

const visible = ref(false)
const difficulty = ref('中等')
const totalRounds = ref(6)
const sections = ref([])
const selectedSections = ref([])
const loading = ref(false)

const open = async (roleKey) => {
  visible.value = true
  loading.value = true
  selectedSections.value = []
  
  // Use the passed key or the prop as fallback
  const targetKey = roleKey || props.roleKey
  if (!targetKey) {
    loading.value = false
    return
  }

  try {
    const { data } = await api.get(`/interview/roles/${targetKey}/sections`)
    sections.value = data
  } catch (err) {
    console.error('Failed to fetch sections:', err)
  } finally {
    loading.value = false
  }
}

const toggleSection = (s) => {
  const idx = selectedSections.value.indexOf(s)
  if (idx > -1) {
    selectedSections.value.splice(idx, 1)
  } else {
    selectedSections.value.push(s)
  }
}

const handleConfirm = () => {
  emit('confirm', {
    difficulty: difficulty.value,
    knowledge_points: selectedSections.value,
    total_rounds: totalRounds.value
  })
  visible.value = false
}

defineExpose({ open })
</script>

<style scoped>
:deep(.el-dialog) {
  background: white;
  margin-top: 15vh !important;
}
:deep(.el-dialog__title) {
  font-weight: 900;
  font-size: 1.5rem;
  color: #1F2937;
}
</style>
