import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, getSession, tryRefreshAccessToken, clearAuthState } from './auth'

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

// 响应拦截器 — 401：先尝试 refresh token，失败再清状态弹登录
service.interceptors.response.use(
  response => response.data,
  async error => {
    if (error.response?.status === 401) {
      // 先尝试用 refresh_token 续签
      const refreshed = await tryRefreshAccessToken()
      if (refreshed) {
        // 续签成功，重试原请求
        const token = getToken()
        if (token) {
          error.config.headers.Authorization = `Bearer ${token}`
          return service(error.config)
        }
      } else {
        // 续签失败 → 清除认证状态，同步 UI
        clearAuthState()
      }
      // 弹登录框等用户重新登录
      await waitForLogin()
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

// 统一 SSE 流式请求
export async function streamRequest(url, data, onChunk, onDone, onError) {
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
  const token = getToken()

  try {
    const resp = await fetch(`${baseURL}${url}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(data),
    })

    if (resp.status === 401) {
      const refreshed = await tryRefreshAccessToken()
      if (refreshed) {
        return streamRequest(url, data, onChunk, onDone, onError)
      }
      clearAuthState()
      await waitForLogin()
      return streamRequest(url, data, onChunk, onDone, onError)
    }
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) { onDone?.(); break }
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try { onChunk(JSON.parse(line.slice(6))) } catch (e) { /* skip */ }
        }
      }
    }
  } catch (e) {
    onError?.(e)
  }
}

export default service
