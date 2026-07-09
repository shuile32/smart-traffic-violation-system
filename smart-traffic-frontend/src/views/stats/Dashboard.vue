<template>
  <div class="stats-dashboard">
    <div class="page-header">
      <h2 class="page-title">统计分析台</h2>
      <div class="header-actions">
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始" end-placeholder="结束" size="small" style="width:240px" />
        <el-button type="primary" size="small" @click="router.push('/stats/report')">
          <el-icon><Document /></el-icon>生成 LLM 分析报告
        </el-button>
      </div>
    </div>

    <!-- 概览指标卡片 -->
    <el-row :gutter="16" class="overview-row">
      <el-col :span="4" v-for="card in overviewCards" :key="card.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value" :style="{ color: card.color }">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区 -->
    <el-row :gutter="16" style="margin-top:16px">
      <!-- 违章趋势 -->
      <el-col :span="14">
        <el-card>
          <template #header><span>违章趋势（近30天）</span></template>
          <div ref="trendChart" style="height:320px"></div>
        </el-card>
      </el-col>

      <!-- 违章类型占比 -->
      <el-col :span="10">
        <el-card>
          <template #header><span>违章类型占比</span></template>
          <div ref="typeChart" style="height:320px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 区域排行 -->
    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="24">
        <el-card>
          <template #header><span>区域违章排行</span></template>
          <div ref="regionChart" style="height:300px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { getOverview, getTrend, getTypeRatio, getRegionRank } from '@/api/statistics'
import * as echarts from 'echarts'

const router = useRouter()
const dateRange = ref([])
const trendChart = ref(null)
const typeChart = ref(null)
const regionChart = ref(null)

const overview = ref({})
const trend = ref([])
const typeRatio = ref([])
const regionRank = ref([])

const overviewCards = computed(() => [
  { label: '总案件数', value: overview.value.total_cases, color: '#409eff' },
  { label: '正式违章', value: overview.value.total_violations, color: '#e6a23c' },
  { label: '通过率', value: overview.value.approve_rate + '%', color: '#67c23a' },
  { label: '驳回率', value: overview.value.reject_rate + '%', color: '#f56c6c' },
  { label: '待审核', value: overview.value.pending_count, color: '#e6a23c' },
  { label: '今日新增', value: overview.value.today_new, color: '#909399' }
])

async function loadData() {
  const [ov, tr, ty, rg] = await Promise.all([
    getOverview(),
    getTrend(),
    getTypeRatio(),
    getRegionRank()
  ])
  overview.value = ov.data
  trend.value = tr.data
  typeRatio.value = ty.data
  regionRank.value = rg.data
}

function renderTrend() {
  if (!trendChart.value) return
  const chart = echarts.init(trendChart.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: trend.value.map(t => t.date.slice(5)), axisLabel: { rotate: 45 } },
    yAxis: { type: 'value' },
    series: [{
      data: trend.value.map(t => t.count),
      type: 'line',
      smooth: true,
      areaStyle: { opacity: 0.15 },
      color: '#409eff'
    }]
  })
}

function renderType() {
  if (!typeChart.value) return
  const chart = echarts.init(typeChart.value)
  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['45%', '75%'],
      center: ['50%', '45%'],
      data: typeRatio.value.map(t => ({ name: t.name, value: t.value })),
      label: { show: true, formatter: '{b}\n{d}%' }
    }]
  })
}

function renderRegion() {
  if (!regionChart.value) return
  const chart = echarts.init(regionChart.value)
  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: regionRank.value.map(r => r.name).reverse(), inverse: true },
    series: [{
      data: regionRank.value.map(r => r.value).reverse(),
      type: 'bar',
      itemStyle: { borderRadius: [0, 4, 4, 0], color: '#409eff' }
    }]
  })
}

onMounted(async () => {
  await loadData()
  await nextTick()
  renderTrend()
  renderType()
  renderRegion()
})
</script>

<style scoped>
.stats-dashboard { }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-title { font-size: 20px; margin: 0; }
.header-actions { display: flex; gap: 12px; }

.overview-row { margin-bottom: 0; }
.stat-card { text-align: center; cursor: default; }
.stat-value { font-size: 28px; font-weight: bold; }
.stat-label { font-size: 13px; color: #909399; margin-top: 8px; }
</style>
