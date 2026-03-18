<template>
  <!-- 编辑器挂载容器，需确保父级有明确的宽高 -->
  <div ref="editorContainer" class="w-full h-full"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import loader from '@monaco-editor/loader'
import type * as monaco from 'monaco-editor'

// 定义组件接收的属性 (Props)
const props = defineProps({
  // v-model 绑定的代码内容
  modelValue: {
    type: String,
    default: ''
  },
  // 编程语言
  language: {
    type: String,
    default: 'java'
  },
  // 主题，默认深色以匹配我们的沉浸式界面
  theme: {
    type: String,
    default: 'vs-dark'
  }
})

// 定义组件触发的事件 (Emits)
const emit = defineEmits(['update:modelValue'])

const editorContainer = ref<HTMLElement | null>(null)
let editorInstance: monaco.editor.IStandaloneCodeEditor | null = null
let monacoInstance: typeof monaco | null = null

onMounted(async () => {
  // 配置 CDN 路径，避免 Vite 本地打包 Worker 的各种问题 (对应你设定的 0.47.x 版本)
  loader.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.47.0/min/vs' } })
  
  try {
    monacoInstance = await loader.init()
    
    if (editorContainer.value && monacoInstance) {
      // 创建编辑器实例
      editorInstance = monacoInstance.editor.create(editorContainer.value, {
        value: props.modelValue,
        language: props.language,
        theme: props.theme,
        automaticLayout: true, // 极其重要：自动适应父容器大小变化
        minimap: { enabled: false }, // 关闭右侧代码小地图，保持界面清爽
        fontSize: 14,
        fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
        scrollBeyondLastLine: false, // 到底后不留大量空白
        roundedSelection: false,
        padding: { top: 16 }
      })

      // 监听编辑器内容变化，实现 v-model 双向绑定
      editorInstance.onDidChangeModelContent(() => {
        const value = editorInstance?.getValue() || ''
        if (value !== props.modelValue) {
          emit('update:modelValue', value)
        }
      })
    }
  } catch (error) {
    console.error('Monaco Editor 初始化失败:', error)
  }
})

// 监听外部传递的 modelValue 变化，同步到编辑器中 (例如后端发来了初始代码)
watch(() => props.modelValue, (newVal) => {
  if (editorInstance && newVal !== editorInstance.getValue()) {
    editorInstance.setValue(newVal)
  }
})

// 监听外部语言变化，动态切换语法高亮 (例如从 Java 切换到 Python)
watch(() => props.language, (newLang) => {
  if (editorInstance && monacoInstance) {
    const model = editorInstance.getModel()
    if (model) {
      monacoInstance.editor.setModelLanguage(model, newLang)
    }
  }
})

// 组件销毁前释放编辑器实例，防止内存泄漏
onBeforeUnmount(() => {
  if (editorInstance) {
    editorInstance.dispose()
  }
})
</script>

<style scoped>
/* 确保加载过程中的占位样式 */
div {
  min-height: 200px;
}
</style>