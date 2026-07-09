<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">数据库维护</h2>
    </div>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card header="数据库备份">
          <p style="margin-bottom:12px;color:#666">备份当前数据库所有数据</p>
          <el-button type="primary" :loading="backingUp" @click="handleBackup">立即备份</el-button>
          <el-table :data="backups" border stripe style="margin-top:16px" :show-header="false">
            <el-table-column prop="name" label="文件名" />
            <el-table-column prop="size" label="大小" width="100" />
            <el-table-column prop="time" label="时间" width="160" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card header="数据恢复">
          <p style="margin-bottom:12px;color:#e6a23c;font-size:13px">⚠ 恢复操作将覆盖当前数据库,请谨慎操作</p>
          <el-upload
            :auto-upload="false"
            :limit="1"
            accept=".sql,.gz"
            style="margin-bottom:12px"
          >
            <el-button type="warning">选择备份文件</el-button>
          </el-upload>
          <el-button type="danger" @click="handleRestore">执行恢复</el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { backupDatabase } from '@/api/system'

const backingUp = ref(false)
const backups = ref([])

async function handleBackup() {
  backingUp.value = true
  try {
    await backupDatabase()
    ElMessage.success('数据库备份成功')
    // 刷新备份列表...
  } catch { /* handled */ }
  finally { backingUp.value = false }
}

function handleRestore() {
  ElMessageBox.confirm('恢复操作将覆盖当前数据，确定继续？', '危险操作', {
    type: 'error',
    confirmButtonText: '确定恢复',
    confirmButtonClass: 'el-button--danger'
  }).then(() => {
    ElMessage.warning('恢复功能需要选择备份文件后调用后端接口')
  })
}
</script>
