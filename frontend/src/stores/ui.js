import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const theme = ref(localStorage.getItem('rsod-theme') || 'dark')
  const globalLoading = ref(false)
  const globalLoadingText = ref('')

  const isDark = computed(() => theme.value === 'dark')

  function toggleTheme() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    localStorage.setItem('rsod-theme', theme.value)
    document.documentElement.setAttribute('data-theme', theme.value)
  }

  function setLoading(loading, text = '加载中...') {
    globalLoading.value = loading
    globalLoadingText.value = text
  }

  return { theme, globalLoading, globalLoadingText, isDark, toggleTheme, setLoading }
})
