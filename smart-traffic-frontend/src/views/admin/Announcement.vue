<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">公告管理</h2>
      <el-button type="primary" @click="openDialog()">发布公告</el-button>
    </div>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="title" label="标题" min-width="200" />
      <el-table-column prop="content" label="内容" min-width="300" show-overflow-tooltip />
      <el-table-column prop="created_at" label="发布时间" width="160" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog title="发布/编辑公告" v-model="dialogVisible" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="5" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getAnnouncements, createAnnouncement, updateAnnouncement, deleteAnnouncement } from '@/api/system'

const list = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref(null)
const submitting = ref(false)
const editingId = ref(null)
const form = reactive({ title: '', content: '' })
const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }]
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getAnnouncements()
    list.value = res.data || []
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
      await updateAnnouncement(editingId.value, form)
    } else {
      await createAnnouncement(form)
    }
    ElMessage.success(editingId.value ? '更新成功' : '发布成功')
    dialogVisible.value = false
    fetchList()
  } catch { /* handled */ }
  finally { submitting.value = false }
}

async function handleDelete(id) {
  await deleteAnnouncement(id)
  ElMessage.success('删除成功')
  fetchList()
}

onMounted(fetchList)
</script>
