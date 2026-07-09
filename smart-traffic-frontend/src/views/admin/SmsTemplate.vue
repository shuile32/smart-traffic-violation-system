<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">短信模板管理</h2>
    </div>

    <el-card>
      <el-table :data="templates" border stripe>
        <el-table-column prop="code" label="模板编号" width="100" />
        <el-table-column prop="name" label="模板名称" width="160" />
        <el-table-column prop="content" label="模板内容" min-width="300" show-overflow-tooltip />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" @change="toggle(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" @click="editTemplate(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const templates = ref([
  { id: 1, code: 'SMS-001', name: '违章通知', content: '【交管平台】尊敬的车主，您名下车牌号{plate_no}于{time}在{location}违反{type}，请及时处理。', enabled: true },
  { id: 2, code: 'SMS-002', name: '审核通过', content: '【交管平台】您提交的违章举报已审核通过，奖励{reward}元已发放到您的账户。', enabled: true },
  { id: 3, code: 'SMS-003', name: '审核驳回', content: '【交管平台】您提交的违章举报经审核未通过，原因：{reason}。感谢您的参与。', enabled: true },
])

function editTemplate(row) { ElMessage.info('编辑功能待实现') }
function toggle(row) { ElMessage.success(row.enabled ? '已启用' : '已禁用') }
</script>

<style scoped>
.page-container { }
.page-header { margin-bottom: 16px; }
.page-title { font-size: 20px; margin: 0; }
</style>
