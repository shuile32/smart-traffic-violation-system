<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">违章审核处理</h2>
      <el-button @click="router.back()">返回列表</el-button>
    </div>

    <el-row :gutter="20" v-loading="loading">
      <!-- 左侧：图片展示 + AI 检测结果 -->
      <el-col :span="14">
        <el-card>
          <template #header>
            <span>违章证据图片</span>
          </template>
          <div class="image-area">
            <el-image
              v-if="detail.image_url"
              :src="detail.image_url"
              fit="contain"
              style="width:100%;max-height:500px"
              :preview-src-list="[detail.image_url]"
            >
              <template #error>
                <div class="image-placeholder">
                  <el-icon :size="48"><Picture /></el-icon>
                  <p>暂无图片</p>
                </div>
              </template>
            </el-image>
          </div>
        </el-card>

        <!-- AI 检测结果 -->
        <el-card style="margin-top:16px">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>AI 检测结果（YOLO-V8 + LLM 分析）</span>
              <el-tag v-if="detail.ai_result === '有效'" type="danger">判定：有效违章</el-tag>
              <el-tag v-else-if="detail.ai_result === '存疑'" type="warning">判定：存疑</el-tag>
              <el-tag v-else type="info">待检测</el-tag>
            </div>
          </template>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="识别违章类型">{{ detail.ai_type || '—' }}</el-descriptions-item>
            <el-descriptions-item label="识别置信度">{{ detail.ai_confidence || '—' }}</el-descriptions-item>
            <el-descriptions-item label="检测到车牌">{{ detail.ai_plate || '—' }}</el-descriptions-item>
            <el-descriptions-item label="路段限速">{{ detail.ai_speed_limit || '—' }}</el-descriptions-item>
          </el-descriptions>
          <div v-if="detail.ai_reason" style="margin-top:12px">
            <strong>LLM 判定理由：</strong>
            <p style="color:#666;margin-top:4px;line-height:1.6">{{ detail.ai_reason }}</p>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：违章信息 + 审核操作 -->
      <el-col :span="10">
        <el-card>
          <template #header><span>违章信息</span></template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="车牌号">{{ detail.plate_number }}</el-descriptions-item>
            <el-descriptions-item label="违章类型">{{ detail.violation_type }}</el-descriptions-item>
            <el-descriptions-item label="违章地点">{{ detail.location }}</el-descriptions-item>
            <el-descriptions-item label="违章时间">{{ detail.violation_time }}</el-descriptions-item>
            <el-descriptions-item label="来源">{{ detail.source || '管理员上传' }}</el-descriptions-item>
            <el-descriptions-item label="关联车主">{{ detail.owner_name || '—' }}</el-descriptions-item>
            <el-descriptions-item label="车主手机号">{{ detail.owner_phone || '—' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 审核操作 -->
        <el-card style="margin-top:16px" v-if="detail.status === 'reviewing' || detail.status === 'pending'">
          <template #header><span>审核操作</span></template>
          <el-form :model="reviewForm" label-width="90px">
            <el-form-item label="审核结果" required>
              <el-radio-group v-model="reviewForm.action">
                <el-radio value="approved">
                  <span style="color:#67c23a;font-weight:bold">审核通过</span>
                </el-radio>
                <el-radio value="rejected">
                  <span style="color:#f56c6c;font-weight:bold">审核驳回</span>
                </el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="处理意见">
              <el-input v-model="reviewForm.comment" type="textarea" :rows="3"
                placeholder="填写审核意见（可选）" />
            </el-form-item>
            <el-form-item>
              <el-button type="success" :loading="submitting" @click="handleReview">
                确认审核
              </el-button>
              <el-button @click="router.back()">取消</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 已审核状态展示 -->
        <el-card style="margin-top:16px" v-else>
          <template #header><span>审核结果</span></template>
          <el-result
            :icon="detail.status === 'approved' ? 'success' : 'error'"
            :title="detail.status === 'approved' ? '已审核通过' : '已驳回'"
            :sub-title="detail.review_comment || ''"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getViolation, getAiResult, reviewViolation } from '@/api/violation'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const detail = ref({})
const loading = ref(false)
const submitting = ref(false)
const reviewForm = reactive({ action: 'approved', comment: '' })

async function fetchDetail() {
  loading.value = true
  try {
    const id = route.params.id
    const [violationRes, aiRes] = await Promise.all([
      getViolation(id),
      getAiResult(id).catch(() => ({ data: {} }))
    ])
    detail.value = { ...violationRes.data, ...aiRes.data }
  } catch { /* handled */ }
  finally { loading.value = false }
}

async function handleReview() {
  submitting.value = true
  try {
    await reviewViolation(route.params.id, reviewForm)
    ElMessage.success(reviewForm.action === 'approved' ? '审核通过' : '已驳回')
    router.push('/admin/violations')
  } catch { /* handled */ }
  finally { submitting.value = false }
}

onMounted(fetchDetail)
</script>

<style scoped>
.image-area {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
  background: var(--bg-color);
  border-radius: 4px;
}
.image-placeholder {
  text-align: center;
  color: #c0c4cc;
}
</style>
