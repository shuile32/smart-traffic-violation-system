<template>
  <el-container class="app-layout review-layout">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="app-aside">
      <button type="button" class="brand" @click="nav('/review/workbench')">
        <el-icon :size="22"><LocationFilled /></el-icon>
        <span v-if="!isCollapse">交管审核平台</span>
      </button>
      <el-menu :default-active="activeMenu" :collapse="isCollapse" :collapse-transition="false" class="sidebar-menu">
        <el-menu-item index="/review/workbench" @click="nav('/review/workbench')"><el-icon><Checked /></el-icon><template #title>案件审核</template></el-menu-item>
        <el-menu-item index="/review/upload" @click="nav('/review/upload')"><el-icon><Upload /></el-icon><template #title>证据上传</template></el-menu-item>
        <el-menu-item index="/review/violations" @click="nav('/review/violations')"><el-icon><List /></el-icon><template #title>违章记录</template></el-menu-item>
        <el-menu-item index="/stats" @click="nav('/stats')"><el-icon><TrendCharts /></el-icon><template #title>统计分析</template></el-menu-item>
      </el-menu>
    </el-aside>

    <el-container class="layout-body">
      <el-header class="app-header">
        <div class="header-context">
          <el-tooltip :content="isCollapse ? '展开菜单' : '收起菜单'" placement="bottom">
            <el-button text circle aria-label="切换侧边栏" @click="isCollapse = !isCollapse"><el-icon :size="20"><Expand v-if="isCollapse" /><Fold v-else /></el-icon></el-button>
          </el-tooltip>
          <el-breadcrumb separator="/" class="breadcrumbs">
            <el-breadcrumb-item v-for="item in breadcrumbItems" :key="`${item.label}-${item.path}`" :to="item.path || undefined">{{ item.label }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <HeaderActions :profile-path="profilePath" role-label="审核员" role-tag-type="warning" default-name="工作人员" />
      </el-header>

      <el-main ref="mainRef" class="app-main">
        <router-view v-slot="{ Component, route: viewRoute }">
          <KeepAlive>
            <component :is="Component" v-if="viewRoute.meta.keepAlive" :key="viewRoute.name" />
          </KeepAlive>
          <component :is="Component" v-if="!viewRoute.meta.keepAlive" :key="viewRoute.fullPath" />
        </router-view>
        <BackToTop :target="mainElement" />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Checked, Expand, Fold, List, LocationFilled, TrendCharts, Upload } from '@element-plus/icons-vue'
import BackToTop from '@/components/BackToTop.vue'
import HeaderActions from '@/components/HeaderActions.vue'
import { useResponsiveSidebar } from '@/composables/useResponsiveSidebar'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const { isCollapse } = useResponsiveSidebar()
const mainRef = ref(null)
const mainElement = computed(() => mainRef.value?.$el || mainRef.value)
const profilePath = computed(() => userStore.role === 'admin' ? '/admin/profile' : '/review/profile')
const activeMenu = computed(() => {
  if (route.path.startsWith('/stats')) return '/stats'
  if (route.path.startsWith('/review/case/')) return '/review/workbench'
  return route.path
})
const breadcrumbItems = computed(() => {
  const home = route.path.startsWith('/stats') ? '/stats' : '/review/workbench'
  const items = [{ label: '审核平台', path: home }]
  if (route.path.startsWith('/review/case/')) items.push({ label: '案件审核', path: '/review/workbench' })
  if (route.meta.title && route.path !== home) items.push({ label: route.meta.title, path: '' })
  return items
})
function nav(path) { if (route.path !== path) router.push(path) }
</script>

<style scoped>
.app-layout { height: 100vh; min-width: 0; }
.app-aside { display: flex; flex-direction: column; overflow: hidden; background: var(--sidebar-bg); transition: width 0.2s; }
.brand { display: flex; align-items: center; justify-content: center; gap: 10px; width: 100%; height: 60px; flex: 0 0 60px; padding: 0 10px; color: #fff; font: inherit; font-weight: 600; background: transparent; border: 0; cursor: pointer; white-space: nowrap; }
.sidebar-menu { flex: 1; overflow-y: auto; border-right: 0; background: transparent; }
.sidebar-menu :deep(.el-menu-item) { color: #c8d1d8; }
.sidebar-menu :deep(.el-menu-item:hover) { background: rgba(255,255,255,0.08); }
.sidebar-menu :deep(.el-menu-item.is-active) { color: #fff; background: rgba(64,158,255,0.24); }
.layout-body { min-width: 0; }
.app-header { display: flex; align-items: center; justify-content: space-between; gap: 16px; height: 60px; padding: 0 20px; background: var(--header-bg); border-bottom: 1px solid var(--border-color); }
.header-context { display: flex; align-items: center; min-width: 0; gap: 10px; }
.breadcrumbs :deep(.el-breadcrumb__inner) { color: var(--text-secondary); }
.breadcrumbs :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) { color: var(--text-color); font-weight: 600; }
.app-main { position: relative; min-width: 0; padding: 20px; overflow: auto; background: var(--bg-color); }
@media (max-width: 720px) { .app-header { padding: 0 10px; } .breadcrumbs { display: none; } .app-main { padding: 12px; } }
</style>
