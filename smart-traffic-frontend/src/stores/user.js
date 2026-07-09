import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getUserInfo } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)
  const role = ref(localStorage.getItem('role') || '')

  // v2.0 角色: citizen(市民) / reviewer(审核员) / admin(超级管理员)
  const homePath = computed(() => {
    if (role.value === 'citizen') return '/citizen/home'
    if (role.value === 'reviewer') return '/review/workbench'
    return '/admin/stats'
  })

  async function login(credentials) {
    const res = await loginApi(credentials)
    // v2.0 响应: { access_token, token_type, user: { id, username, role } }
    const data = res.data
    token.value = data.access_token || data.token
    role.value = data.user?.role || data.role
    userInfo.value = data.user || data
    localStorage.setItem('token', token.value)
    localStorage.setItem('role', role.value)
    return res
  }

  async function restoreLoginState() {
    if (!token.value) return
    // 优先使用本地缓存，避免 mock 开发模式下请求后端
    const cachedUserInfo = localStorage.getItem('userInfo')
    if (cachedUserInfo) {
      try {
        userInfo.value = JSON.parse(cachedUserInfo)
        role.value = userInfo.value.role || localStorage.getItem('role') || ''
        return
      } catch { /* ignore */ }
    }
    try {
      const res = await getUserInfo()
      userInfo.value = res.data
      role.value = res.data.role
      localStorage.setItem('role', res.data.role)
      localStorage.setItem('userInfo', JSON.stringify(res.data))
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    role.value = ''
    localStorage.clear()
  }

  return { token, userInfo, role, homePath, login, restoreLoginState, logout }
})
