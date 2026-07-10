<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">违章记录管理</h2>
      <div style="display:flex;gap:12px">
        <el-button @click="handleBatchExport" :disabled="selectedIds.length === 0">
          批量导出 Excel
        </el-button>
        <el-button type="primary" @click="router.push('/admin/violations/upload')">
          上传违章证据
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="table-toolbar">
      <div class="left">
        <el-input v-model="search.plate" placeholder="车牌号" clearable style="width:140px" />
        <el-input v-model="search.driver" placeholder="驾驶员" clearable style="width:140px" />
        <el-select v-model="search.type" placeholder="违章类型" clearable style="width:140px">
          <el-option label="闯红灯" value="闯红灯" />
          <el-option label="超速" value="超速" />
          <el-option label="违停" value="违停" />
          <el-option label="压线" value="压线" />
          <el-option label="逆行" value="逆行" />
        </el-select>
        <el-select v-model="search.status" placeholder="审核状态" clearable style="width:140px">
          <el-option label="待 AI 检测" value="pending" />
          <el-option label="待审核" value="reviewing" />
          <el-option label="已通过" value="approved" />
          <el-option label="已驳回" value="rejected" />
        </el-select>
        <el-date-picker
          v-model="search.dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          style="width:250px"
        />
        <el-button type="primary" @click="fetchList">查询</el-button>
        <el-button @click="resetSearch">重置</el-button>
      </div>
    </div>

    <!-- 表格 -->
    <el-table :data="list" border stripe v-loading="loading" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="plate_number" label="车牌号" width="120" />
      <el-table-column label="违章图片" width="100">
        <template #default="{ row }">
          <el-image
            v-if="row.image_url"
            :src="row.image_url"
            style="width:60px;height:60px;border-radius:4px"
            fit="cover"
            :preview-src-list="[row.image_url]"
          />
        </template>
      </el-table-column>
      <el-table-column prop="violation_type" label="违章类型" width="100" />
      <el-table-column prop="location" label="违章地点" min-width="160" />
      <el-table-column prop="violation_time" label="违章时间" width="160" />
      <el-table-column label="AI 判定" width="140">
        <template #default="{ row }">
          <el-tag v-if="row.ai_result === '有效'" type="danger" size="small">有效</el-tag>
          <el-tag v-else-if="row.ai_result === '存疑'" type="warning" size="small">存疑</el-tag>
          <el-tag v-else type="info" size="small">待检测</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="审核状态" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.status === 'pending'" type="info">待检测</el-tag>
          <el-tag v-else-if="row.status === 'reviewing'" type="warning">待审核</el-tag>
          <el-tag v-else-if="row.status === 'approved'" type="success">已通过</el-tag>
          <el-tag v-else type="danger">已驳回</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="router.push(`/admin/violations/${row.id}/review`)">
            审核
          </el-button>
          <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
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
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchViolations } from '@/api/violation'

const router = useRouter()
const list = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const selectedIds = ref([])

const search = reactive({
  plate: '', driver: '', type: '', status: '', dateRange: null
})

function handleSelectionChange(rows) {
  selectedIds.value = rows.map(r => r.id)
}

async function fetchList() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (search.plate) params.plate = search.plate
    if (search.driver) params.driver = search.driver
    if (search.type) params.type = search.type
    if (search.status) params.status = search.status
    if (search.dateRange) {
      params.start_date = search.dateRange[0]
      params.end_date = search.dateRange[1]
    }
    const res = await fetchViolations(params)
    list.value = res.data.items
    total.value = res.data.total
  } catch { /* handled */ }
  finally { loading.value = false }
}

function resetSearch() {
  Object.keys(search).forEach(k => search[k] = k === 'dateRange' ? null : '')
  fetchList()
}

async function handleDelete(id) {
  ElMessage.warning('暂不支持删除')
}

async function handleBatchExport() {
  ElMessage.warning('导出功能开发中')
}

onMounted(fetchList)
</script>
