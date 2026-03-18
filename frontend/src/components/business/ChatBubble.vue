<template>
  <div :class="['flex w-full space-y-1', isInterviewer ? 'flex-col items-start' : 'flex-col items-end']">
    <!-- 角色名称 -->
    <div :class="['text-[10px] font-bold', isInterviewer ? 'text-blue-400' : 'text-gray-500 uppercase']">
      {{ isInterviewer ? '面试官' : '候选人 (你)' }}
    </div>

    <!-- 气泡内容区 -->
    <div v-if="status === 'typing'" :class="[bubbleClasses, 'italic']">
      <span class="animate-pulse">{{ isInterviewer ? '正在分析并生成追问...' : '正在输入或语音收音中...' }}</span>
    </div>
    <div v-else :class="bubbleClasses">
      <!-- 实际项目中如果后端返回的是 Markdown，这里可以使用 v-html 结合 marked 库进行渲染 -->
      {{ content }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  // 角色类型：'interviewer' (面试官) | 'candidate' (候选人)
  role: {
    type: String,
    required: true
  },
  // 聊天文本内容
  content: {
    type: String,
    default: ''
  },
  // 状态：'done' (已完成) | 'typing' (正在输入/录音中)
  status: {
    type: String,
    default: 'done'
  }
})

// 判断当前是否是面试官发出的消息
const isInterviewer = computed(() => props.role === 'interviewer')

// 动态计算气泡的 Tailwind 样式类
const bubbleClasses = computed(() => {
  const baseClasses = 'text-sm leading-relaxed p-3 inline-block border max-w-[90%] break-words'
  
  if (isInterviewer.value) {
    // 面试官气泡样式 (深灰)
    return `${baseClasses} text-gray-300 bg-[#1E1E1E] rounded-r-lg rounded-bl-lg border-[#333333]`
  } else {
    // 候选人气泡样式 (幽灵蓝)
    return `${baseClasses} text-gray-400 bg-blue-900/20 rounded-l-lg rounded-br-lg border-blue-800/30`
  }
})
</script>

<style scoped>
/* 可在此处覆盖特定的 markdown 样式（如果有需要的话） */
</style>