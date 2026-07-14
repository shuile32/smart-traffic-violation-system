<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">违章记录管理</h2>
      <el-button type="success" :loading="exporting" :disabled="total === 0" @click="exportData">
        <el-icon><Download /></el-icon>导出 Excel
      </el-button>
    </div>

    <!-- 筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filter" size="small">
        <el-form-item label="车牌号">
          <el-input v-model="filter.plate" placeholder="输入车牌号" clearable />
        </el-form-item>
        <el-form-item label="违章类型">
          <el-select v-model="filter.type" placeholder="全部" clearable style="width:140px">
            <el-option v-for="t in types" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchList">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格 -->
    <el-card style="margin-top:16px">
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="violation_no" label="编号" width="140" />
        <el-table-column prop="plate_no" label="车牌号" width="120" />
        <el-table-column prop="violation_type" label="违章类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.violation_type === '闯红灯' ? 'danger' : 'warning'" size="small">{{ row.violation_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="location_text" label="地点" min-width="180" show-overflow-tooltip />
        <el-table-column prop="occurred_at" label="发生时间" width="170">
          <template #default="{ row }">{{ formatTime(row.occurred_at) }}</template>
        </el-table-column>
        <el-table-column prop="fine_amount" label="罚款(元)" width="90" align="center" />
        <el-table-column prop="points" label="扣分" width="70" align="center" />
      </el-table>

      <div style="padding:16px 0 0;text-align:right">
        <el-pagination
          v-model:current-page="page"
          :total="total"
          :page-size="pageSize"
          layout="total, prev, pager, next"
          @current-change="fetchList"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { fetchViolations as getViolations } from '@/api/violation'
import { buildViolationQuery } from '@/utils/contracts'
import { fetchAllPages } from '@/utils/pagination'
import { exportToExcel, formatExportTime } from '@/utils/export'
import { Download } from '@element-plus/icons-vue'

const list = ref([])
const loading = ref(false)
const exporting = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const types = ['闯红灯', '违停', '压线', '逆行', '超速', '占用应急车道']

const filter = reactive({ plate: '', type: '' })

function formatTime(t) { return t ? new Date(t).toLocaleString('zh-CN') : '' }

async function fetchList() {
  loading.value = true
  try {
    const res = await getViolations(buildViolationQuery(filter, page.value, pageSize.value))
    list.value = res.data.items
    total.value = res.data.total
  } catch { /* handled by interceptor */ }
  finally { loading.value = false }
}

function resetFilter() {
  Object.assign(filter, { plate: '', type: '' })
  page.value = 1
  fetchList()
}

async function exportData() {
  exporting.value = true
  try {
    const rows = await fetchAllPages(
      params => getViolations(params),
      buildViolationQuery(filter)
    )
    exportToExcel(rows.map(row => ({
      ...row,
      occurred_at: formatExportTime(row.occurred_at)
    })), [
      { key: 'violation_no', label: '违章编号', width: 22 },
      { key: 'plate_no', label: '车牌号', width: 14 },
      { key: 'violation_type', label: '违章类型', width: 14 },
      { key: 'location_text', label: '违章地点', width: 24 },
      { key: 'occurred_at', label: '违章时间', width: 22 },
      { key: 'fine_amount', label: '罚款（元）', width: 12 },
      { key: 'points', label: '扣分', width: 10 }
    ], `违章记录_${new Date().toISOString().slice(0, 10)}`)
  } finally {
    exporting.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped>
.page-container { }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-title { margin: 0; font-size: 20px; }
.filter-card { margin-bottom: 0; }
</style>
