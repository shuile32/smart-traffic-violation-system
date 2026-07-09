<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">角色权限管理</h2>
    </div>

    <el-row :gutter="20">
      <el-col :span="8">
        <el-card header="角色列表">
          <el-table :data="roles" border stripe v-loading="loading" highlight-current-row
            @current-change="handleRoleChange" style="width:100%">
            <el-table-column prop="name" label="角色名称" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card header="权限配置">
          <template v-if="currentRole">
            <p style="margin-bottom:12px">当前角色：<strong>{{ currentRole.name }}</strong></p>
            <el-tree
              :data="permissionTree"
              show-checkbox
              node-key="id"
              default-expand-all
              :default-checked-keys="currentRole.permissions"
            />
            <el-button type="primary" style="margin-top:16px" @click="savePermissions">保存权限</el-button>
          </template>
          <p v-else style="text-align:center;color:#999;padding:60px 0">请选择左侧角色</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getRoles, updateRolePermissions } from '@/api/system'

const roles = ref([])
const loading = ref(false)
const currentRole = ref(null)

const permissionTree = [
  { id: 1, label: '车辆管理', children: [
    { id: 101, label: '查看车辆' },
    { id: 102, label: '新增车辆' },
    { id: 103, label: '编辑车辆' },
    { id: 104, label: '删除车辆' }
  ]},
  { id: 2, label: '驾驶员管理', children: [
    { id: 201, label: '查看驾驶员' },
    { id: 202, label: '新增驾驶员' },
    { id: 203, label: '扣分管理' }
  ]},
  { id: 3, label: '违章管理', children: [
    { id: 301, label: '查看违章' },
    { id: 302, label: '违章审核' },
    { id: 303, label: '批量导出' }
  ]},
  { id: 4, label: '系统管理', children: [
    { id: 401, label: '公告管理' },
    { id: 402, label: '日志查看' },
    { id: 403, label: '角色管理' }
  ]}
]

async function fetchRoles() {
  loading.value = true
  try {
    const res = await getRoles()
    roles.value = res.data || []
  } catch { /* handled */ }
  finally { loading.value = false }
}

function handleRoleChange(row) {
  currentRole.value = row
}

async function savePermissions() {
  ElMessage.success('权限保存成功（需接入后端接口）')
}

onMounted(fetchRoles)
</script>
