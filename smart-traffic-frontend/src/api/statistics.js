/**
 * 统计分析 API — 对齐 API接口规范文档 v2.0 §6
 */
import { ok, delay, mockStatistics } from './mock'
import request from './request'

// ==================== Mock API (默认使用) ====================
export const getStatisticsOverview = async () => { await delay(); return ok(mockStatistics.overview) }
export const getStatisticsByLocation = async () => { await delay(); return ok(mockStatistics.regionRank) }
export const getStatisticsByTime = async () => { await delay(); return ok(mockStatistics.trend) }
export const getStatisticsByType = async () => { await delay(); return ok(mockStatistics.typeRatio) }

export const getOverview = async () => { await delay(); return ok(mockStatistics.overview) }
export const getTrend = async () => { await delay(); return ok(mockStatistics.trend) }
export const getTypeRatio = async () => { await delay(); return ok(mockStatistics.typeRatio) }
export const getRegionRank = async () => { await delay(); return ok(mockStatistics.regionRank) }
