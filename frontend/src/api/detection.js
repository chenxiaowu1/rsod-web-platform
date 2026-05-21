import request from '../utils/request'

// ── 快速预览 (TIF→PNG) ─────────────────────────
export const previewImage = (data) => {
  return request({
    url: '/detection/preview',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// ── 单图检测 ──────────────────────────────────────
export const detectSingleImage = (data) => {
  return request({
    url: '/detection/single',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// ── 批量检测 ──────────────────────────────────────
export const detectBatchImages = (data) => {
  return request({
    url: '/detection/batch',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// ── 历史记录 ──────────────────────────────────────
export const getDetectionHistory = (params) => {
  return request({
    url: '/detection/history',
    method: 'get',
    params
  })
}

export const getDetectionDetail = (id) => {
  return request({
    url: `/detection/history/${id}`,
    method: 'get'
  })
}

export const deleteDetectionRecord = (id) => {
  return request({
    url: `/detection/history/${id}`,
    method: 'delete'
  })
}

// ── 目标库 ──────────────────────────────────────
export const getTargetList = () => {
  return request({
    url: '/detection/targets/list',
    method: 'get'
  })
}

// ── 模型管理 ──────────────────────────────────────
export const getModels = () => {
  return request({
    url: '/detection/models',
    method: 'get'
  })
}

export const switchModel = (modelKey) => {
  return request({
    url: '/detection/model/switch',
    method: 'post',
    data: { model_key: modelKey }
  })
}

// ── 用户中心 ──────────────────────────────────────
export const getUserProfile = () => {
  return request({
    url: '/user/profile',
    method: 'get'
  })
}

// ── AI 问答 ──────────────────────────────────────
export const askQuestion = (data) => {
  return request({
    url: '/qa/ask',
    method: 'post',
    data
  })
}

// ── 标注导出 ──────────────────────────────────────
export const exportDetection = (recordId, format = 'coco') => {
  return request({
    url: '/detection/export',
    method: 'post',
    data: { record_id: recordId, format },
    responseType: 'blob'
  })
}

// ── 批量下载结果图 ────────────────────────────
export const downloadResultsZip = (recordIds) => {
  return request({
    url: '/detection/download-results',
    method: 'post',
    data: { record_ids: recordIds },
    responseType: 'blob'
  })
}

// ── 模型评估 ──────────────────────────────────────
export const getStatistics = (params) => {
  return request({
    url: '/detection/statistics',
    method: 'get',
    params
  })
}

// ── 变化检测 ──────────────────────────────────────
export const detectChangeSingle = (data) => {
  return request({
    url: '/change-detection/single',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const detectChangeBatch = (data) => {
  return request({
    url: '/change-detection/batch',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const getChangeModels = () => {
  return request({
    url: '/change-detection/models',
    method: 'get'
  })
}

export const switchChangeModel = (modelKey) => {
  return request({
    url: '/change-detection/model/switch',
    method: 'post',
    data: { model_key: modelKey }
  })
}

export const getChangeHistory = (params) => {
  return request({
    url: '/change-detection/history',
    method: 'get',
    params
  })
}

export const deleteChangeRecord = (id) => {
  return request({
    url: `/change-detection/history/${id}`,
    method: 'delete'
  })
}

// ── 视频流检测 ──────────────────────────────────────
export const detectVideo = (data) => {
  return request({
    url: '/video/detect',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000
  })
}

export const getVideoModels = () => {
  return request({ url: '/video/models', method: 'get' })
}

export const switchVideoModel = (modelKey) => {
  return request({
    url: '/video/model/switch',
    method: 'post',
    data: { model_key: modelKey }
  })
}

export const downloadVideo = (videoId) => {
  return request({
    url: `/video/download/${videoId}`,
    method: 'get',
    responseType: 'blob'
  })
}
