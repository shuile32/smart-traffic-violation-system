<template>
  <el-container class="admin-layout">
    <!-- 左侧侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="aside">
      <div class="logo" @click="router.push('/admin/stats')">
        <span v-if="!isCollapse">🚦 交通违章管理</span>
        <span v-else>🚦</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        background-color="transparent"
        text-color="#C8DDE4"
        active-text-color="#A2D9F0"
        class="sidebar-menu"
      >
        <!-- 违章管理 -->
        <el-sub-menu index="violation-group">
          <template #title>
            <el-icon><WarningFilled /></el-icon>
            <span>违章管理</span>
          </template>
          <el-menu-item index="/admin/violations/upload" @click="nav('/admin/violations/upload')">证据上传</el-menu-item>
          <el-menu-item index="/admin/violations/review" @click="nav('/admin/violations/review')">案件审核</el-menu-item>
          <el-menu-item index="/admin/violations" @click="nav('/admin/violations')">违章列表</el-menu-item>
          <el-menu-item index="/admin/stats" @click="nav('/admin/stats')">统计分析</el-menu-item>
        </el-sub-menu>

        <!-- 车辆管理 -->
        <el-menu-item index="/admin/vehicles" @click="nav('/admin/vehicles')">
          <el-icon><Van /></el-icon>
          <template #title>车辆管理</template>
        </el-menu-item>

        <!-- 用户管理 -->
        <el-menu-item index="/admin/users" @click="nav('/admin/users')">
          <el-icon><UserFilled /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>

        <!-- 设备管理 -->
        <el-menu-item index="/admin/cameras" @click="nav('/admin/cameras')">
          <el-icon><VideoCamera /></el-icon>
          <template #title>摄像头管理</template>
        </el-menu-item>

        <!-- 系统配置 -->
        <el-sub-menu index="config-group">
          <template #title>
            <el-icon><Tools /></el-icon>
            <span>系统配置</span>
          </template>
          <el-menu-item index="/admin/rules" @click="nav('/admin/rules')">违章规则</el-menu-item>
          <el-menu-item index="/admin/announcements" @click="nav('/admin/announcements')">公告管理</el-menu-item>
        </el-sub-menu>

        <!-- 系统维护 -->
        <el-sub-menu index="system-group">
          <template #title>
            <el-icon><Monitor /></el-icon>
            <span>系统维护</span>
          </template>
          <el-menu-item index="/admin/logs" @click="nav('/admin/logs')">系统日志</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse" /><Expand v-else />
          </el-icon>
          <el-breadcrumb class="breadcrumb">
            <el-breadcrumb-item
              v-for="(item, index) in breadcrumbs"
              :key="index"
              :to="item.path || undefined"
            >
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <AnnouncementBell />
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
        <router-view v-slot="{ Component, route: r }">
          <Transition name="page-fade" mode="out-in">
            <keep-alive :include="cachedViews">
              <component :is="Component" :key="r.path" />
            </keep-alive>
          </Transition>
        </router-view>
        <BackToTop />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'
import BackToTop from '@/components/BackToTop.vue'
import AnnouncementBell from '@/components/AnnouncementBell.vue'
import {
  WarningFilled, Van, UserFilled, VideoCamera, Tools, Monitor,
  Fold, Expand, Moon, Sunny, ArrowDown
} from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const themeStore = useThemeStore()
const isCollapse = ref(false)

// keep-alive 白名单从路由 meta 读取
const cachedViews = computed(() => {
  const names = []
  const collect = (routes) => {
    for (const r of routes) {
      if (r.children) collect(r.children)
      if (r.meta?.keepAlive && r.name) names.push(r.name)
    }
  }
  collect(router.options.routes)
  return names
})

const activeMenu = computed(() => route.path)

const breadcrumbMap = {
  '/admin/violations/upload': ['违章管理'],
  '/admin/violations/review': ['违章管理'],
  '/admin/violations': ['违章管理'],
  '/admin/violations/:id': ['违章管理'],
  '/admin/stats/report': ['统计分析'],
  '/admin/rules': ['系统配置'],
  '/admin/announcements': ['系统配置'],
  '/admin/logs': ['系统维护']
}

const breadcrumbs = computed(() => {
  const items = [{ title: '首页', path: '/admin/stats' }]
  let extra = null
  for (const [path, names] of Object.entries(breadcrumbMap)) {
    const regex = new RegExp('^' + path.replace(/:id/, '[^/]+') + '$')
    if (regex.test(route.path)) {
      extra = names
      break
    }
  }
  if (extra) {
    for (const name of extra) {
      items.push({ title: name, path: '' })
    }
  }
  items.push({ title: route.meta.title || '', path: '' })
  return items
})

function nav(path) {
  if (route.path !== path) router.push(path).catch(() => {})
}

function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', { type: 'warning' }).then(() => {
    localStorage.removeItem('access_token')
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
  display: flex;
  flex-direction: column;
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
  flex-shrink: 0;
}
.sidebar-menu {
  border-right: none !important;
  flex: 1;
  overflow-y: auto;
}
.sidebar-menu .el-menu-item {
  height: 48px;
  line-height: 48px;
}
.sidebar-menu .el-sub-menu .el-menu-item {
  height: 44px;
  line-height: 44px;
  min-width: auto;
}
.sidebar-menu .el-menu-item:hover,
.sidebar-menu .el-sub-menu__title:hover {
  background: rgba(255, 255, 255, 0.08) !important;
}
.sidebar-menu .el-menu-item.is-active {
  background: rgba(162, 217, 240, 0.15) !important;
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
.header-right { display: flex; align-items: center; gap: 12px; }
.collapse-btn { font-size: 20px; cursor: pointer; }
.theme-toggle { cursor: pointer; }
.user-info { display: flex; align-items: center; gap: 4px; cursor: pointer; }
.breadcrumb { line-height: 1; }
.breadcrumb :deep(.el-breadcrumb__separator) { color: var(--text-secondary); }
.breadcrumb :deep(.el-breadcrumb__inner) { color: var(--text-secondary); font-size: 14px; }
.breadcrumb :deep(.el-breadcrumb__inner.is-link:hover) { color: var(--text-color); }
.breadcrumb :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) { color: var(--text-color); font-weight: 500; }
.el-main {
  background: var(--bg-color);
  padding: 20px;
  position: relative;
}
</style>
