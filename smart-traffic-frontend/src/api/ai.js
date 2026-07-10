import axios from 'axios'

// /internal/ai 不在 /api/v1 下面，单独实例
const ai = axios.create({ baseURL: '', timeout: 30000 })
ai.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
// 复用信封格式
ai.interceptors.response.use(
  response => {
    const raw = response.data
    if (typeof raw === 'object' && raw !== null && !('code' in raw)) {
      return { code: 200, message: 'ok', data: raw }
    }
    return raw
  },
  error => Promise.reject(error)
)

export const yoloDetect = (formData) => ai.post('/internal/ai/yolo/detect', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
export const ocrPlate = (formData) => ai.post('/internal/ai/ocr/plate', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
export const evaluateRule = (data) => ai.post('/internal/ai/rules/evaluate', data)
export const reviewText = (data) => ai.post('/internal/ai/review/text', data)
