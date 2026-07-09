import request from './request'

// 驾驶员列表
export const getDrivers = (params) => request.get('/drivers', { params })
// 驾驶员详情
export const getDriver = (id) => request.get(`/drivers/${id}`)
// 新增驾驶员
export const createDriver = (data) => request.post('/drivers', data)
// 更新驾驶员
export const updateDriver = (id, data) => request.put(`/drivers/${id}`, data)
// 删除驾驶员
export const deleteDriver = (id) => request.delete(`/drivers/${id}`)
// 驾驶证信息
export const getDriverLicense = (id) => request.get(`/drivers/${id}/license`)
// 扣分记录
export const getPenaltyPoints = (id) => request.get(`/drivers/${id}/points`)
// 扣分操作
export const deductPoints = (id, data) => request.post(`/drivers/${id}/points/deduct`, data)
