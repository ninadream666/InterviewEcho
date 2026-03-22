<template>
  <div id="app" class="min-h-screen flex flex-col">
    <!-- Navigation Bar -->
    <header class="bg-white shadow-sm py-4 px-8 flex justify-between items-center fixed w-full top-0 z-50">
      <div class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary">
        InterviewEcho
      </div>
      <nav v-if="authStore.isAuthenticated">
        <router-link to="/dashboard" class="text-gray-600 hover:text-primary mx-4 transition-colors">仪表盘</router-link>
        <button @click="logout" class="text-gray-600 hover:text-primary transition-colors">登出</button>
      </nav>
      <nav v-else>
        <router-link to="/login" class="text-gray-600 hover:text-primary transition-colors">登录/注册</router-link>
      </nav>
    </header>

    <!-- Main Content Area -->
    <main class="flex-grow pt-20 bg-gray-50 pb-10">
      <div class="container mx-auto px-4">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>

    <!-- Footer -->
    <footer class="bg-dark text-white text-center py-4">
      <p class="text-sm">© 2026 InterviewEcho. 面向计算机相关学生的AI模拟面试平台.</p>
    </footer>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const logout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
