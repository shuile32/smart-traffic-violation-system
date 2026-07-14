<template>
  <Transition name="back-to-top">
    <el-tooltip v-if="visible" content="返回顶部" placement="left">
      <el-button
        type="primary"
        circle
        class="back-to-top"
        aria-label="返回顶部"
        @click="scrollToTop"
      >
        <el-icon :size="20"><ArrowUp /></el-icon>
      </el-button>
    </el-tooltip>
  </Transition>
</template>

<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import { ArrowUp } from '@element-plus/icons-vue'

const props = defineProps({
  target: { type: Object, default: null }
})

const visible = ref(false)
let attachedTarget = null

function handleScroll() {
  visible.value = (attachedTarget?.scrollTop || 0) > 400
}

function detach() {
  attachedTarget?.removeEventListener('scroll', handleScroll)
  attachedTarget = null
  visible.value = false
}

function attach(target) {
  detach()
  if (!target?.addEventListener) return
  attachedTarget = target
  attachedTarget.addEventListener('scroll', handleScroll, { passive: true })
  handleScroll()
}

function scrollToTop() {
  attachedTarget?.scrollTo({ top: 0, behavior: 'smooth' })
}

watch(() => props.target, attach, { immediate: true })
onBeforeUnmount(detach)
</script>

<style scoped>
.back-to-top {
  position: fixed;
  right: 28px;
  bottom: 28px;
  width: 42px;
  height: 42px;
  z-index: 30;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18);
}

.back-to-top-enter-active,
.back-to-top-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}

.back-to-top-enter-from,
.back-to-top-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
