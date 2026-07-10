import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import {
  buildApprovePayload,
  buildRejectPayload,
  buildViolationQuery,
  caseAiFallbackText,
  fetchAllCitizenCases,
  getCaseReviewOpinion,
  getStatisticsCards,
  isApprovedCaseStatus,
  mapNamedSeries,
  reportPathForRoute,
  summarizeCitizenOverview
} from '../src/utils/contracts.js'

test('maps backend statistics fields without multiplying percentages', () => {
  const cards = getStatisticsCards({
    total_cases: 3,
    total_violations: 2,
    approve_rate: 66.7,
    reject_rate: 33.3,
    pending_count: 1,
    today_new: 2
  })

  assert.deepEqual(cards.map(card => card.value), [3, 2, '66.7%', '33.3%', 1, 2])
})

test('maps name/value statistic series', () => {
  assert.deepEqual(
    mapNamedSeries({ items: [{ name: '超速', value: 2 }] }),
    [{ name: '超速', value: 2 }]
  )
})

test('uses backend violation query names', () => {
  assert.deepEqual(buildViolationQuery({
    plate: '粤A',
    type: '超速',
    location: '人民路',
    dateRange: ['2026-07-01', '2026-07-10']
  }, 2, 10), {
    page: 2,
    page_size: 10,
    plate_no: '粤A',
    violation_type: '超速',
    location_text: '人民路',
    start_time: '2026-07-01T00:00:00',
    end_time: '2026-07-10T23:59:59'
  })
})

test('builds exact review request bodies', () => {
  const form = {
    action: 'approve',
    plate_no: '粤A1',
    violation_type: '超速',
    fine_amount: 200,
    points: 3,
    review_opinion: '证据清晰'
  }

  assert.deepEqual(buildApprovePayload(form), {
    plate_no: '粤A1',
    violation_type: '超速',
    fine_amount: 200,
    points: 3,
    review_opinion: '证据清晰'
  })
  assert.deepEqual(buildRejectPayload(form), { reject_reason: '证据清晰' })
})

test('keeps admin report navigation inside admin routes', () => {
  assert.equal(reportPathForRoute('/admin/stats'), '/admin/stats/report')
  assert.equal(reportPathForRoute('/stats'), '/stats/report')
})

test('describes missing AI results according to case processing state', () => {
  assert.equal(caseAiFallbackText('detecting'), 'AI 处理中...')
  assert.equal(caseAiFallbackText('ai_reviewing'), 'AI 处理中...')

  for (const status of ['uploaded', 'pending_human_review', 'approved', 'rejected', 'notified']) {
    assert.equal(caseAiFallbackText(status), '暂无 AI 结果')
  }
})

test('maps notified cases and nested review results to the approved terminal view', () => {
  assert.equal(isApprovedCaseStatus('approved'), true)
  assert.equal(isApprovedCaseStatus('notified'), true)
  assert.equal(isApprovedCaseStatus('rejected'), false)
  assert.equal(
    getCaseReviewOpinion({ review: { review_opinion: '证据清晰' } }),
    '证据清晰'
  )
  assert.equal(getCaseReviewOpinion({}), '')
})

test('summarizes citizen overview from real API payloads', () => {
  assert.deepEqual(summarizeCitizenOverview(
    { total: 2 },
    { total: 3, items: [{ reward: 10 }, { reward: null }, { reward: 5 }] },
    { total: 1 }
  ), { violations: 2, reports: 3, rewards: 15, vehicles: 1 })
})

test('includes rewards from every citizen case page when total exceeds 100', async () => {
  const requestedPages = []
  const cases = await fetchAllCitizenCases(async ({ page }) => {
    requestedPages.push(page)
    if (page === 1) {
      return {
        total: 101,
        page: 1,
        page_size: 100,
        items: Array.from({ length: 100 }, () => ({ reward: 1 }))
      }
    }
    return { total: 101, page: 2, page_size: 100, items: [{ reward: 5 }] }
  })

  assert.deepEqual(requestedPages, [1, 2])
  assert.deepEqual(
    summarizeCitizenOverview({}, cases, {}),
    { violations: 0, reports: 101, rewards: 105, vehicles: 0 }
  )
})

test('does not fabricate citizen announcements without a backend API', async () => {
  const source = await readFile(new URL('../src/views/citizen/Home.vue', import.meta.url), 'utf8')

  assert.doesNotMatch(source, /系统升级通知/)
  assert.match(source, /const announcements = ref\(\[\]\)/)
})
