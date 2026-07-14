<template>
  <div class="header-actions">
    <AnnouncementBell />

    <el-tooltip :content="themeStore.isDark ? '切换浅色模式' : '切换深色模式'" placement="bottom">
      <el-button
        text
        circle
        class="icon-action"
        :aria-label="themeStore.isDark ? '切换浅色模式' : '切换深色模式'"
        @click="themeStore.isDark = !themeStore.isDark"
      >
        <el-icon :size="19">
          <Sunny v-if="themeStore.isDark" />
          <Moon v-else />
        </el-icon>
      </el-button>
    </el-tooltip>

    <el-tag v-if="roleLabel" size="small" :type="roleTagType">{{ roleLabel }}</el-tag>

    <el-dropdown trigger="click" @command="handleCommand">
      <button type="button" class="user-trigger">
        <span>{{ displayName }}</span>
        <el-icon><ArrowDown /></el-icon>
      </button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="profile">
            <el-icon><User /></el-icon>
            个人信息
          </el-dropdown-item>
          <el-dropdown-item command="logout" divided>
            <el-icon><SwitchButton /></el-icon>
            退出登录
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { ArrowDown, Moon, Sunny, SwitchButton, User } from '@element-plus/icons-vue'
import AnnouncementBell from '@/components/AnnouncementBell.vue'
import { useThemeStore } from '@/stores/theme'
import { useUserStore } from '@/stores/user'

const props = defineProps({
  profilePath: { type: String, required: true },
  roleLabel: { type: String, default: '' },
  roleTagType: { type: String, default: 'info' },
  defaultName: { type: String, default: '用户' }
})

const router = useRouter()
const themeStore = useThemeStore()
const userStore = useUserStore()
const displayName = computed(() => userStore.userInfo?.username || props.defaultName)

async function handleCommand(command) {
  if (command === 'profile') {
    await router.push(props.profilePath)
    return
  }
  if (command !== 'logout') return

  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '退出登录', { type: 'warning' })
  } catch {
    return
  }
  userStore.logout()
  await router.push('/login')
}
</script>

<style scoped>
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.icon-action {
  width: 36px;
  height: 36px;
  color: var(--text-secondary);
}

.user-trigger {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  max-width: 180px;
  padding: 8px 0;
  color: var(--text-color);
  font: inherit;
  background: transparent;
  border: 0;
  cursor: pointer;
}

.user-trigger span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 640px) {
  .header-actions {
    gap: 6px;
  }

  .header-actions :deep(.el-tag) {
    display: none;
  }

  .user-trigger {
    max-width: 92px;
  }
}
</style>
