import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 10000,
})

instance.interceptors.request.use((config) => {
  const authStore = useAuthStore()
  if (authStore.token) {
    config.headers.Authorization = `Bearer ${authStore.token}`
  }
  return config
})

// 添加响应拦截器：实现前端独立解耦开发的 Mock 数据挡板
instance.interceptors.response.use(
  (response) => response,
  (error) => {
    const config = error.config
    if (config && config.url) {
      // 1. 拦截查询未完成面试的请求 (后端暂未实现，会报404)
      if (config.url.endsWith('/interview/incomplete') && error.response && error.response.status === 404) {
        console.log('【Mock API】拦截到 /interview/incomplete 请求，注入模拟数据...')
        return Promise.resolve({
          data: {
            has_incomplete: true,
            interview: {
              id: 999, // 模拟的面试房间 ID
              role: 'Java后端开发工程师',
              start_time: '2026-04-24T18:30:00Z'
            }
          }
        })
      }
      
      // 2. 拦截废弃面试的请求
      if (config.url.match(/\/interview\/\d+\/discard/) && error.response && error.response.status === 404) {
        console.log('【Mock API】拦截到废弃面试请求，模拟废弃成功...')
        return Promise.resolve({ data: { success: true } })
      }
    }
    return Promise.reject(error)
  }
)

export default instance