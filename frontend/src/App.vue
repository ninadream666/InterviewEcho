<template>
  <router-view v-slot="{ Component, route }">
    <component :is="getLayout(route.meta.layout)">
      <transition name="fade" mode="out-in">
        <component :is="Component" :key="route.path" />
      </transition>
    </component>
  </router-view>
</template>

<script setup lang="ts">
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import InterviewLayout from '@/layouts/InterviewLayout.vue'

const getLayout = (layoutName: unknown) => {
  if (layoutName === 'interview') {
    return InterviewLayout
  }
  return DefaultLayout
}
</script>

<style>
/* 全局基础样式重置 */
html, body, #app {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  background-color: #f5f7fa; 
}

/* 隐藏部分浏览器的默认滚动条 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-thumb {
  background-color: #dcdfe6;
  border-radius: 3px;
}

/* ✨ 将路由切换的过渡动画统一放到全局 ✨ */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>