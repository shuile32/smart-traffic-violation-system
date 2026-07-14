import * as XLSX from 'xlsx'

export function exportToExcel(data, columns, filename = 'export') {
  const header = columns.map(column => column.label)
  const rows = data.map(row => columns.map(column => {
    const value = row[column.key]
    return value === undefined || value === null ? '' : String(value)
  }))
  const sheet = XLSX.utils.aoa_to_sheet([header, ...rows])
  sheet['!cols'] = columns.map(column => ({ wch: column.width || 20 }))

  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, sheet, 'Sheet1')
  XLSX.writeFile(workbook, `${filename}.xlsx`)
}

export function formatExportTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : ''
}
