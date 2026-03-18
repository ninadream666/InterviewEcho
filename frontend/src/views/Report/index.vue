<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 min-h-[600px] w-full p-8 md:p-12">
    <!-- 头部信息 -->
    <div class="mb-8 border-b border-gray-200 pb-6">
      <h1 class="text-3xl font-extrabold text-gray-900 tracking-tight">面试评估报告</h1>
      <p class="text-gray-500 mt-2">岗位：Java后端开发工程师 | 面试时间：2026-05-20 | 候选人：张三</p>
    </div>

    <!-- 主体区域：左右分栏 -->
    <div class="flex flex-col md:flex-row gap-10">
      
      <!-- 左侧：雷达图能力可视化 -->
      <div class="w-full md:w-5/12 flex flex-col items-center">
        <h3 class="text-lg font-bold text-gray-800 mb-4 self-start">多维度能力图谱</h3>
        <div class="w-full h-[350px] bg-gray-50 rounded-lg p-4 border border-gray-100 flex items-center justify-center">
          <RadarChart :data="mockData" :indicators="mockIndicators" />
        </div>
      </div>

      <!-- 右侧：文字评价与建议 -->
      <div class="w-full md:w-7/12 space-y-6">
        
        <!-- 核心优势 -->
        <div>
          <h3 class="text-lg font-bold text-gray-800 mb-3 flex items-center">
            <span class="w-1.5 h-5 bg-green-500 rounded-full mr-2"></span>
            核心优势 (Highlights)
          </h3>
          <p class="text-gray-600 text-sm leading-relaxed bg-green-50/50 p-4 rounded-lg border border-green-100">
            候选人对 Java 基础知识掌握扎实，特别是对 HashMap 的底层数据结构（数组+链表+红黑树）及扩容机制解释得非常清晰，能够准确指出 Java 8 中引入红黑树解决哈希冲突的性能优势。逻辑严谨性表现优秀。
          </p>
        </div>

        <!-- 改进建议 -->
        <div>
          <h3 class="text-lg font-bold text-gray-800 mb-3 flex items-center">
            <span class="w-1.5 h-5 bg-orange-500 rounded-full mr-2"></span>
            待提升项 (Improvements)
          </h3>
          <p class="text-gray-600 text-sm leading-relaxed bg-orange-50/50 p-4 rounded-lg border border-orange-100">
            在回答并发场景下的 HashMap (ConcurrentHashMap) 相关问题时，知识深度稍显不足。在后续追问中，对于 CAS 算法的底层原理以及 synchronized 锁升级的过程表述较为模糊。
          </p>
        </div>

        <!-- 推荐学习路径 -->
        <div>
          <h3 class="text-lg font-bold text-gray-800 mb-3 flex items-center">
            <span class="w-1.5 h-5 bg-[#0066CC] rounded-full mr-2"></span>
            个性化提升计划
          </h3>
          <div class="bg-blue-50/50 p-4 rounded-lg border border-blue-100">
            <ul class="list-disc list-inside text-gray-600 text-sm space-y-2 ml-1">
              <li>建议复习：<a href="#" class="text-[#0066CC] hover:underline font-medium">深入理解 Java 内存模型 (JMM) 与 Volatile 关键字</a></li>
              <li>实战练习：<a href="#" class="text-[#0066CC] hover:underline font-medium">JUC 并发编程核心面试题库训练</a></li>
              <li>进阶阅读：<a href="#" class="text-[#0066CC] hover:underline font-medium">Java 并发容器的演进历史</a></li>
            </ul>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import RadarChart from '@/components/business/RadarChart.vue'

// ==== 模拟后端返回的雷达图配置数据 ====
const mockIndicators = ref([
  { name: '技术正确性', max: 100 },
  { name: '知识深度', max: 100 },
  { name: '逻辑严谨性', max: 100 },
  { name: '岗位匹配度', max: 100 },
  { name: '沟通表达', max: 100 }
])

const mockData = ref([
  {
    value: [92, 75, 88, 85, 90], // 各维度的具体得分
    name: '本次评估得分'
  }
])
</script>