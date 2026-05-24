import { ref } from 'vue'
import { getSession } from '../utils/auth'

const MAX_MESSAGES = 100

function getStorageKey() {
  const user = getSession()
  const uid = user?.id || 'anonymous'
  return `rsod-chat-history-${uid}`
}

function loadSessions() {
  try { return JSON.parse(localStorage.getItem(getStorageKey())) || [] }
  catch { return [] }
}

function saveSessions(sessions) {
  localStorage.setItem(getStorageKey(), JSON.stringify(sessions))
}

export function useChatHistory() {
  const sessions = ref(loadSessions())
  const currentId = ref(sessions.value[0]?.id || null)
  const messages = ref([])

  function loadMessages() {
    const s = sessions.value.find(s => s.id === currentId.value)
    messages.value = s?.messages?.slice(-MAX_MESSAGES) || []
  }

  if (currentId.value) loadMessages()

  function newSession() {
    const id = Date.now().toString(36)
    const session = { id, title: '新对话', createdAt: new Date().toISOString(), messages: [] }
    sessions.value.unshift(session)
    currentId.value = id
    messages.value = []
    saveSessions(sessions.value)
  }

  function addMessage(msg) {
    messages.value.push(msg)
    const s = sessions.value.find(s => s.id === currentId.value)
    if (s) {
      s.messages = [...messages.value]
      if (s.title === '新对话' && msg.role === 'user') {
        s.title = msg.content.slice(0, 30) + (msg.content.length > 30 ? '...' : '')
      }
      saveSessions(sessions.value)
    }
  }

  function switchSession(id) {
    currentId.value = id
    loadMessages()
  }

  function deleteSession(id) {
    sessions.value = sessions.value.filter(s => s.id !== id)
    saveSessions(sessions.value)
    if (currentId.value === id) {
      if (sessions.value.length) {
        switchSession(sessions.value[0].id)
      } else {
        currentId.value = null
        messages.value = []
      }
    }
  }

  function renameSession(id, title) {
    const s = sessions.value.find(s => s.id === id)
    if (s && title.trim()) {
      s.title = title.trim()
      saveSessions(sessions.value)
    }
  }

  return { sessions, currentId, messages, newSession, addMessage, switchSession, deleteSession, renameSession }
}
