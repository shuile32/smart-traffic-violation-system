<template>
  <div class="page-container" style="display:flex;align-items:center;justify-content:center;min-height:60vh">
    <el-result icon="info" title="功能开发中" sub-title="该功能正在开发中，敬请期待。">
      <template #extra>
        <el-button type="primary" @click="$router.back()">返回上一页</el-button>
        <el-button @click="$router.push('/')">返回首页</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup>
// Pure placeholder component — no additional logic needed
</script>
