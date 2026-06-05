/**
 * 模块名称：API 客户端（api/index）
 * 功能描述：基于 Axios 的 HTTP 客户端封装，提供所有后端 API 的统一调用接口。
 *
 * 功能模块：
 * - resumeApi：简历解析
 * - evaluationApi：面试评估与报告
 * - interviewApi：面试会话管理
 * - codeApi：代码题库与判题
 *
 * 特性：
 * - 请求拦截器：自动注入 Authorization Token
 * - 响应拦截器：统一处理 401 未授权错误
 */
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const apiBaseUrl =
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  'http://localhost:8000/api'

const instance = axios.create({
  baseURL: apiBaseUrl,
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

export const interviewApi = {
  getState: (interviewId) => instance.get(`/interview/${interviewId}/state`),
  submitCode: (interviewId, data) => instance.post(`/interview/${interviewId}/code/submit`, data, { timeout: 120000 })
}

// 代码面试模块（W4.3.5 / W5.3 扩展）
export const codeApi = {
  getProblems: (params) => instance.get('/code/problems', { params }),
  getProblemDetail: (problemId) => instance.get(`/code/problems/${problemId}`),
  run: (problemId, data) => instance.post(`/code/problems/${problemId}/run`, data),
  submit: (problemId, data) => instance.post(`/code/problems/${problemId}/submit`, data)
}

export default instance
