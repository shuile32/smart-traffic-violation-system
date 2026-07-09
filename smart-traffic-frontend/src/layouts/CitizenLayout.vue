<template>
  <el-container class="citizen-layout">
    <el-header class="header">
      <div class="header-left">
        <h3 @click="router.push('/citizen/home')" style="cursor:pointer">🚦 交通违章查询平台</h3>
      </div>
      <el-menu mode="horizontal" :default-active="activeMenu" router class="nav-menu">
        <el-menu-item index="/citizen/home">首页</el-menu-item>
        <el-menu-item index="/citizen/my-violations">我的违章</el-menu-item>
        <el-menu-item index="/citizen/report">随手拍举报</el-menu-item>
        <el-menu-item index="/citizen/my-reports">举报进度</el-menu-item>
        <el-menu-item index="/citizen/vehicles">车辆绑定</el-menu-item>
      </el-menu>
      <div class="header-right">
        <el-icon class="theme-toggle" :size="20" @click="themeStore.isDark = !themeStore.isDark">
          <Moon v-if="themeStore.isDark" />
          <Sunny v-else />
        </el-icon>
        <el-dropdown>
          <span class="user-info">
            {{ userStore.userInfo?.username || '用户' }}
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="router.push('/citizen/profile')">
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
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'
import { Moon, Sunny } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const themeStore = useThemeStore()

const activeMenu = computed(() => route.path)

function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    type: 'warning'
  }).then(() => {
    userStore.logout()
    router.push('/login')
  })
}
</script>

<style scoped>
.citizen-layout { min-height: 100vh; }
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--header-bg);
  border-bottom: 1px solid var(--border-color);
  padding: 0 40px;
}
.header-left h3 { color: var(--text-color); }
.nav-menu { border-bottom: none !important; flex: 1; justify-content: center; }
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.theme-toggle { cursor: pointer; color: var(--text-secondary); }
.theme-toggle:hover { color: var(--text-color); }
.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}
.el-main {
  min-height: calc(100vh - 60px);
  background: var(--bg-color);
  padding: 20px 40px;
}
</style>
