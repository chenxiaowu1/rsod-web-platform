import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getSession, getToken } from '../utils/auth'

export const useAuthStore = defineStore('auth', () => {
  const session = ref(getSession())
  const token = ref(getToken())

  const loggedIn = computed(() => !!token.value && !!session.value)
  const isAdmin = computed(() => session.value?.role === 'admin')
  const username = computed(() => session.value?.username || '')

  function refresh() {
    session.value = getSession()
    token.value = getToken()
  }

  function clear() {
    session.value = null
    token.value = null
  }

  return { session, token, loggedIn, isAdmin, username, refresh, clear }
})
