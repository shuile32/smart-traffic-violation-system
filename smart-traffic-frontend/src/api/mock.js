/**
 * Mock 数据工厂 — 前端独立开发使用
 * 所有数据格式对齐 API接口规范文档 v2.0
 */

// ==================== 工具函数 ====================
let _id = 100
const uid = () => ++_id
const now = () => new Date().toISOString()
const rand = (arr) => arr[Math.floor(Math.random() * arr.length)]
const randInt = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min

// ==================== 用户 ====================
export const mockUsers = [
  { id: 1, username: 'admin', phone: '13800000001', role: 'admin', status: 'enabled' },
  { id: 2, username: 'reviewer', phone: '13800000002', role: 'reviewer', status: 'enabled' },
  { id: 3, username: 'citizen', phone: '13800000003', role: 'citizen', status: 'enabled' }
]

// ==================== 车辆 ====================
const platePrefix = ['粤A', '粤B', '京A', '沪A', '苏A', '浙A']
export const mockVehicles = Array.from({ length: 20 }, (_, i) => ({
  id: i + 1,
  plate_no: `${rand(platePrefix)}${randInt(10000, 99999)}`,
  owner_id: randInt(3, 10),
  owner_name: ['张伟', '李娜', '王强', '赵敏', '刘洋'][i % 5],
  owner_phone: `138${String(randInt(10000000, 99999999))}`,
  vehicle_type: rand(['小型轿车', 'SUV', '货车', '摩托车', '公交车']),
  color: rand(['白', '黑', '银', '红', '蓝', '灰']),
  created_at: now()
}))

// ==================== 摄像头设备 ====================
export const mockCameras = [
  { id: 1, camera_id: 'CAM-001', name: '人民路与建设路交叉口东', location_text: '人民路与建设路交叉口', status: 'active', created_at: now() },
  { id: 2, camera_id: 'CAM-002', name: '中山大道天河路口', location_text: '中山大道天河路', status: 'active', created_at: now() },
  { id: 3, camera_id: 'CAM-003', name: '解放路北京路口', location_text: '解放路与北京路交叉口', status: 'active', created_at: now() },
  { id: 4, camera_id: 'CAM-004', name: '东风路农林下路口', location_text: '东风路农林下路', status: 'inactive', created_at: now() }
]

// ==================== 违章类型 ====================
const violationTypes = ['闯红灯', '违停', '压线', '逆行', '超速', '占用应急车道']
const locations = ['人民路与建设路交叉口', '中山大道天河路', '解放路与北京路交叉口', '东风路农林下路', '黄埔大道西', '广州大道中']
const sources = ['citizen', 'camera', 'admin']

// ==================== AI 检测结果生成器 ====================
function makeDetectionResult(caseId) {
  const vt = rand(violationTypes)
  const objects = []
  const bboxes = { vehicle: [100, 120, 420, 360], stop_line: [80, 365, 520, 382], red_light: [500, 40, 535, 85] }

  objects.push({ label: 'vehicle', confidence: randInt(88, 100) / 100, bbox: bboxes.vehicle })

  if (vt === '闯红灯') {
    objects.push({ label: 'stop_line', confidence: randInt(85, 98) / 100, bbox: bboxes.stop_line })
    objects.push({ label: 'red_light', confidence: randInt(88, 99) / 100, bbox: bboxes.red_light })
  } else if (vt === '压线') {
    objects.push({ label: 'lane_line', confidence: randInt(85, 97) / 100, bbox: [150, 200, 350, 205] })
  } else if (vt === '违停') {
    objects.push({ label: 'no_parking_sign', confidence: randInt(82, 96) / 100, bbox: [520, 80, 560, 130] })
  }

  const evidenceLevel = vt === '闯红灯' ? 'complete' : (Math.random() > 0.4 ? 'complete' : 'partial')
  const reviewMode = evidenceLevel === 'complete' ? 'text_llm' : 'vision_llm'
  const conclusion = evidenceLevel === 'complete'
    ? (Math.random() > 0.15 ? 'suggest_approve' : 'need_review')
    : 'need_review'

  return {
    detection: {
      id: uid(), case_id: caseId, model_name: 'yolov8-traffic-v1', model_version: 'v1.2',
      detected_objects: objects,
      plate_bbox: { bbox: [210, 310, 310, 345] },
      vehicle_bbox: { bbox: bboxes.vehicle },
      raw_result: { framework: 'ultralytics', inference_time_ms: randInt(45, 120) },
      annotated_url: `/media/annotated/${caseId}.jpg`,
      created_at: now()
    },
    rule: {
      id: uid(), case_id: caseId,
      candidate_violation_type: vt,
      rule_code: `RL-${String(randInt(1, 20)).padStart(3, '0')}`,
      rule_matched: true,
      evidence_level: evidenceLevel,
      evidence_items: ['检测到车辆', '检测到停止线', '检测到红灯状态', '车辆位置越过停止线'],
      missing_evidence: evidenceLevel === 'partial' ? ['无法确认信号灯状态连续性'] : [],
      reason: evidenceLevel === 'complete'
        ? `车辆框、停止线位置和红灯状态等证据满足${vt}规则。`
        : `疑似${vt}，但部分证据需人工确认。`,
      created_at: now()
    },
    review: {
      id: uid(), case_id: caseId,
      review_mode: reviewMode,
      conclusion: conclusion,
      ai_confidence: randInt(75, 98) / 100,
      reason: conclusion === 'suggest_approve'
        ? `规则判定显示满足${vt}条件，证据链较完整，建议人工终审确认。`
        : '部分视觉要素检测存在不确定性，建议人工重点复核。',
      risk_points: conclusion === 'need_review' ? ['车辆框边缘模糊', '光照条件不佳'] : [],
      missing_evidence: evidenceLevel === 'partial' ? ['信号灯状态暂不清晰'] : [],
      prompt_version: 'traffic-review-v1',
      created_at: now()
    }
  }
}

// ==================== 案件数据生成器 ====================
function makeCase(status) {
  const id = uid()
  const source = rand(sources)
  const location = rand(locations)
  const capturedAt = new Date(Date.now() - randInt(0, 7 * 86400000)).toISOString()
  const plateNo = `${rand(platePrefix)}${randInt(10000, 99999)}`

  const base = {
    id, case_no: `CASE${String(id).padStart(6, '0')}`,
    source_type: source,
    source_desc: source === 'citizen' ? '市民王先生' : source === 'camera' ? 'CAM-001' : '管理员',
    location_text: location,
    captured_at: capturedAt,
    speed: source === 'camera' ? randInt(30, 120) : null,
    plate_no: plateNo,
    violation_type: null,
    reviewer_id: null,
    review_opinion: null,
    reviewed_at: null,
    status,
    created_at: capturedAt,
    media: {
      original_url: `/media/original/${id}.jpg`,
      annotated_url: `/media/annotated/${id}.jpg`
    }
  }

  // 根据状态补充 AI 和审核数据
  switch (status) {
    case 'uploaded':
      break
    case 'detecting':
      base.detection_result = makeDetectionResult(id).detection
      break
    case 'ai_reviewing':
      Object.assign(base, makeDetectionResult(id))
      break
    case 'pending_human_review':
      Object.assign(base, makeDetectionResult(id))
      break
    case 'approved':
      Object.assign(base, makeDetectionResult(id))
      base.reviewer_id = 2
      base.violation_type = base.rule.candidate_violation_type
      base.review_opinion = '证据清晰，AI 分析准确，确认违章。'
      base.reviewed_at = new Date(Date.now() - randInt(1000, 86400000)).toISOString()
      break
    case 'rejected':
      Object.assign(base, makeDetectionResult(id))
      base.reviewer_id = 2
      base.review_opinion = '图片模糊，关键要素无法确认，予以驳回。'
      base.reviewed_at = new Date(Date.now() - randInt(1000, 86400000)).toISOString()
      break
    case 'archived':
      Object.assign(base, makeDetectionResult(id))
      base.reviewer_id = 2
      base.violation_type = base.rule.candidate_violation_type
      base.review_opinion = '确认违章，已归档。'
      base.reviewed_at = new Date(Date.now() - randInt(100000, 86400000)).toISOString()
      break
    case 'notified':
      Object.assign(base, makeDetectionResult(id))
      base.reviewer_id = 2
      base.violation_type = base.rule.candidate_violation_type
      base.review_opinion = '确认违章，已通知车主。'
      base.reviewed_at = new Date(Date.now() - randInt(200000, 86400000 * 2)).toISOString()
      break
  }

  return base
}

// ==================== 预生成 Mock 案件 ====================
export const mockCases = [
  ...Array.from({ length: 5 }, () => makeCase('pending_human_review')),
  ...Array.from({ length: 3 }, () => makeCase('uploaded')),
  ...Array.from({ length: 2 }, () => makeCase('detecting')),
  ...Array.from({ length: 2 }, () => makeCase('ai_reviewing')),
  ...Array.from({ length: 5 }, () => makeCase('approved')),
  ...Array.from({ length: 3 }, () => makeCase('rejected')),
  ...Array.from({ length: 2 }, () => makeCase('archived')),
  ...Array.from({ length: 2 }, () => makeCase('notified'))
]

// ==================== 违章记录 ====================
export const mockViolations = mockCases
  .filter(c => ['approved', 'archived', 'notified'].includes(c.status))
  .map((c, i) => ({
    id: i + 1,
    violation_no: `VIO${String(i + 1).padStart(6, '0')}`,
    case_id: c.id,
    vehicle_id: randInt(1, 20),
    owner_id: randInt(3, 10),
    owner_name: ['张伟', '李娜', '王强', '赵敏', '刘洋'][i % 5],
    plate_no: c.plate_no,
    violation_type: c.violation_type || rand(violationTypes),
    occurred_at: c.captured_at,
    location_text: c.location_text,
    fine_amount: [200, 200, 200, 200, 500, 200][randInt(0, 5)],
    points: [6, 3, 3, 3, 6, 6][randInt(0, 5)],
    status: rand(['pending', 'handled', 'cancelled']),
    created_at: c.captured_at
  }))

// ==================== 举报记录 ====================
export const mockReports = Array.from({ length: 8 }, (_, i) => ({
  id: i + 1,
  report_no: `RPT${String(i + 1).padStart(6, '0')}`,
  description: ['涉嫌闯红灯', '占用应急车道', '路边违停', '实线变道'][i % 4],
  location_text: rand(locations),
  captured_at: new Date(Date.now() - randInt(1000, 7 * 86400000)).toISOString(),
  status: rand(['uploaded', 'detecting', 'ai_reviewing', 'pending_human_review', 'approved', 'rejected']),
  image_url: `/media/original/${i + 100}.jpg`,
  reward: Math.random() > 0.5 ? randInt(10, 50) : 0,
  created_at: now()
}))

// ==================== 统计数据 ====================
export const mockStatistics = {
  overview: {
    total_cases: 2456,
    total_violations: 1823,
    total_reports: 892,
    approve_rate: 74.2,
    reject_rate: 18.5,
    pending_count: 56,
    today_new: 12,
    notify_success_rate: 96.8
  },
  trend: Array.from({ length: 30 }, (_, i) => {
    const d = new Date()
    d.setDate(d.getDate() - 29 + i)
    return { date: d.toISOString().slice(0, 10), count: randInt(30, 120) }
  }),
  typeRatio: [
    { name: '闯红灯', value: 38 },
    { name: '违停', value: 25 },
    { name: '压线', value: 18 },
    { name: '超速', value: 10 },
    { name: '逆行', value: 6 },
    { name: '其他', value: 3 }
  ],
  regionRank: locations.map(l => ({ name: l, value: randInt(50, 300) })).sort((a, b) => b.value - a.value),
  topViolations: violationTypes.map(t => ({ name: t, count: randInt(30, 200), percent: randInt(5, 35) }))
}

// ==================== LLM 报告 Mock ====================
export const mockReports2 = [
  {
    id: 1,
    title: '2026年7月第一周交通违章分析报告',
    dimension: 'week',
    period: { start: '2026-07-01', end: '2026-07-07' },
    summary: '本周违章主要集中在早晚高峰时段，人民路与建设路交叉口闯红灯占比较高（38%），违停行为在商圈附近明显增多。',
    highlights: [
      '闯红灯占比最高，达 38%，主要集中在人民路与建设路交叉口',
      '违停行为比上周增长 12%，集中在中山大道天河路商圈附近',
      '早高峰 7:30-9:00 是违章高发时段'
    ],
    suggestions: [
      '加强人民路与建设路交叉口早高峰执勤力量',
      '在天河路商圈增设违停抓拍设备',
      '优化人民路信号灯配时，减少闯红灯诱因',
      '在违章高发点位增设法令提示牌'
    ],
    created_at: now()
  }
]

// ==================== Mock 响应工具 ====================
export function ok(data, message = 'success') {
  return { code: 200, message, data }
}

export function pageOk(list, total, page = 1, pageSize = 10) {
  return { code: 200, message: 'success', data: { list, total, page, page_size: pageSize } }
}

export function err(message = '操作失败', code = 400) {
  return { code, message, data: null }
}

// ==================== 模拟延迟 ====================
export function delay(ms = 300) {
  return new Promise(r => setTimeout(r, ms + Math.random() * 200))
}
