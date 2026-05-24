import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const KEY = 'rsod_detection'

function loadState() {
  try { return JSON.parse(sessionStorage.getItem(KEY)) || {} } catch { return {} }
}

function saveState(state) {
  sessionStorage.setItem(KEY, JSON.stringify(state))
}

export const useDetectionStore = defineStore('detection', () => {
  // ── Config ──
  const selectedModel = ref('')
  const confThreshold = ref(0.5)
  const iouThreshold = ref(0.45)
  const useSahi = ref(false)
  const activeTab = ref('single')

  // ── Single mode ──
  const singleFile = ref(null)         // 不可序列化，不持久化
  const singleOriginal = ref('')
  const singleResultImg = ref('')
  const singleResult = ref(null)

  // ── Batch mode ──
  const batchFiles = ref([])           // [{ filename, preview, done, total_objects, detection_time, boxes, result_url, original_url, detection_id }]
  const batchDone = ref(0)
  const batchCurrentIdx = ref(-1)
  const batchTotalObjects = ref(0)
  const batchTotalTime = ref('0')
  const batchSelectedIdx = ref(-1)

  // ── Persist ──
  function collect() {
    return {
      selectedModel: selectedModel.value,
      confThreshold: confThreshold.value,
      iouThreshold: iouThreshold.value,
      useSahi: useSahi.value,
      activeTab: activeTab.value,
      singleOriginal: singleOriginal.value,
      singleResultImg: singleResultImg.value,
      singleResult: singleResult.value,
      batchFiles: batchFiles.value,
      batchDone: batchDone.value,
      batchCurrentIdx: batchCurrentIdx.value,
      batchTotalObjects: batchTotalObjects.value,
      batchTotalTime: batchTotalTime.value,
      batchSelectedIdx: batchSelectedIdx.value,
    }
  }

  function restore() {
    const s = loadState()
    selectedModel.value = s.selectedModel || ''
    confThreshold.value = s.confThreshold ?? 0.5
    iouThreshold.value = s.iouThreshold ?? 0.45
    useSahi.value = s.useSahi ?? false
    activeTab.value = s.activeTab || 'single'
    singleOriginal.value = s.singleOriginal || ''
    singleResultImg.value = s.singleResultImg || ''
    singleResult.value = s.singleResult || null
    batchFiles.value = s.batchFiles || []
    batchDone.value = s.batchDone || 0
    batchCurrentIdx.value = s.batchCurrentIdx ?? -1
    batchTotalObjects.value = s.batchTotalObjects || 0
    batchTotalTime.value = s.batchTotalTime || '0'
    batchSelectedIdx.value = s.batchSelectedIdx ?? -1
  }

  // 自动持久化
  watch(collect, saveState, { deep: true })

  // ── Reset ──
  function resetSingle() {
    singleFile.value = null
    singleOriginal.value = ''
    singleResultImg.value = ''
    singleResult.value = null
  }

  function resetBatch() {
    batchFiles.value = []
    batchDone.value = 0
    batchCurrentIdx.value = -1
    batchTotalObjects.value = 0
    batchTotalTime.value = '0'
    batchSelectedIdx.value = -1
  }

  function resetConfig() {
    selectedModel.value = ''
    confThreshold.value = 0.5
    iouThreshold.value = 0.45
    useSahi.value = false
  }

  function clearAll() {
    resetSingle()
    resetBatch()
    resetConfig()
    activeTab.value = 'single'
    sessionStorage.removeItem(KEY)
  }

  // restore on store creation
  restore()

  return {
    selectedModel, confThreshold, iouThreshold, useSahi, activeTab,
    singleFile, singleOriginal, singleResultImg, singleResult,
    batchFiles, batchDone, batchCurrentIdx, batchTotalObjects, batchTotalTime, batchSelectedIdx,
    resetSingle, resetBatch, resetConfig, clearAll, restore,
  }
})
