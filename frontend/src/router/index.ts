import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
// 定义路由表
const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'Home',
    // 采用路由懒加载，优化首屏加载速度
    // 注意：这里的 .vue 文件将在阶段六中创建，目前保存后如果浏览器报错提示找不到文件是正常的
    component: () => import('@/views/Home/index.vue'),
    meta: {
      layout: 'default', // 标识使用带导航栏的默认布局
      title: '首页 - AI模拟面试平台'
    }
  },
  {
    path: '/interview/setup',
    name: 'InterviewSetup',
    component: () => import('@/views/Interview/Setup.vue'),
    meta: {
      layout: 'default',
      title: '面试准备'
    }
  },
  {
    path: '/interview/room',
    name: 'InterviewRoom',
    component: () => import('@/views/Interview/Room.vue'),
    meta: {
      layout: 'interview', // 标识使用无干扰的沉浸式面试布局
      title: '面试进行中'
    }
  },
  {
    path: '/report/:id', // 动态路由，根据面试记录 ID 查看对应的报告
    name: 'Report',
    component: () => import('@/views/Report/index.vue'),
    meta: {
      layout: 'default',
      title: '评估报告'
    }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile/index.vue'),
    meta: {
      layout: 'default',
      title: '个人中心'
    }
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(), // 使用 HTML5 History 模式，URL 中没有 # 号
  routes
})

// 全局前置路由守卫：用于在页面切换时动态修改浏览器的标签页标题
router.beforeEach((to, _from, next) => {
  if (to.meta.title) {
    document.title = to.meta.title as string
  }
  next()
})

export default router