<template>
  <div class="space-y-4">
    <div v-for="(dim, index) in dimensionDetails" :key="index" class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex flex-col md:flex-row items-start md:items-center gap-6 hover:border-[#0066CC]/30 transition-colors">
      
      <!-- 维度名称与权重 -->
      <div class="w-full md:w-1/5 shrink-0">
        <h4 class="text-base font-bold text-gray-800">{{ dim.name }}</h4>
        <div class="text-xs text-gray-400 mt-1.5">
          评估权重：<span class="font-semibold text-gray-600">{{ dim.weight }}</span>
        </div>
      </div>
      
      <!-- 分数与进度条 -->
      <div class="w-full md:w-1/4 shrink-0 flex flex-col justify-center">
         <div class="flex items-end gap-1 mb-1.5">
            <span class="text-2xl font-extrabold" :class="getScoreColor(dim.score)">{{ Number(dim.score).toFixed(1) }}</span>
            <span class="text-xs text-gray-400 mb-1">/ 100</span>
         </div>
         <div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div class="h-full rounded-full transition-all duration-700" :class="getScoreBgColor(dim.score)" :style="{ width: `${dim.score}%` }"></div>
         </div>
      </div>
      
      <!-- 评分依据 (一句话评价) -->
      <div class="w-full md:flex-1 mt-2 md:mt-0">
         <div class="bg-gray-50 rounded-lg p-3 text-sm text-gray-600 leading-relaxed border border-gray-100">
           <span class="font-semibold text-gray-700 mr-1">评分依据：</span>{{ dim.reason }}
         </div>
      </div>
      
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  report: {
    type: Object,
    required: true
  }
})

// 根据分数决定颜色样式
const getScoreColor = (score) => {
  if (score >= 85) return 'text-green-600'
  if (score >= 60) return 'text-[#0066CC]'
  return 'text-orange-500'
}

const getScoreBgColor = (score) => {
  if (score >= 85) return 'bg-green-500'
  if (score >= 60) return 'bg-[#0066CC]'
  return 'bg-orange-500'
}

// 计算并组装 5 个维度的明细数据
const dimensionDetails = computed(() => {
  if (!props.report) return []

  // 尝试从 report_json 中解析后端可能下发的自定义维度说明
  let customDetails = []
  if (props.report.report_json) {
    try {
      const parsed = typeof props.report.report_json === 'string' 
        ? JSON.parse(props.report.report_json) 
        : props.report.report_json
      customDetails = parsed.dimension_details || []
    } catch (e) {
      console.warn('Failed to parse report_json for dimension details', e)
    }
  }

  // 如果后端传了明细，直接使用
  if (customDetails.length > 0) {
    return customDetails
  }

  // 否则，基于顶层分数做通用映射兜底（包含权重和标准依据）
  const contentScore = props.report.content_score || 0
  const solvingScore = props.report.problem_solving_score || 0
  const logicScore = (contentScore + solvingScore) / 2 // 逻辑严谨性采用综合估算
  
  return [
    { 
      name: '技术正确性', 
      score: contentScore, 
      weight: '30%', 
      reason: '考察候选人对核心技术概念的掌握程度以及回答是否准确无误。' 
    },
    { 
      name: '知识深度', 
      score: solvingScore, 
      weight: '25%', 
      reason: '考察候选人对底层原理、源码结构及复杂场景的理解与探究深度。' 
    },
    { 
      name: '岗位匹配度', 
      score: props.report.business_scenario_score || 0, 
      weight: '20%', 
      reason: '考察候选人的项目经验与解决问题的思路是否高度契合目标岗位需求。' 
    },
    { 
      name: '逻辑严谨性', 
      score: logicScore, 
      weight: '15%', 
      reason: '考察候选人在分析问题时的结构化思维、边界条件考虑及推理过程。' 
    },
    { 
      name: '表达清晰度', 
      score: props.report.expression_score || 0, 
      weight: '10%', 
      reason: '基于声学特征提取，考察沟通流畅度、语速节奏控制及专业表达自信感。' 
    }
  ]
})
</script>