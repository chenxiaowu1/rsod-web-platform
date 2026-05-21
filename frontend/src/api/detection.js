import request from '../utils/request'

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
