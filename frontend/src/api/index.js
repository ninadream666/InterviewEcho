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

// 添加响应拦截器：统一错误处理
instance.interceptors.response.use(
  (response) => response,
  (error) => {
    return Promise.reject(error)
  }
)

// 导出单独的 API 封装（W4.2.4 / W4.5.8 扩展）
export const resumeApi = {
  parse: (formData) => instance.post('/interview/resume/parse', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000
  })
}

export const evaluationApi = {
  getEvaluation: (evalId) => instance.get(`/interview/${evalId}/evaluation`)
}

// 代码面试模块（W4.3.5 / W5.3 扩展）
export const codeApi = {
  run: (data) => instance.post('/code/run', data),
  submit: (data) => instance.post('/code/submit', data)
}

export default instance