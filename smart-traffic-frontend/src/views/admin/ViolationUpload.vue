<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">违章证据上传</h2>
    </div>

    <el-card style="max-width:800px">
      <template #header>
        <span>上传违章图片信息</span>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="违章图片" prop="image">
          <el-upload
            :auto-upload="false"
            :on-change="handleImageChange"
            :before-remove="handleImageRemove"
            :file-list="fileList"
            list-type="picture-card"
            accept="image/*"
            :limit="3"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">支持 jpg/png，单张不超过 10MB</div>
        </el-form-item>

        <el-form-item label="违章类型" prop="violation_type">
          <el-select v-model="form.violation_type" placeholder="选择违章类型" style="width:100%">
            <el-option label="闯红灯" value="闯红灯" />
            <el-option label="超速行驶" value="超速行驶" />
            <el-option label="违法停车" value="违法停车" />
            <el-option label="压实线变道" value="压实线变道" />
            <el-option label="逆向行驶" value="逆向行驶" />
            <el-option label="不礼让行人" value="不礼让行人" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>

        <el-form-item label="车牌号" prop="plate_number">
          <el-input v-model="form.plate_number" placeholder="请输入车牌号" />
        </el-form-item>

        <el-form-item label="违章地点" prop="location">
          <el-input v-model="form.location" placeholder="请输入违章地点" />
        </el-form-item>

        <el-form-item label="违章时间" prop="violation_time">
          <el-date-picker
            v-model="form.violation_time"
            type="datetime"
            placeholder="选择违章时间"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width:100%"
          />
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="补充说明（可选）" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">提交并触发 AI 检测</el-button>
          <el-button @click="router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { createViolation, uploadImage } from '@/api/violation'
import { ElMessage } from 'element-plus'

const router = useRouter()
const formRef = ref(null)
const submitting = ref(false)
const fileList = ref([])

const form = reactive({
  violation_type: '', plate_number: '', location: '',
  violation_time: '', remark: ''
})

const rules = {
  violation_type: [{ required: true, message: '请选择违章类型', trigger: 'change' }],
  plate_number: [{ required: true, message: '请输入车牌号', trigger: 'blur' }],
  location: [{ required: true, message: '请输入违章地点', trigger: 'blur' }],
  violation_time: [{ required: true, message: '请选择违章时间', trigger: 'change' }]
}

function handleImageChange(file) {
  fileList.value.push(file)
}

function handleImageRemove(file) {
  const idx = fileList.value.indexOf(file)
  if (idx > -1) fileList.value.splice(idx, 1)
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  if (fileList.value.length === 0) {
    ElMessage.warning('请至少上传一张违章图片')
    return
  }

  submitting.value = true
  try {
    const fd = new FormData()
    Object.keys(form).forEach(k => fd.append(k, form[k] || ''))
    fileList.value.forEach(f => fd.append('images', f.raw))

    await createViolation(fd)
    ElMessage.success('上传成功，已触发 AI 违章检测')
    router.push('/admin/violations')
  } catch { /* handled */ }
  finally { submitting.value = false }
}
</script>

<style scoped>
.upload-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
}
</style>
