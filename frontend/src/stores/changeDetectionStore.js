import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const KEY = 'rsod_change_detection'

function loadState() {
  try { return JSON.parse(sessionStorage.getItem(KEY)) || {} } catch { return {} }
}

function saveState(state) {
  sessionStorage.setItem(KEY, JSON.stringify(state))
}

export const useChangeDetectionStore = defineStore('changeDetection', () => {
  // ── Config ──
  const selectedModel = ref('')
  const activeTab = ref('single')

  // ── Single mode ──
  const fileAName = ref('')
  const fileBName = ref('')
  const singleImgA = ref('')
  const singleImgB = ref('')
  const singleResultUrl = ref('')
  const singleResult = ref(null)
  // 不可序列化：fileA, fileB — 不持久化

  // ── Batch mode ──
  const batchPairs = ref([])  // [{ filename_a, filename_b, done, result_url, change_ratio, detection_id }]
  const batchDone = ref(0)
  const batchCurrentIdx = ref(-1)
  const batchTotalTime = ref('0')
  const folderACount = ref(0)
  const folderBCount = ref(0)
  // 不可序列化：filesAList, filesBList, file_a, file_b — 不持久化

  // ── Persist ──
  function collect() {
    return {
      selectedModel: selectedModel.value,
      activeTab: activeTab.value,
      fileAName: fileAName.value,
      fileBName: fileBName.value,
      singleImgA: singleImgA.value,
      singleImgB: singleImgB.value,
      singleResultUrl: singleResultUrl.value,
      singleResult: singleResult.value,
      batchPairs: batchPairs.value,
      batchDone: batchDone.value,
      batchCurrentIdx: batchCurrentIdx.value,
      batchTotalTime: batchTotalTime.value,
      folderACount: folderACount.value,
      folderBCount: folderBCount.value,
    }
  }

  function restore() {
    const s = loadState()
    selectedModel.value = s.selectedModel || ''
    activeTab.value = s.activeTab || 'single'
    fileAName.value = s.fileAName || ''
    fileBName.value = s.fileBName || ''
    singleImgA.value = s.singleImgA || ''
    singleImgB.value = s.singleImgB || ''
    singleResultUrl.value = s.singleResultUrl || ''
    singleResult.value = s.singleResult || null
    batchPairs.value = s.batchPairs || []
    batchDone.value = s.batchDone || 0
    batchCurrentIdx.value = s.batchCurrentIdx ?? -1
    batchTotalTime.value = s.batchTotalTime || '0'
    folderACount.value = s.folderACount || 0
    folderBCount.value = s.folderBCount || 0
  }

  watch(collect, saveState, { deep: true })

  // ── Reset ──
  function resetSingle() {
    fileAName.value = ''
    fileBName.value = ''
    singleImgA.value = ''
    singleImgB.value = ''
    singleResultUrl.value = ''
    singleResult.value = null
  }

  function resetBatch() {
    batchPairs.value = []
    batchDone.value = 0
    batchCurrentIdx.value = -1
    batchTotalTime.value = '0'
    folderACount.value = 0
    folderBCount.value = 0
  }

  function clearAll() {
    resetSingle()
    resetBatch()
    selectedModel.value = ''
    activeTab.value = 'single'
    sessionStorage.removeItem(KEY)
  }

  restore()
  return {
    selectedModel, activeTab,
    fileAName, fileBName, singleImgA, singleImgB, singleResultUrl, singleResult,
    batchPairs, batchDone, batchCurrentIdx, batchTotalTime, folderACount, folderBCount,
    resetSingle, resetBatch, clearAll, restore,
  }
})
