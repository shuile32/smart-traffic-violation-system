import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 15000
})

// 请求拦截器 —— 自动携带 token
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器 —— 统一处理错误
request.interceptors.response.use(
  response => {
    const raw = response.data
    // 后端返裸 Pydantic（无 {code,message,data} 信封），包一层对齐 mock
    if (typeof raw === 'object' && raw !== null && !('code' in raw)) {
      return { code: 200, message: 'ok', data: raw }
    }
    if (raw.code === 401) {
      localStorage.clear()
      router.push('/login')
      return Promise.reject(new Error('登录已过期'))
    }
    return raw
  },
  error => {
    if (error.response) {
      switch (error.response.status) {
        case 401:
          localStorage.clear()
          router.push('/login')
          ElMessage.error('登录已过期，请重新登录')
          break
        case 403:
          ElMessage.error('没有操作权限')
          break
        case 500:
          ElMessage.error('服务器错误，请稍后重试')
          break
        default:
          ElMessage.error(error.response.data?.message || '请求失败')
      }
    } else {
      ElMessage.error('网络连接失败')
    }
    return Promise.reject(error)
  }
)

export default request
