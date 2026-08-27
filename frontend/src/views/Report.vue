<template>
  <div class="report-page">
    <el-card v-loading="loading">
      <template #header>
        <div class="header">
          <span>面试复盘报告</span>
          <el-button size="small" @click="router.push({ name: 'interview' })">再来一场面试</el-button>
        </div>
      </template>

      <el-empty v-if="!loading && !report" description="暂无报告。完成一场模拟面试后，将在此展示复盘结果。" />

      <template v-if="report">
        <!-- 总分 + 四维度 -->
        <div class="overview">
          <el-progress
            type="dashboard"
            :percentage="Math.round(report.overall_score)"
            :color="scoreColor(report.overall_score)"
            :width="150"
          >
            <template #default>
              <span class="overall-num">{{ Math.round(report.overall_score) }}</span>
            </template>
          </el-progress>

          <div class="dims">
            <div v-for="(label, key) in DIMS" :key="key" class="dim-item">
              <div class="dim-label">
                {{ label }}
                <el-tag size="small" :type="scoreTag(report.dimensions?.[key] ?? 0)">
                  {{ Math.round(report.dimensions?.[key] ?? 0) }}
                </el-tag>
              </div>
              <el-progress
                :percentage="Math.round(report.dimensions?.[key] ?? 0)"
                :color="scoreColor(report.dimensions?.[key] ?? 0)"
                :stroke-width="14"
              />
            </div>
          </div>
        </div>

        <!-- 总评 -->
        <el-divider content-position="left">总评与建议</el-divider>
        <el-alert :title="report.summary || '暂无总评'" type="info" :closable="false" />

        <!-- 弱点 -->
        <template v-if="report.weak_points?.length">
          <el-divider content-position="left">待加强的弱点</el-divider>
          <el-tag
            v-for="(w, i) in report.weak_points"
            :key="i"
            type="danger"
            effect="plain"
            class="weak-tag"
          >
            {{ w }}
          </el-tag>
        </template>

        <!-- 逐题反馈 -->
        <el-divider content-position="left">逐题批改（{{ report.question_feedback?.length || 0 }}）</el-divider>
        <el-collapse v-if="report.question_feedback?.length">
          <el-collapse-item v-for="(qf, i) in report.question_feedback" :key="i" :name="i">
            <template #title>
              <div class="qf-title">
                <span class="qf-q">Q{{ i + 1 }}：{{ qf.question || '（题目）' }}</span>
                <el-tag size="small" :type="scoreTag(qf.score ?? 0)">{{ Math.round(qf.score ?? 0) }}</el-tag>
              </div>
            </template>
            <div class="qf-body">
              <div class="qf-answer"><b>我的回答：</b>{{ qf.answer }}</div>
              <div class="qf-comment"><b>面试官点评：</b>{{ qf.comment }}</div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getReport } from '@/api/report'

const route = useRoute()
const router = useRouter()

const DIMS = { tech: '技术能力', expression: '表达沟通', logic: '逻辑思维', project: '项目经验' }

const loading = ref(false)
const report = ref(null)

function scoreColor(s) {
  if (s >= 80) return '#67c23a'
  if (s >= 60) return '#e6a23c'
  return '#f56c6c'
}
function scoreTag(s) {
  return s >= 80 ? 'success' : s >= 60 ? 'warning' : 'danger'
}

async function load() {
  const id = route.params.id
  if (!id) return
  loading.value = true
  try {
    report.value = await getReport(id)
  } catch {
    report.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.overview {
  display: flex;
  align-items: center;
  gap: 40px;
  padding: 16px 8px;
}
.overall-num {
  font-size: 34px;
  font-weight: 700;
}
.dims {
  flex: 1;
}
.dim-item {
  margin-bottom: 16px;
}
.dim-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  font-weight: 600;
}
.weak-tag {
  margin: 0 8px 8px 0;
}
.qf-title {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-right: 12px;
}
.qf-q {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.qf-body {
  color: #606266;
  line-height: 1.7;
}
.qf-answer {
  margin-bottom: 8px;
}
</style>
