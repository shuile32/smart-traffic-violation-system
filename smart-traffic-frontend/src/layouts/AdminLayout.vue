<template>
  <el-container class="admin-layout">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="aside">
      <div class="logo" @click="router.push('/admin/stats')">
        <span v-if="!isCollapse">🚦 交通违章管理</span>
        <span v-else>🚦</span>
      </div>

      <div class="sidebar-menu">
        <div :class="['menu-item', { active: isActive('/admin/stats') }]" @click="navigate('/admin/stats')">
          <el-icon><TrendCharts /></el-icon>
          <span v-if="!isCollapse">统计分析</span>
        </div>

        <div :class="['menu-item', { active: isActive('/review/workbench') }]" @click="navigate('/review/workbench')">
          <el-icon><Checked /></el-icon>
          <span v-if="!isCollapse">案件审核</span>
        </div>

        <div class="menu-group-title" v-if="!isCollapse">用户管理</div>
        <div :class="['menu-item sub', { active: isActive('/admin/users') }]" @click="navigate('/admin/users')">
          <span v-if="!isCollapse">用户列表</span>
        </div>
        <div :class="['menu-item sub', { active: isActive('/admin/roles') }]" @click="navigate('/admin/roles')">
          <span v-if="!isCollapse">角色权限</span>
        </div>

        <div :class="['menu-item', { active: isActive('/admin/cameras') }]" @click="navigate('/admin/cameras')">
          <el-icon><VideoCamera /></el-icon>
          <span v-if="!isCollapse">摄像头管理</span>
        </div>

        <div class="menu-group-title" v-if="!isCollapse">系统配置</div>
        <div :class="['menu-item sub', { active: isActive('/admin/rules') }]" @click="navigate('/admin/rules')">
          <span v-if="!isCollapse">违章规则</span>
        </div>
        <div :class="['menu-item sub', { active: isActive('/admin/sms-templates') }]" @click="navigate('/admin/sms-templates')">
          <span v-if="!isCollapse">短信模板</span>
        </div>

        <div :class="['menu-item', { active: isActive('/admin/logs') }]" @click="navigate('/admin/logs')">
          <el-icon><Document /></el-icon>
          <span v-if="!isCollapse">操作日志</span>
        </div>
      </div>
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
import { ref } from 'vue'
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
function isActive(path) {
  return route.path === path || route.path.startsWith(path + '/')
}

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

.sidebar-menu { padding: 8px 0; }
.menu-item {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 20px; color: #bfcbd9; cursor: pointer;
  font-size: 14px; transition: all 0.2s;
}
.menu-item:hover { background: rgba(255,255,255,0.08); color: #fff; }
.menu-item.active { color: #409EFF; background: rgba(64,158,255,0.1); }
.menu-item.sub { padding-left: 48px; font-size: 13px; }
.menu-group-title {
  padding: 12px 20px 4px; font-size: 12px;
  color: rgba(255,255,255,0.4); text-transform: uppercase;
}
</style>
