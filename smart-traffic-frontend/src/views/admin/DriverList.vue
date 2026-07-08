<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">驾驶员管理</h2>
      <el-button type="primary" @click="openDialog()">新 增 驾 驶 员</el-button>
    </div>

    <div class="table-toolbar">
      <div class="left">
        <el-input v-model="search.name" placeholder="姓名" clearable style="width:150px" @change="fetchList" />
        <el-input v-model="search.license_no" placeholder="驾驶证号" clearable style="width:180px" @change="fetchList" />
        <el-input v-model="search.phone" placeholder="手机号" clearable style="width:150px" @change="fetchList" />
        <el-button type="primary" @click="fetchList">查询</el-button>
        <el-button @click="search = {}; fetchList()">重置</el-button>
      </div>
    </div>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="name" label="姓名" width="100" />
      <el-table-column prop="gender" label="性别" width="60" />
      <el-table-column prop="phone" label="手机号" width="130" />
      <el-table-column prop="license_no" label="驾驶证号" width="180" />
      <el-table-column prop="license_type" label="准驾车型" width="100" />
      <el-table-column prop="total_points" label="总分" width="80" />
      <el-table-column prop="remaining_points" label="剩余分数" width="100" />
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" @click="openPointsDialog(row)">扣分</el-button>
          <el-button size="small" @click="viewPoints(row)">扣分记录</el-button>
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

    <!-- 新增/编辑弹窗 -->
    <el-dialog :title="editingId ? '编辑驾驶员' : '新增驾驶员'" v-model="dialogVisible" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-select v-model="form.gender" style="width:100%">
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
          </el-select>
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="驾驶证号" prop="license_no">
          <el-input v-model="form.license_no" />
        </el-form-item>
        <el-form-item label="准驾车型" prop="license_type">
          <el-input v-model="form.license_type" placeholder="如 C1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 扣分弹窗 -->
    <el-dialog title="违章扣分" v-model="pointsVisible" width="400px">
      <el-form :model="pointsForm" label-width="100px">
        <el-form-item label="扣除分数">
          <el-input-number v-model="pointsForm.points" :min="1" :max="12" />
        </el-form-item>
        <el-form-item label="处罚原因">
          <el-input v-model="pointsForm.reason" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pointsVisible = false">取消</el-button>
        <el-button type="primary" @click="handleDeduct">确认扣分</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getDrivers, createDriver, updateDriver, deleteDriver, deductPoints } from '@/api/driver'

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

const form = reactive({ name: '', gender: '', phone: '', license_no: '', license_type: '' })
const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [{ required: true, pattern: /^1\d{10}$/, message: '请输入正确的手机号', trigger: 'blur' }],
  license_no: [{ required: true, message: '请输入驾驶证号', trigger: 'blur' }]
}

const pointsVisible = ref(false)
const currentDriverId = ref(null)
const pointsForm = reactive({ points: 3, reason: '' })

async function fetchList() {
  loading.value = true
  try {
    const res = await getDrivers({ ...search, page: page.value, page_size: pageSize.value })
    list.value = res.data.items
    total.value = res.data.total
  } catch { /* handled */ }
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
      await updateDriver(editingId.value, form)
      ElMessage.success('更新成功')
    } else {
      await createDriver(form)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    fetchList()
  } catch { /* handled */ }
  finally { submitting.value = false }
}

async function handleDelete(id) {
  await deleteDriver(id)
  ElMessage.success('删除成功')
  fetchList()
}

function openPointsDialog(row) {
  currentDriverId.value = row.id
  pointsVisible.value = true
}

async function handleDeduct() {
  await deductPoints(currentDriverId.value, pointsForm)
  ElMessage.success('扣分操作完成')
  pointsVisible.value = false
  fetchList()
}

function viewPoints(row) {
  ElMessage.info(`查看 ${row.name} 的扣分记录`)
}

onMounted(fetchList)
</script>
