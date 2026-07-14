<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">违章查询</h2>
      <el-button type="success" :loading="exporting" :disabled="total === 0" @click="exportData">
        <el-icon><Download /></el-icon>导出 Excel
      </el-button>
    </div>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="plate_no" label="车牌号" width="120" />
      <el-table-column prop="violation_type" label="违章类型" width="100">
        <template #default="{ row }">
          <el-tag :type="row.violation_type === '闯红灯' ? 'danger' : 'warning'" size="small">{{ row.violation_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="location_text" label="违章地点" min-width="180" show-overflow-tooltip />
      <el-table-column prop="occurred_at" label="违章时间" width="170">
        <template #default="{ row }">{{ formatTime(row.occurred_at) }}</template>
      </el-table-column>
      <el-table-column label="处罚" width="120">
        <template #default="{ row }">
          <span v-if="row.status === 'pending'" style="color:#e6a23c">待处理</span>
          <span v-else-if="row.status === 'handled'" style="color:#67c23a">已处理</span>
          <span v-else style="color:#909399">已撤销</span>
        </template>
      </el-table-column>
      <el-table-column prop="points" label="扣分" width="70" align="center" />
      <el-table-column prop="fine_amount" label="罚款(元)" width="90" align="center" />
    </el-table>

    <div style="display:flex;justify-content:flex-end;margin-top:16px">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @change="fetchList"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchOwnerViolations } from '@/api/violation'
import { fetchAllPages } from '@/utils/pagination'
import { exportToExcel, formatExportTime } from '@/utils/export'
import { Download } from '@element-plus/icons-vue'

const list = ref([])
const loading = ref(false)
const exporting = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

function formatTime(t) { return t ? new Date(t).toLocaleString('zh-CN') : '' }

async function fetchList() {
  loading.value = true
  try {
    const uid = JSON.parse(localStorage.getItem('userInfo') || '{}').id
    if (uid) {
      const res = await fetchOwnerViolations(uid, { page: page.value, page_size: pageSize.value })
      list.value = res.data.items
      total.value = res.data.total
    }
  } catch {}
  loading.value = false
}

async function exportData() {
  const uid = JSON.parse(localStorage.getItem('userInfo') || '{}').id
  if (!uid) return
  exporting.value = true
  try {
    const rows = await fetchAllPages(params => fetchOwnerViolations(uid, params))
    exportToExcel(rows.map(row => ({
      ...row,
      occurred_at: formatExportTime(row.occurred_at)
    })), [
      { key: 'plate_no', label: '车牌号', width: 14 },
      { key: 'violation_type', label: '违章类型', width: 14 },
      { key: 'location_text', label: '违章地点', width: 24 },
      { key: 'occurred_at', label: '违章时间', width: 22 },
      { key: 'fine_amount', label: '罚款（元）', width: 12 },
      { key: 'points', label: '扣分', width: 10 }
    ], `我的违章_${new Date().toISOString().slice(0, 10)}`)
  } finally {
    exporting.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped>
.page-container { }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 20px; margin: 0; }
</style>
