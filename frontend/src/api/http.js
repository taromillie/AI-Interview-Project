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
    const data = error.response?.data
    let msg = '请求失败'
    if (data?.detail) {
      // FastAPI 验证错误 [{"loc":..., "msg":...}]
      if (Array.isArray(data.detail)) {
        msg = data.detail.map((d) => d.msg).join('；') || msg
      } else {
        msg = data.detail
      }
    } else if (data?.message) {
      msg = data.message
    }
    if (status === 401) {
      localStorage.removeItem('token')
      router.push({ name: 'login' })
    }
    ElMessage.error(msg)
    return Promise.reject(error)
  },
)

export default http
