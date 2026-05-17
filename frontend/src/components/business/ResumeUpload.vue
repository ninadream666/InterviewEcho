<template>
  <div class="w-full">
    <label v-if="!hideTitle" class="block text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-1 sm:gap-0">
      <span>简历上传 (可选)</span>
      <span class="text-xs text-gray-400 normal-case tracking-normal">AI 将根据你的真实经历定制面试问题</span>
    </label>

    <!-- 未解析时：上传入口 -->
    <div v-if="!resumePersona">
      <!-- 模式切换 -->
      <div class="flex gap-2 mb-3">
        <button
          @click="resumeMode = 'pdf'"
          :class="[
            'px-3 py-1.5 text-xs rounded-lg border transition-colors',
            resumeMode === 'pdf'
              ? 'bg-[#0066CC] text-white border-[#0066CC]'
              : 'bg-white text-gray-600 border-gray-200 hover:border-[#0066CC]'
          ]"
        >
          上传 PDF
        </button>
        <button
          @click="resumeMode = 'text'"
          :class="[
            'px-3 py-1.5 text-xs rounded-lg border transition-colors',
            resumeMode === 'text'
              ? 'bg-[#0066CC] text-white border-[#0066CC]'
              : 'bg-white text-gray-600 border-gray-200 hover:border-[#0066CC]'
          ]"
        >
          粘贴文本
        </button>
      </div>

      <!-- PDF 模式 -->
      <div v-if="resumeMode === 'pdf'" class="mb-3">
        <label
          class="flex items-center gap-3 px-3 py-3 text-sm border border-dashed border-gray-200 rounded-lg cursor-pointer hover:border-[#0066CC] transition-colors"
        >
          <input
            type="file"
            accept=".pdf"
            class="hidden"
            @change="handleResumeFileChange"
          />
          <svg class="w-5 h-5 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
          <span :class="resumeFile ? 'text-gray-700' : 'text-gray-400'">
            {{ resumeFile ? resumeFile.name : '点击选择 PDF 简历文件' }}
          </span>
        </label>
      </div>

      <!-- 文本模式 -->
      <div v-else class="mb-3">
        <el-input
          v-model="resumeText"
          type="textarea"
          :rows="5"
          placeholder="在此粘贴简历文本内容（纯文本或 Markdown）"
          class="resume-textarea"
        />
      </div>

      <!-- 解析按钮 -->
      <button
        @click="parseResume"
        :disabled="resumeParsing || (!resumeFile && !resumeText.trim())"
        class="w-full py-2 text-sm rounded-lg border border-[#0066CC] text-[#0066CC] hover:bg-[#E6F0FA] transition-colors disabled:border-gray-200 disabled:text-gray-400 disabled:hover:bg-white"
      >
        <span v-if="resumeParsing" class="inline-flex items-center gap-2">
          <el-icon class="is-loading"><Loading /></el-icon>
          解析中...
        </span>
        <span v-else>开始解析</span>
      </button>
    </div>

    <!-- 已解析时：展示结果 -->
    <div v-else>
      <div class="bg-[#E6F0FA]/40 border border-[#0066CC]/20 rounded-lg px-4 py-3 space-y-3">
        <!-- 总体画像 -->
        <p class="text-sm text-gray-700 leading-relaxed">
          <span class="font-semibold text-[#0066CC]">画像：</span>
          {{ resumePersona.summary || '（未提取到）' }}
        </p>

        <!-- 基本信息行 -->
        <div class="flex gap-4 text-xs text-gray-600">
          <span v-if="resumePersona.education">
            <span class="text-gray-400">学历：</span>{{ resumePersona.education }}
          </span>
          <span>
            <span class="text-gray-400">经验：</span>{{ resumePersona.work_years != null ? resumePersona.work_years + ' 年' : '未知' }}
          </span>
        </div>

        <!-- 技能标签 -->
        <div v-if="resumePersona.skills && resumePersona.skills.length > 0">
          <div class="text-xs text-gray-400 mb-1.5">技能栈</div>
          <div class="flex flex-wrap gap-1.5">
            <el-tag
              v-for="skill in resumePersona.skills"
              :key="skill"
              size="small"
              class="!bg-white !border-[#0066CC]/30 !text-[#0066CC] !text-xs"
            >
              {{ skill }}
            </el-tag>
          </div>
        </div>

        <!-- 项目列表 -->
        <div v-if="resumePersona.projects && resumePersona.projects.length > 0">
          <div class="text-xs text-gray-400 mb-1.5">主要项目</div>
          <div class="space-y-1.5">
            <div
              v-for="(proj, i) in resumePersona.projects"
              :key="i"
              class="bg-white rounded-lg px-3 py-2 text-xs border border-[#0066CC]/10"
            >
              <div class="flex items-center gap-2 mb-0.5">
                <span class="font-semibold text-gray-800">{{ proj.name || '未命名项目' }}</span>
                <span v-if="proj.role" class="text-gray-400">· {{ proj.role }}</span>
              </div>
              <div v-if="proj.tech && proj.tech.length" class="text-gray-500 mb-0.5">
                {{ proj.tech.join(' / ') }}
              </div>
              <div v-if="proj.highlights" class="text-gray-600">{{ proj.highlights }}</div>
            </div>
          </div>
        </div>

        <!-- 重新上传 / 移除 -->
        <button
          @click="clearResume"
          class="w-full py-1.5 text-xs text-gray-500 border border-dashed border-gray-200 rounded-lg hover:border-red-300 hover:text-red-500 transition-colors"
        >
          移除，重新上传
        </button>
      </div>
    </div>

    <!-- 解析警告 -->
    <div
      v-if="resumeWarning"
      class="mt-2 px-3 py-2 bg-yellow-50 border border-yellow-200 rounded-lg text-xs text-yellow-700"
    >
      {{ resumeWarning }}
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { resumeApi } from '@/api'

const props = defineProps({
  modelValue: {
    type: Object,
    default: null
  },
  hideTitle: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const resumeMode = ref('pdf')
const resumeFile = ref(null)
const resumeText = ref('')
const resumeParsing = ref(false)
const resumePersona = ref(null)
const resumeWarning = ref('')

// 同步外部传入的数据
watch(() => props.modelValue, (newVal) => {
  resumePersona.value = newVal
}, { immediate: true })

const handleResumeFileChange = (e) => {
  const file = e.target?.files?.[0]
  if (file) {
    resumeFile.value = file
    resumeWarning.value = ''
  }
}

const parseResume = async () => {
  resumeParsing.value = true
  resumeWarning.value = ''
  try {
    const formData = new FormData()
    if (resumeMode.value === 'pdf' && resumeFile.value) {
      formData.append('file', resumeFile.value)
    } else if (resumeMode.value === 'text' && resumeText.value.trim()) {
      formData.append('text', resumeText.value.trim())
    } else {
      resumeWarning.value = '请先选择 PDF 文件或粘贴简历文本'
      return
    }
    
    const { data } = await resumeApi.parse(formData)
    
    resumePersona.value = data.persona
    resumeWarning.value = data.warning || ''
    emit('update:modelValue', data.persona)
  } catch (err) {
    resumeWarning.value = err.response?.data?.detail || err.message || '简历解析请求失败'
  } finally {
    resumeParsing.value = false
  }
}

const clearResume = () => {
  resumePersona.value = null
  resumeFile.value = null
  resumeText.value = ''
  resumeWarning.value = ''
  emit('update:modelValue', null)
}
</script>

<style scoped>
.resume-textarea :deep(.el-textarea__inner) {
  font-size: 13px;
  line-height: 1.6;
}
</style>