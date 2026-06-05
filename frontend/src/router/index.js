/**
 * 模块名称：Vue Router 路由配置（router/index）
 * 功能描述：定义应用的全部前端路由及导航守卫。
 *
 * 路由表：
 * - /：首页
 * - /login：登录/注册
 * - /dashboard：面试仪表盘（需登录）
 * - /interview/:role：面试房间（需登录）
 * - /report/:id：面试报告（需登录）
 * - /profile：个人资料与历史（需登录）
 * - /code：代码题库列表（需登录）
 * - /code/problems/:problemId：代码题目详情（需登录）
 *
 * 导航守卫：未登录时自动跳转到 /login。
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

import HomeView from '@/features/shared/views/HomeView.vue'
import LoginView from '@/features/auth/views/LoginView.vue'
import DashboardView from '@/features/interview/views/DashboardView.vue'
import InterviewRoomView from '@/features/interview/views/InterviewRoomView.vue'
import ReportView from '@/features/report/views/ReportView.vue'
import ProfileView from '@/features/report/views/ProfileView.vue'
import CodePracticeView from '@/features/code-practice/views/CodePracticeView.vue'
import CodeProblemView from '@/features/code-practice/views/CodeProblemView.vue'

const routes = [
  { 
    path: '/', 
    name: 'Home', 
    component: HomeView 
  },
  { 
    path: '/login', 
    name: 'Login', 
    component: LoginView, 
    meta: { hideLayout: true } 
  },
  { 
    path: '/dashboard', 
    name: 'Dashboard', 
    component: DashboardView, 
    meta: { requiresAuth: true } 
  },
  { 
    path: '/profile', 
    name: 'Profile', 
    component: ProfileView, 
    meta: { requiresAuth: true } 
  },
  {
    path: '/code',
    name: 'CodePractice',
    component: CodePracticeView,
    meta: { requiresAuth: true }
  },
  {
    path: '/code/problems/:problemId',
    name: 'CodeProblem',
    component: CodeProblemView,
    meta: { requiresAuth: true }
  },
  { 
    path: '/interview/:role', 
    name: 'InterviewRoom', 
    component: InterviewRoomView, 
    meta: { requiresAuth: true, hideLayout: true } 
  },
  { 
    path: '/report/:id', 
    name: 'Report', 
    component: ReportView, 
    meta: { requiresAuth: true } 
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router
