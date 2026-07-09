<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">摄像头设备管理</h2>
      <el-button type="primary" @click="openDialog()">新增设备</el-button>
    </div>

    <el-card>
      <el-table :data="cameras" border stripe>
        <el-table-column prop="camera_id" label="设备编号" width="120" />
        <el-table-column prop="name" label="设备名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="location_text" label="安装位置" width="200" show-overflow-tooltip />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '运行中' : '已停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="API Key" width="180">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="showKey(row)">查看/生成</el-button>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="openDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteCamera(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 弹窗 -->
    <el-dialog v-model="dialog.visible" :title="dialog.isEdit ? '编辑设备' : '新增设备'" width="500px">
      <el-form :model="dialog.form" label-width="80px">
        <el-form-item label="设备编号">
          <el-input v-model="dialog.form.camera_id" :disabled="dialog.isEdit" placeholder="如：CAM-005" />
        </el-form-item>
        <el-form-item label="设备名称">
          <el-input v-model="dialog.form.name" placeholder="如：人民路十字路口东" />
        </el-form-item>
        <el-form-item label="安装位置">
          <el-input v-model="dialog.form.location_text" placeholder="详细地址" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="dialog.form.status" active-value="active" inactive-value="inactive" active-text="运行" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" @click="saveCamera">保存</el-button>
      </template>
    </el-dialog>

    <!-- API Key 查看 -->
    <el-dialog v-model="keyDialog.visible" title="API Key" width="450px">
      <el-alert title="请妥善保管密钥，仅创建时展示一次" type="warning" :closable="false" show-icon style="margin-bottom:16px" />
      <el-input v-model="keyDialog.key" readonly>
        <template #append>
          <el-button @click="copyKey">复制</el-button>
        </template>
      </el-input>
      <template #footer>
        <el-button type="primary" @click="generateKey">生成新密钥</el-button>
        <el-button @click="keyDialog.visible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { mockCameras, delay } from '@/api/mock'
import { ElMessage, ElMessageBox } from 'element-plus'

const cameras = ref([...mockCameras.map(c => ({ ...c, api_key: '' }))])

const dialog = ref({
  visible: false,
  isEdit: false,
  form: { camera_id: '', name: '', location_text: '', status: 'active' }
})

const keyDialog = ref({ visible: false, key: '', cameraId: null })

function openDialog(row) {
  if (row) {
    dialog.value = { visible: true, isEdit: true, form: { ...row } }
  } else {
    dialog.value = { visible: true, isEdit: false, form: { camera_id: '', name: '', location_text: '', status: 'active' } }
  }
}

async function saveCamera() {
  await delay(300)
  if (dialog.value.isEdit) {
    const idx = cameras.value.findIndex(c => c.id === dialog.value.form.id)
    if (idx > -1) cameras.value[idx] = { ...cameras.value[idx], ...dialog.value.form }
  } else {
    cameras.value.push({ ...dialog.value.form, id: Date.now(), created_at: new Date().toISOString() })
  }
  dialog.value.visible = false
  ElMessage.success('保存成功')
}

function deleteCamera(row) {
  ElMessageBox.confirm(`确定删除设备 ${row.name} 吗？`, '确认', { type: 'warning' }).then(() => {
    cameras.value = cameras.value.filter(c => c.id !== row.id)
    ElMessage.success('已删除')
  })
}

function showKey(row) {
  keyDialog.value = { visible: true, key: row.api_key || '未生成', cameraId: row.id }
}

async function generateKey() {
  await delay(400)
  const newKey = 'sk-' + Array.from({ length: 32 }, () => Math.random().toString(36)[2]).join('')
  keyDialog.value.key = newKey
  const cam = cameras.value.find(c => c.id === keyDialog.value.cameraId)
  if (cam) cam.api_key = newKey
  ElMessage.success('新密钥已生成')
}

function copyKey() {
  navigator.clipboard.writeText(keyDialog.value.key)
  ElMessage.success('已复制到剪贴板')
}
</script>

<style scoped>
.page-container { }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-title { font-size: 20px; margin: 0; }
</style>
