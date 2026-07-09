<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">违章规则配置</h2>
      <el-button type="primary" @click="dialog.visible = true">新增规则</el-button>
    </div>

    <el-card>
      <el-table :data="rules" border stripe>
        <el-table-column prop="rule_code" label="规则编号" width="100" />
        <el-table-column prop="violation_type" label="违章类型" width="120" />
        <el-table-column prop="description" label="规则描述" min-width="240" show-overflow-tooltip />
        <el-table-column label="罚款(元)" width="90" align="center">
          <template #default="{ row }">{{ row.fine_amount }}</template>
        </el-table-column>
        <el-table-column label="扣分" width="70" align="center">
          <template #default="{ row }">{{ row.points }}</template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" @change="toggleRule(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click="editRule(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteRule(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const rules = ref([
  { id: 1, rule_code: 'RL-001', violation_type: '闯红灯', description: '车辆在红灯亮起时越过停止线并继续通行', fine_amount: 200, points: 6, enabled: true },
  { id: 2, rule_code: 'RL-002', violation_type: '违停', description: '车辆在禁停区域或标线内停放', fine_amount: 200, points: 3, enabled: true },
  { id: 3, rule_code: 'RL-003', violation_type: '压线', description: '车辆在行驶中压越车道实线', fine_amount: 200, points: 3, enabled: true },
  { id: 4, rule_code: 'RL-004', violation_type: '逆行', description: '车辆在单行道或分隔道路上逆向行驶', fine_amount: 200, points: 3, enabled: true },
  { id: 5, rule_code: 'RL-005', violation_type: '超速', description: '车辆行驶速度超过路段限速值', fine_amount: 500, points: 6, enabled: true },
  { id: 6, rule_code: 'RL-006', violation_type: '占用应急车道', description: '非紧急情况下在应急车道行驶或停车', fine_amount: 200, points: 6, enabled: true },
])

const dialog = ref({ visible: false, isEdit: false, form: {} })

function editRule(row) { ElMessage.info('编辑功能待实现') }
function deleteRule(row) {
  ElMessageBox.confirm('确定删除该规则？', '确认', { type: 'warning' }).then(() => {
    rules.value = rules.value.filter(r => r.id !== row.id)
    ElMessage.success('已删除')
  })
}
function toggleRule(row) { ElMessage.success(row.enabled ? '已启用' : '已禁用') }
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
