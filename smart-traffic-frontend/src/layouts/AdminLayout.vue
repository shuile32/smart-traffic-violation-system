<template>
  <el-container class="admin-layout">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="aside">
      <div class="logo" @click="router.push('/admin/stats')">
        <span v-if="!isCollapse">🚦 交通违章管理</span>
        <span v-else>🚦</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        :background-color="menuBg"
        :text-color="menuText"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/admin/stats" @click="navigate('/admin/stats')">
          <el-icon><TrendCharts /></el-icon>
          <span>统计分析</span>
        </el-menu-item>

        <el-menu-item index="/review/workbench" @click="navigate('/review/workbench')">
          <el-icon><Checked /></el-icon>
          <span>案件审核</span>
        </el-menu-item>

        <el-sub-menu index="user-group">
          <template #title>
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </template>
          <el-menu-item index="/admin/users" @click="navigate('/admin/users')">用户列表</el-menu-item>
          <el-menu-item index="/admin/roles" @click="navigate('/admin/roles')">角色权限</el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/admin/cameras" @click="navigate('/admin/cameras')">
          <el-icon><VideoCamera /></el-icon>
          <span>摄像头管理</span>
        </el-menu-item>

        <el-sub-menu index="config-group">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统配置</span>
          </template>
          <el-menu-item index="/admin/rules" @click="navigate('/admin/rules')">违章规则</el-menu-item>
          <el-menu-item index="/admin/sms-templates" @click="navigate('/admin/sms-templates')">短信模板</el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/admin/logs" @click="navigate('/admin/logs')">
          <el-icon><Document /></el-icon>
          <span>操作日志</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse" /><Expand v-else />
          </el-icon>
          <span class="page-name">{{ route.meta.title }}</span>
        </div>
        <div class="header-right">
          <el-icon class="theme-toggle" :size="20" @click="themeStore.isDark = !themeStore.isDark">
            <Moon v-if="themeStore.isDark" />
            <Sunny v-else />
          </el-icon>
          <el-tag size="small" type="danger">超级管理员</el-tag>
          <el-dropdown>
            <span class="user-info">
              {{ userStore.userInfo?.username || 'admin' }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/admin/profile')">个人信息</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main>
        <router-view />
      </el-main>
    </el-container>
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
const isCollapse = ref(false)

function navigate(path) {
  if (route.path !== path) router.push(path)
}

const activeMenu = computed(() => {
  if (route.path.startsWith('/admin/stats')) return '/admin/stats'
  return route.path
})

const menuBg = computed(() => themeStore.isDark ? '#1a1a2e' : '#304156')
const menuText = computed(() => themeStore.isDark ? '#a0a0a0' : '#bfcbd9')

function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', { type: 'warning' }).then(() => {
    userStore.logout()
    router.push('/login')
  })
}
</script>

<style scoped>
.admin-layout { height: 100vh; }
.aside {
  background: var(--sidebar-bg);
  overflow: hidden;
  transition: width 0.3s;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  cursor: pointer;
  white-space: nowrap;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--header-bg);
  border-bottom: 1px solid var(--border-color);
  padding: 0 20px;
  height: 60px;
}
.header-left { display: flex; align-items: center; gap: 12px; }
.collapse-btn { font-size: 20px; cursor: pointer; }
.page-name { font-size: 16px; font-weight: 500; }
.header-right { display: flex; align-items: center; gap: 16px; }
.user-info { cursor: pointer; display: flex; align-items: center; gap: 4px; }
.theme-toggle { cursor: pointer; color: var(--text-secondary); }
.theme-toggle:hover { color: var(--text-color); }
.el-main { background: var(--bg-color); padding: 20px; }
</style>
