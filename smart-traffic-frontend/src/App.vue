<template>
  <router-view />
</template>

<script setup>
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
userStore.restoreLoginState()
</script>
