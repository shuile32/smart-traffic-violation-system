/**
 * 系统管理 API — 连接真实后端
 */
import request from './request'

// ===================== 用户管理 =====================
export const getUsers = (params) => request.get('/admin/users', { params })
export const getUser = (id) => request.get(`/admin/users/${id}`)
export const createUser = (data) => request.post('/admin/users', data)
export const updateUser = (id, data) => request.patch(`/admin/users/${id}`, data)

// 兼容旧版接口名
export const updateUserRole = (id, data) => request.patch(`/admin/users/${id}`, data)
export const toggleUserStatus = (id, data) => request.patch(`/admin/users/${id}`, data)

// ===================== 摄像头管理 =====================
export const getCameras = (params) => request.get('/admin/cameras', { params })
export const getCamera = (id) => request.get(`/admin/cameras/${id}`)
export const createCamera = (data) => request.post('/admin/cameras', data)
export const updateCamera = (id, data) => request.patch(`/admin/cameras/${id}`, data)

// API Key 管理
export const getApiKeys = (cameraId) => request.get(`/admin/cameras/${cameraId}/keys`)
export const createApiKey = (cameraId, data) => request.post(`/admin/cameras/${cameraId}/keys`, data)
export const revokeApiKey = (cameraId, keyId) => request.post(`/admin/cameras/${cameraId}/keys/${keyId}/revoke`)

// ===================== 违章规则配置 =====================
export const getViolationRules = (params) => request.get('/admin/rules', { params })
export const createViolationRule = (data) => request.post('/admin/rules', data)
export const updateViolationRule = (id, data) => request.patch(`/admin/rules/${id}`, data)

// ===================== 操作日志 =====================
export const getAuditLogs = (params) => request.get('/admin/audit-logs', { params })

// ===================== 奖励管理 =====================
export const getRewards = (params) => request.get('/admin/rewards', { params })

// ===================== 通知模块 =====================
export const getNotifications = (params) => request.get('/notifications', { params })
export const getNotificationsByViolation = (violationId) => request.get(`/violations/${violationId}/notifications`)

// ===================== 角色管理 (后端暂无端点，保留 stub 兼容旧视图) =====================
export const getRoles = async () => ({ code: 200, data: [], message: 'success' })
export const createRole = async (data) => ({ code: 200, data: { ...data }, message: 'success' })
export const updateRole = async (id, data) => ({ code: 200, data: { id, ...data }, message: 'success' })
export const deleteRole = async (id) => ({ code: 200, data: { id }, message: 'success' })
export const updateRolePermissions = async (id, data) => ({ code: 200, data: { id, ...data }, message: 'success' })
