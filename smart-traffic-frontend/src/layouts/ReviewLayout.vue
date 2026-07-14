<template>
  <el-container class="review-layout">
    <!-- 左侧侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="aside">
      <div class="logo" @click="router.push('/review/workbench')">
        <span v-if="!isCollapse">🚦 交管审核平台</span>
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
        <el-menu-item index="/review/upload" @click="nav('/review/upload')">
          <el-icon><Upload /></el-icon>
          <template #title>证据上传</template>
        </el-menu-item>

        <el-menu-item index="/review/workbench" @click="nav('/review/workbench')">
          <el-icon><Checked /></el-icon>
          <template #title>案件审核</template>
        </el-menu-item>

        <el-menu-item index="/review/violations" @click="nav('/review/violations')">
          <el-icon><List /></el-icon>
          <template #title>违章列表</template>
        </el-menu-item>

        <el-menu-item index="/stats" @click="nav('/stats')">
          <el-icon><TrendCharts /></el-icon>
          <template #title>统计分析</template>
        </el-menu-item>

      </el-menu>
    </el-aside>

    <!-- 右侧主内容 -->
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
        <HeaderActions profile-path="/review/profile" default-name="工作人员" />
      </el-header>

      <el-main class="main-content">
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
import HeaderActions from '@/components/HeaderActions.vue'
import BackToTop from '@/components/BackToTop.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const isCollapse = ref(false)

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

const activeMenu = computed(() => {
  const p = route.path
  if (p.startsWith('/stats')) return p
  if (p.startsWith('/review/case/')) return '/review/workbench'
  return p
})

const breadcrumbMap = {
  '/review/case/:id': ['案件审核'],
  '/stats/report': ['统计分析']
}

const breadcrumbs = computed(() => {
  const items = [{ title: '首页', path: '/review/workbench' }]
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
</script>

<style scoped>
.review-layout { height: 100vh; }
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
  font-size: 17px;
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
.sidebar-menu .el-menu-item:hover {
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
.collapse-btn { font-size: 20px; cursor: pointer; }
.breadcrumb { line-height: 1; }
.breadcrumb :deep(.el-breadcrumb__separator) { color: var(--text-secondary); }
.breadcrumb :deep(.el-breadcrumb__inner) { color: var(--text-secondary); font-size: 14px; }
.breadcrumb :deep(.el-breadcrumb__inner.is-link:hover) { color: var(--text-color); }
.breadcrumb :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) { color: var(--text-color); font-weight: 500; }
.main-content {
  background: var(--bg-color);
  padding: 20px;
  overflow-y: auto;
  position: relative;
}
</style>
