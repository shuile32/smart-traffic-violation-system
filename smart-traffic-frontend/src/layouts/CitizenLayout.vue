<template>
  <el-container class="app-layout citizen-layout">
    <el-aside :width="isCollapse ? '64px' : '210px'" class="citizen-aside">
      <button type="button" class="brand" @click="router.push('/citizen/home')">
        <el-icon :size="22"><LocationFilled /></el-icon>
        <span v-if="!isCollapse">市民交通服务</span>
      </button>
      <el-menu :default-active="activeMenu" router :collapse="isCollapse" :collapse-transition="false" class="sidebar-menu">
        <el-menu-item index="/citizen/home"><el-icon><HomeFilled /></el-icon><template #title>首页</template></el-menu-item>
        <el-menu-item index="/citizen/my-violations"><el-icon><WarningFilled /></el-icon><template #title>我的违章</template></el-menu-item>
        <el-menu-item index="/citizen/report"><el-icon><Camera /></el-icon><template #title>随手拍举报</template></el-menu-item>
        <el-menu-item index="/citizen/my-reports"><el-icon><List /></el-icon><template #title>举报进度</template></el-menu-item>
        <el-menu-item index="/citizen/vehicles"><el-icon><Van /></el-icon><template #title>车辆绑定</template></el-menu-item>
      </el-menu>
    </el-aside>

    <el-container class="layout-body">
      <el-header class="app-header">
        <div class="header-context">
          <el-tooltip :content="isCollapse ? '展开菜单' : '收起菜单'" placement="bottom">
            <el-button text circle aria-label="切换侧边栏" @click="isCollapse = !isCollapse"><el-icon :size="20"><Expand v-if="isCollapse" /><Fold v-else /></el-icon></el-button>
          </el-tooltip>
          <span class="page-title">{{ route.meta.title || '市民服务平台' }}</span>
        </div>
        <HeaderActions profile-path="/citizen/profile" default-name="市民用户" />
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
import { Camera, Expand, Fold, HomeFilled, List, LocationFilled, Van, WarningFilled } from '@element-plus/icons-vue'
import BackToTop from '@/components/BackToTop.vue'
import HeaderActions from '@/components/HeaderActions.vue'
import { useResponsiveSidebar } from '@/composables/useResponsiveSidebar'

const router = useRouter()
const route = useRoute()
const { isCollapse } = useResponsiveSidebar()
const mainRef = ref(null)
const mainElement = computed(() => mainRef.value?.$el || mainRef.value)
const activeMenu = computed(() => route.path)
</script>

<style scoped>
.app-layout { height: 100vh; min-width: 0; }
.citizen-aside { display: flex; flex-direction: column; overflow: hidden; background: var(--header-bg); border-right: 1px solid var(--border-color); transition: width 0.2s; }
.brand { display: flex; align-items: center; justify-content: center; gap: 10px; width: 100%; height: 60px; flex: 0 0 60px; padding: 0 10px; color: var(--text-color); font: inherit; font-weight: 600; background: transparent; border: 0; border-bottom: 1px solid var(--border-color); cursor: pointer; white-space: nowrap; }
.sidebar-menu { flex: 1; overflow-y: auto; border-right: 0; background: transparent; }
.sidebar-menu :deep(.el-menu-item.is-active) { color: var(--el-color-primary); background: var(--el-color-primary-light-9); }
.layout-body { min-width: 0; }
.app-header { display: flex; align-items: center; justify-content: space-between; gap: 16px; height: 60px; padding: 0 20px; background: var(--header-bg); border-bottom: 1px solid var(--border-color); }
.header-context { display: flex; align-items: center; min-width: 0; gap: 10px; }
.page-title { overflow: hidden; color: var(--text-color); font-size: 15px; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.app-main { position: relative; min-width: 0; padding: 16px; overflow: auto; background: var(--bg-color); }
@media (max-width: 720px) { .app-header { padding: 0 10px; } .page-title { display: none; } .app-main { padding: 12px; } }
</style>
