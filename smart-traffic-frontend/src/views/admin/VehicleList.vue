<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">车辆管理</h2>
      <el-button type="primary" @click="openDialog()">新 增 车 辆</el-button>
    </div>

    <!-- 搜索栏 -->
    <div class="table-toolbar">
      <div class="left">
        <el-input v-model="search.plate" placeholder="车牌号" clearable style="width:180px" @change="fetchList" />
        <el-input v-model="search.brand" placeholder="品牌" clearable style="width:150px" @change="fetchList" />
        <el-button type="primary" @click="fetchList">查询</el-button>
        <el-button @click="search = {}; fetchList()">重置</el-button>
      </div>
    </div>

    <!-- 表格 -->
    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="plate_number" label="车牌号" width="120" />
      <el-table-column prop="brand" label="品牌" width="120" />
      <el-table-column prop="model" label="型号" width="140" />
      <el-table-column prop="color" label="颜色" width="80" />
      <el-table-column prop="owner_name" label="车主姓名" width="100" />
      <el-table-column prop="owner_phone" label="车主手机号" width="130" />
      <el-table-column prop="engine_number" label="发动机号" min-width="140" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
          <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div style="display:flex;justify-content:flex-end;margin-top:16px">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @change="fetchList"
      />
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog :title="dialogTitle" v-model="dialogVisible" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="车牌号" prop="plate_number">
          <el-input v-model="form.plate_number" />
        </el-form-item>
        <el-form-item label="品牌" prop="brand">
          <el-input v-model="form.brand" />
        </el-form-item>
        <el-form-item label="型号" prop="model">
          <el-input v-model="form.model" />
        </el-form-item>
        <el-form-item label="颜色" prop="color">
          <el-input v-model="form.color" />
        </el-form-item>
        <el-form-item label="车主姓名" prop="owner_name">
          <el-input v-model="form.owner_name" />
        </el-form-item>
        <el-form-item label="车主手机号" prop="owner_phone">
          <el-input v-model="form.owner_phone" />
        </el-form-item>
        <el-form-item label="发动机号" prop="engine_number">
          <el-input v-model="form.engine_number" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getVehicles, createVehicle, updateVehicle, deleteVehicle } from '@/api/vehicle'

const list = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const search = reactive({})

const dialogVisible = ref(false)
const formRef = ref(null)
const submitting = ref(false)
const editingId = ref(null)

const dialogTitle = computed(() => (editingId.value ? '编辑车辆' : '新增车辆'))

const form = reactive({
  plate_number: '', brand: '', model: '', color: '',
  owner_name: '', owner_phone: '', engine_number: ''
})

const rules = {
  plate_number: [{ required: true, message: '请输入车牌号', trigger: 'blur' }],
  brand: [{ required: true, message: '请输入品牌', trigger: 'blur' }],
  owner_phone: [{ pattern: /^1\d{10}$/, message: '请输入正确的手机号', trigger: 'blur' }]
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getVehicles({ ...search, page: page.value, page_size: pageSize.value })
    list.value = res.data.items
    total.value = res.data.total
  } catch { /* handled by interceptor */ }
  finally { loading.value = false }
}

function openDialog(row) {
  editingId.value = row ? row.id : null
  if (row) Object.assign(form, row)
  else Object.keys(form).forEach(k => form[k] = '')
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    if (editingId.value) {
      await updateVehicle(editingId.value, form)
      ElMessage.success('更新成功')
    } else {
      await createVehicle(form)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    fetchList()
  } catch { /* handled */ }
  finally { submitting.value = false }
}

async function handleDelete(id) {
  await deleteVehicle(id)
  ElMessage.success('删除成功')
  fetchList()
}

function viewDetail(row) {
  // 跳转到详情或在弹窗中展示
  ElMessage.info(`查看车辆：${row.plate_number}`)
}

onMounted(fetchList)
</script>
