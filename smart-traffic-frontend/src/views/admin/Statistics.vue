<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">统计分析</h2>
    </div>
    <el-card>
      <p style="text-align:center;color:#999;padding:60px 0">
        统计分析页面 —— 访问 <el-link type="primary" @click="router.push('/stats')">统计分析台</el-link> 查看完整可视化
      </p>
    </el-card>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>
