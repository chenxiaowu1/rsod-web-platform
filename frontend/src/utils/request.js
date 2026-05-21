import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getSession } from './auth'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 30000
})

// 请求拦截器 — 自动附带用户名
service.interceptors.request.use(
  config => {
    const session = getSession()
    if (session?.username) {
      // GET 请求加 query param，POST 加 FormData
      if (config.method === 'get') {
        config.params = { ...config.params, username: session.username }
      } else if (config.data instanceof FormData) {
        config.data.append('username', session.username)
      }
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    ElMessage.error('请求失败：' + (error.response?.data?.message || '服务器错误'))
    return Promise.reject(error)
  }
)

export default service