import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const KEY = 'rsod_video'

function loadState() {
  try { return JSON.parse(sessionStorage.getItem(KEY)) || {} } catch { return {} }
}

function saveState(state) {
  sessionStorage.setItem(KEY, JSON.stringify(state))
}

export const useVideoStore = defineStore('video', () => {
  const selectedModel = ref('')
  const result = ref(null)
  const processing = ref(false)
  const videoFileName = ref('')
  const _activeTab = ref('video')
  const _videoPreviewUrl = ref('')
  const _resultPreviewUrl = ref('')

  function collect() {
    return {
      selectedModel: selectedModel.value,
      result: result.value,
      processing: processing.value,
      videoFileName: videoFileName.value,
      _activeTab: _activeTab.value,
      _videoPreviewUrl: _videoPreviewUrl.value,
      _resultPreviewUrl: _resultPreviewUrl.value,
    }
  }

  function restore() {
    const s = loadState()
    selectedModel.value = s.selectedModel || ''
    result.value = s.result || null
    processing.value = false
    videoFileName.value = s.videoFileName || ''
    _activeTab.value = s._activeTab || 'video'
    _videoPreviewUrl.value = s._videoPreviewUrl || ''
    _resultPreviewUrl.value = s._resultPreviewUrl || ''
  }

  watch(collect, saveState, { deep: true })

  function resetAll() {
    result.value = null
    processing.value = false
    videoFileName.value = ''
    _videoPreviewUrl.value = ''
    _resultPreviewUrl.value = ''
  }

  function clearAll() {
    resetAll()
    selectedModel.value = ''
    _activeTab.value = 'video'
    sessionStorage.removeItem(KEY)
  }

  restore()
  return { selectedModel, result, processing, videoFileName, _activeTab, _videoPreviewUrl, _resultPreviewUrl, resetAll, clearAll, restore }
})
