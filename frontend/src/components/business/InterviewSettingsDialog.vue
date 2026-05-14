<template>
  <el-dialog
    v-model="visible"
    :title="`开始 ${roleName} 面试`"
    width="550px"
    class="custom-clean-dialog"
    :show-close="false"
    destroy-on-close
  >
    <div class="space-y-8 py-2">
      <!-- Difficulty Selection -->
      <div>
        <label class="block text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">选择面试难度</label>
        <div class="grid grid-cols-3 gap-4">
          <button
            v-for="d in ['简单', '中等', '困难']"
            :key="d"
            @click="difficulty = d"
            :class="[
              'py-3 rounded-lg font-bold transition-colors border',
              difficulty === d
                ? 'bg-[#E6F0FA] border-[#0066CC] text-[#0066CC]'
                : 'bg-white border-gray-200 text-gray-600 hover:border-[#0066CC]'
            ]"
          >
            {{ d }}
          </button>
        </div>
      </div>

      <!-- Rounds Selection -->
      <div>
        <label class="block text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2 flex justify-between">
          正式提问轮次 (不含开场/简历/项目深挖)
          <span class="text-[#0066CC]">{{ totalRounds }} 轮</span>
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
      <div>
        <label class="block text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">重点考察领域 (多选)</label>
        <div v-if="loading" class="flex items-center justify-center py-6">
          <el-icon class="is-loading text-[#0066CC] text-2xl"><Loading /></el-icon>
        </div>
        <div v-else-if="sections.length === 0" class="text-sm text-gray-400 py-2">
          该岗位暂无可选考察方向，面试官将按全流程进行。
        </div>
        <div v-else class="flex flex-wrap gap-3">
          <label
            v-for="s in sections"
            :key="s"
            class="cursor-pointer"
            @click="toggleSection(s)"
          >
            <span
              :class="[
                'px-4 py-2 rounded-lg border text-sm transition-all select-none block',
                selectedSections.includes(s)
                  ? 'bg-[#0066CC] text-white border-[#0066CC]'
                  : 'bg-white border-gray-200 text-gray-700 hover:border-[#0066CC]'
              ]"
            >
              {{ s }}
            </span>
          </label>
        </div>
      </div>

      <!-- GitHub Repo Deep Dive (v3) -->
      <div>
        <label class="block text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2 flex justify-between items-center">
          <span>项目深挖 GitHub 仓库 (可选)</span>
          <span class="text-xs text-gray-400 normal-case tracking-normal">AI 将针对你的真实项目定制提问</span>
        </label>

        <div class="space-y-2">
          <div
            v-for="(repo, idx) in repoSlots"
            :key="idx"
            class="flex items-center gap-2"
          >
            <input
              v-model="repoSlots[idx].url"
              type="text"
              placeholder="https://github.com/username/repo"
              class="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-[#0066CC] transition-colors disabled:bg-gray-50"
              :disabled="repoSlots[idx].analyzing || !!repoSlots[idx].summary"
            />
            <button
              v-if="!repoSlots[idx].summary"
              @click="analyzeRepoSlot(idx)"
              :disabled="!repoSlots[idx].url || repoSlots[idx].analyzing"
              class="px-3 py-2 text-sm rounded-lg border border-[#0066CC] text-[#0066CC] hover:bg-[#E6F0FA] transition-colors disabled:border-gray-200 disabled:text-gray-400 disabled:hover:bg-white whitespace-nowrap"
            >
              <span v-if="repoSlots[idx].analyzing">分析中...</span>
              <span v-else>分析</span>
            </button>
            <button
              v-else
              @click="clearRepoSlot(idx)"
              class="px-3 py-2 text-sm rounded-lg border border-gray-200 text-gray-500 hover:border-red-300 hover:text-red-500 transition-colors whitespace-nowrap"
            >
              移除
            </button>
          </div>

          <!-- 摘要预览卡片 -->
          <div
            v-for="(repo, idx) in repoSlots"
            :key="'s-' + idx"
            v-show="repo.summary"
            class="bg-[#E6F0FA]/40 border border-[#0066CC]/20 rounded-lg px-3 py-2 text-xs text-gray-700"
          >
            <div class="font-semibold text-[#0066CC] mb-0.5">
              ✓ {{ repo.summary?.full_name }}
              <span class="text-gray-500 font-normal">· {{ repo.summary?.main_language }} · ⭐ {{ repo.summary?.stars }}</span>
            </div>
            <div class="text-gray-600 line-clamp-2">{{ repo.summary?.description || '（无描述）' }}</div>
          </div>

          <!-- 错误提示 -->
          <div
            v-for="(repo, idx) in repoSlots"
            :key="'e-' + idx"
            v-show="repo.error"
            class="text-xs text-red-500"
          >
            {{ repo.error }}
          </div>

          <button
            v-if="repoSlots.length < 3"
            @click="addRepoSlot"
            class="w-full py-2 text-xs text-gray-500 border border-dashed border-gray-200 rounded-lg hover:border-[#0066CC] hover:text-[#0066CC] transition-colors"
          >
            + 添加仓库 ({{ repoSlots.length }}/3)
          </button>
        </div>
      </div>

      <!-- 简历上传 (v4) -->
      <div>
        <label class="block text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2 flex justify-between items-center">
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
    </div>

    <template #footer>
      <div class="flex gap-4 pt-2">
        <el-button @click="visible = false" class="!px-6 !border-gray-200 !text-gray-600 hover:!bg-gray-50">取消</el-button>
        <button 
          @click="handleConfirm" 
          class="flex-1 bg-[#0066CC] hover:bg-blue-700 text-white font-bold py-2.5 px-4 rounded transition-colors active:scale-[0.98]"
        >
          确认配置并进入房间
        </button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
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

// v3: GitHub 项目深挖（最多 3 个）
const repoSlots = ref([
  { url: '', analyzing: false, summary: null, error: '' }
])

// v4: 简历上传与解析
const resumeMode = ref('pdf')
const resumeFile = ref(null)
const resumeText = ref('')
const resumeParsing = ref(false)
const resumePersona = ref(null)
const resumeWarning = ref('')

const open = async (roleKey) => {
  visible.value = true
  loading.value = true
  selectedSections.value = []
  // 每次打开都重置 repo 输入和 resume 状态
  repoSlots.value = [{ url: '', analyzing: false, summary: null, error: '' }]
  resumeMode.value = 'pdf'
  resumeFile.value = null
  resumeText.value = ''
  resumeParsing.value = false
  resumePersona.value = null
  resumeWarning.value = ''

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

const addRepoSlot = () => {
  if (repoSlots.value.length < 3) {
    repoSlots.value.push({ url: '', analyzing: false, summary: null, error: '' })
  }
}

const clearRepoSlot = (idx) => {
  repoSlots.value[idx] = { url: '', analyzing: false, summary: null, error: '' }
}

const analyzeRepoSlot = async (idx) => {
  const slot = repoSlots.value[idx]
  if (!slot.url) return
  slot.analyzing = true
  slot.error = ''
  slot.summary = null
  try {
    const { data } = await api.post('/interview/repo/analyze', { url: slot.url }, { timeout: 15000 })
    slot.summary = data
  } catch (err) {
    slot.error = err.response?.data?.detail || err.message || '分析失败'
  } finally {
    slot.analyzing = false
  }
}

// v4: 简历解析
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
    const { data } = await api.post('/interview/resume/parse', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000
    })
    resumePersona.value = data.persona
    resumeWarning.value = data.warning || ''
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
}

const handleConfirm = () => {
  // 收集所有非空 URL（不要求必须先点"分析"，后端会再次抓取兜底）
  // 但如果分析过且失败了，就跳过这条，避免明知失败还提交
  const repo_urls = repoSlots.value
    .filter(s => s.url && s.url.trim() && !s.error)
    .map(s => s.url.trim())

  emit('confirm', {
    difficulty: difficulty.value,
    knowledge_points: selectedSections.value,
    total_rounds: totalRounds.value,
    repo_urls,
    resume_persona: resumePersona.value
  })
  visible.value = false
}

defineExpose({ open })
</script>

<style>
.custom-clean-dialog {
  border-radius: 12px !important;
}

.custom-clean-dialog .el-dialog__header {
  border-bottom: 1px solid #F3F4F6;
  margin-right: 0;
  padding-bottom: 16px;
}

.custom-clean-dialog .el-dialog__title {
  font-weight: bold;
  color: #1F2937;
  font-size: 1.25rem;
}

.resume-textarea .el-textarea__inner {
  font-size: 13px;
  line-height: 1.6;
}
</style>