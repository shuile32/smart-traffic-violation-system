/**
 * 违章管理 API — 连接真实后端
 */
import request from './request'

export const getViolations = async (params = {}) => {
  const res = await request.get('/violations', { params })
  return { ...res, data: { list: res.data.items, total: res.data.total, page: res.data.page, page_size: res.data.page_size } }
}

export const getViolationDetail = (id) => request.get(`/violations/${id}`)

export const manualNotify = (id) => request.post(`/violations/${id}/notify`)

export const getOwnerViolations = async (ownerId, params = {}) => {
  const res = await request.get(`/owners/${ownerId}/violations`, { params })
  return { ...res, data: { list: res.data.items, total: res.data.total, page: res.data.page, page_size: res.data.page_size } }
}

export const exportExcel = (params) => request.get('/violations/export', { params, responseType: 'blob' })

// 市民举报 (转发到 intake)
export const submitReport = (formData) =>
  request.post('/intakes/citizen-reports', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })

// 举报记录查询 (后端暂无端点，保留 stub)
export const getReports = async (params = {}) => ({ code: 200, data: { list: [], total: 0, page: 1, page_size: 10 }, message: 'success' })
