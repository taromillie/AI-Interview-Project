import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const http = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (resp) => resp.data,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail || error.response?.data?.message || '请求失败'
    if (status === 401) {
      localStorage.removeItem('token')
      router.push({ name: 'login' })
    }
    ElMessage.error(typeof detail === 'string' ? detail : '请求失败')
    return Promise.reject(error)
  },
)

export default http
