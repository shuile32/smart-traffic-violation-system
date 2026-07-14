export async function batchRejectCases(ids, reason, rejectFn) {
  const normalizedReason = String(reason ?? '').trim()
  if (!normalizedReason) throw new TypeError('驳回原因不能为空')

  const uniqueIds = [...new Set(ids)]
  const results = await Promise.allSettled(
    uniqueIds.map(id => rejectFn(id, { reject_reason: normalizedReason }))
  )
  const succeededIds = []
  const failedIds = []

  results.forEach((result, index) => {
    const target = result.status === 'fulfilled' ? succeededIds : failedIds
    target.push(uniqueIds[index])
  })
  return { succeededIds, failedIds }
}
