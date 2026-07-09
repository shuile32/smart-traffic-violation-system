<template>
  <el-container class="review-layout">
    <!-- 顶栏导航 -->
    <el-header class="top-header">
      <div class="header-left">
        <span class="logo-text">🚦 交通违章智能管理平台</span>
      </div>
      <div class="header-nav">
        <el-menu mode="horizontal" :default-active="activeTopMenu" router :ellipsis="false" class="top-menu">
          <el-menu-item index="/review/workbench">案件审核</el-menu-item>
          <el-menu-item index="/review/violations">违章记录</el-menu-item>
          <el-menu-item index="/review/upload">证据上传</el-menu-item>
          <el-menu-item index="/stats">统计分析</el-menu-item>
          <el-menu-item v-if="userStore.role === 'admin'" index="/admin/users">系统管理</el-menu-item>
        </el-menu>
      </div>
      <div class="header-right">
        <el-icon class="theme-toggle" :size="20" @click="themeStore.isDark = !themeStore.isDark">
          <Moon v-if="themeStore.isDark" />
          <Sunny v-else />
        </el-icon>
        <el-badge :value="pendingCount" :hidden="!pendingCount" class="pending-badge">
          <el-icon :size="20"><Bell /></el-icon>
        </el-badge>
        <el-dropdown>
          <span class="user-info">
            {{ userStore.userInfo?.username || '工作人员' }}
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="router.push('/review/profile')">
                <el-icon><User /></el-icon>个人信息
              </el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">
                <el-icon><SwitchButton /></el-icon>退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <!-- 主内容 -->
    <el-main class="main-content">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'
import { Moon, Sunny } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const themeStore = useThemeStore()
const pendingCount = ref(5)

const activeTopMenu = computed(() => {
  if (route.path.startsWith('/stats')) return '/stats'
  if (route.path.startsWith('/review')) return '/' + route.path.split('/').slice(0, 2).join('/')
  return '/review/workbench'
})

function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', { type: 'warning' }).then(() => {
    userStore.logout()
    router.push('/login')
  })
}
</script>

<style scoped>
.review-layout { height: 100vh; display: flex; flex-direction: column; }
.top-header {
  display: flex;
  align-items: center;
  padding: 0 20px;
  background: var(--header-bg);
  border-bottom: 1px solid var(--border-color);
  height: 60px;
  z-index: 100;
}
.header-left { margin-right: 40px; }
.logo-text { font-size: 18px; font-weight: bold; color: var(--text-color); }
.header-nav { flex: 1; }
.top-menu { border-bottom: none !important; }
.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}
.pending-badge { cursor: pointer; }
.theme-toggle { cursor: pointer; color: var(--text-secondary); }
.theme-toggle:hover { color: var(--text-color); }
.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--text-color);
}
.main-content {
  flex: 1;
  background: var(--bg-color);
  padding: 20px;
  overflow-y: auto;
}
</style>
