import { onMounted, onUnmounted, ref } from 'vue'

export function useResponsiveSidebar() {
  const mediaQuery = window.matchMedia('(max-width: 720px)')
  const isCollapse = ref(mediaQuery.matches)

  function collapseOnNarrow(event) {
    if (event.matches) isCollapse.value = true
  }

  onMounted(() => mediaQuery.addEventListener('change', collapseOnNarrow))
  onUnmounted(() => mediaQuery.removeEventListener('change', collapseOnNarrow))

  return { isCollapse }
}
