export function getChartTheme(isDark) {
  return isDark
    ? {
        text: '#e5eaf3',
        secondaryText: '#a3a6ad',
        axis: '#8d9095',
        grid: '#3a3d43',
        tooltipBackground: '#1f2329',
        tooltipBorder: '#4c4d4f'
      }
    : {
        text: '#303133',
        secondaryText: '#606266',
        axis: '#909399',
        grid: '#e4e7ed',
        tooltipBackground: '#ffffff',
        tooltipBorder: '#dcdfe6'
      }
}
