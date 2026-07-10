import request from './request'

// 图片接入 API — 对齐 API接口规范文档 v2.0 §3
// 三来源：市民举报 / 后台管理员上传 / 摄像头抓拍（通过 X-Camera-Key 鉴权）
export const citizenReport = (fd) => request.post('/intakes/citizen-reports', fd, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const cameraCapture = (fd) => request.post('/intakes/camera-captures', fd, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const adminUpload = (fd) => request.post('/intakes/admin-uploads', fd, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
