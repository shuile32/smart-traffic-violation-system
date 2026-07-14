export async function fetchAllPages(fetchPage, params = {}, pageSize = 100) {
  const rows = []
  for (let page = 1; ; page += 1) {
    const response = await fetchPage({ ...params, page, page_size: pageSize })
    const payload = response.data ?? response
    const items = payload.items ?? []
    rows.push(...items)
    if (rows.length >= (payload.total ?? rows.length) || items.length === 0) return rows
  }
}
