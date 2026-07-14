<template>
  <main v-if="hasError" class="error-boundary">
    <div class="error-content">
      <el-icon :size="46" color="#f56c6c"><WarningFilled /></el-icon>
      <h1>页面加载失败</h1>
      <p>当前页面发生异常，请刷新后重试。</p>
      <el-button type="primary" @click="reloadPage">刷新页面</el-button>
      <details v-if="errorMessage">
        <summary>错误详情</summary>
        <code>{{ errorMessage }}</code>
      </details>
    </div>
  </main>
  <router-view v-else />
</template>

<script setup>
import { onErrorCaptured, ref } from 'vue'
import { WarningFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const hasError = ref(false)
const errorMessage = ref('')

userStore.restoreLoginState()

onErrorCaptured((error, _instance, info) => {
  console.error('[AppErrorBoundary]', error, info)
  hasError.value = true
  errorMessage.value = error instanceof Error ? error.message : String(error)
  return false
})

function reloadPage() {
  window.location.reload()
}
</script>

<style scoped>
.error-boundary {
  display: grid;
  min-height: 100vh;
  place-items: center;
  padding: 24px;
  background: var(--bg-color);
}

.error-content {
  width: min(100%, 520px);
  padding: 32px;
  text-align: center;
  color: var(--text-color);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.error-content h1 {
  margin: 16px 0 8px;
  font-size: 22px;
}

.error-content p {
  margin: 0 0 20px;
  color: var(--text-secondary);
}

.error-content details {
  margin-top: 20px;
  text-align: left;
}

.error-content code {
  display: block;
  margin-top: 8px;
  overflow-wrap: anywhere;
}
</style>
