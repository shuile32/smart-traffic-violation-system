/**
 * 图片接入 API — 对齐 API接口规范文档 v2.0 §3
 */
import { ok, pageOk, delay } from './mock'

// ==================== Mock API (默认使用) ====================
export const citizenReport = async (formData) => {
  await delay(600)
  return ok({
    intake_event_id: 5001,
    case_id: 8001,
    case_no: 'CASE008001',
    status: 'uploaded',
    message: '图片已接收，正在进行 AI 识别，预计 30 秒内完成。'
  })
}

export const cameraCapture = async (formData) => {
  await delay(300)
  return ok({
    intake_event_id: 5002,
    case_id: 8002,
    case_no: 'CASE008002',
    status: 'uploaded',
    message: '抓拍图片已接入，正在处理。'
  })
}

export const adminUpload = async (formData) => {
  await delay(400)
  return ok({
    intake_event_id: 5003,
    case_id: 8003,
    case_no: 'CASE008003',
    status: 'uploaded',
    message: '图片已上传，已投递 AI 识别任务。'
  })
}

export const getIntakeEvents = async (params = {}) => {
  await delay()
  return pageOk([], 0)
}

export const getIntakeEvent = async (id) => {
  await delay()
  return ok({ id })
}
