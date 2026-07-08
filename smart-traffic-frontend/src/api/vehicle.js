import request from './request'

// 车辆列表
export const getVehicles = (params) => request.get('/vehicles', { params })
// 车辆详情
export const getVehicle = (id) => request.get(`/vehicles/${id}`)
// 新增车辆
export const createVehicle = (data) => request.post('/vehicles', data)
// 更新车辆
export const updateVehicle = (id, data) => request.put(`/vehicles/${id}`, data)
// 删除车辆
export const deleteVehicle = (id) => request.delete(`/vehicles/${id}`)
// 车辆归属记录
export const getVehicleOwners = (id) => request.get(`/vehicles/${id}/owners`)
