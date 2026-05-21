import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, getSession } from './auth'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 30000
})

// 登录弹窗触发器 — App.vue 挂载后注入
let showLoginModal = null
let _loginResolve = null

export function setLoginModalTrigger(fn) { showLoginModal = fn }
export function notifyLoggedIn() {
  if (_loginResolve) { _loginResolve(); _loginResolve = null }
}

function waitForLogin() {
  return new Promise((resolve) => {
    _loginResolve = resolve
    if (showLoginModal) showLoginModal()
  })
}

// 页面调用：未登录则弹框，登录成功后返回 true
export async function requireLogin() {
  if (getSession()) return true
  if (showLoginModal) showLoginModal()
  await waitForLogin()
  return !!getSession()
}

// 请求拦截器
service.interceptors.request.use(
  config => {
    const token = getToken()
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器
service.interceptors.response.use(
  response => response.data,
  async error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('rsod-access-token')
      localStorage.removeItem('rsod-refresh-token')
      localStorage.removeItem('rsod-user')
      // 等待用户登录后重试
      await waitForLogin()
      // 登录成功后重试原请求
      const token = getToken()
      if (token) {
        error.config.headers.Authorization = `Bearer ${token}`
        return service(error.config)
      }
      return Promise.reject(error)
    }
    ElMessage.error('请求失败：' + (error.response?.data?.detail || error.response?.data?.message || '服务器错误'))
    return Promise.reject(error)
  }
)

export default service
