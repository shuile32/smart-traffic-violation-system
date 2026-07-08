/**
 * 案件管理 API — 对齐 API接口规范文档 v2.0 §4
 */
import { ok, pageOk, delay, mockCases } from './mock'

// ==================== Mock API (默认使用) ====================
export const getCases = async (params = {}) => {
  await delay()
  const { status, source_type, page = 1, page_size = 10, keyword } = params
  let filtered = [...mockCases]

  if (status) filtered = filtered.filter(c => c.status === status)
  if (source_type) filtered = filtered.filter(c => c.source_type === source_type)
  if (keyword) {
    const kw = keyword.toLowerCase()
    filtered = filtered.filter(c =>
      c.case_no.toLowerCase().includes(kw) ||
      c.plate_no.toLowerCase().includes(kw) ||
      c.location_text.toLowerCase().includes(kw)
    )
  }

  const total = filtered.length
  const start = (page - 1) * page_size
  const list = filtered.slice(start, start + page_size)

  return pageOk(list, total, page, page_size)
}

export const getCaseDetail = async (id) => {
  await delay()
  const c = mockCases.find(c => c.id === Number(id))
  if (!c) return { code: 404, message: '案件不存在', data: null }
  return ok(c)
}

export const approveCase = async (id, data) => {
  await delay(400)
  return ok({
    case_id: Number(id),
    violation_id: 9000 + Number(id),
    status: 'approved',
    message: '审核通过，违章记录已生成。'
  })
}

export const rejectCase = async (id, data) => {
  await delay(300)
  return ok({
    case_id: Number(id),
    status: 'rejected',
    message: '案件已驳回。'
  })
}

export const requestRecheck = async (id) => {
  await delay(500)
  return ok({
    case_id: Number(id),
    status: 'ai_reviewing',
    message: '已重新投递 AI 初审任务。'
  })
}

export const batchApprove = async (data) => {
  await delay(300)
  return ok({ success_count: data.ids?.length || 0, message: '批量审核通过完成' })
}

export const batchReject = async (data) => {
  await delay(300)
  return ok({ success_count: data.ids?.length || 0, message: '批量驳回完成' })
}
