/**
 * 模块名称：认证状态管理（stores/auth）
 * 功能描述：基于 Pinia 的用户认证状态管理，管理 Token 持久化和登录/登出逻辑。
 *
 * 状态：
 * - token：认证 Token（持久化到 localStorage）
 * - user：当前登录用户信息
 *
 * 操作：
 * - login(username, password)：登录并保存 Token
 * - register(username, password)：注册新用户
 * - logout()：清除 Token 和用户信息
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user')) || null)

  const isAuthenticated = ref(!!token.value)

  const login = (newToken, userData) => {
    token.value = newToken
    user.value = userData
    isAuthenticated.value = true
    localStorage.setItem('token', newToken)
    localStorage.setItem('user', JSON.stringify(userData))
  }

  const logout = () => {
    token.value = ''
    user.value = null
    isAuthenticated.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { token, user, isAuthenticated, login, logout }
})
