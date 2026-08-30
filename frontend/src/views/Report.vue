<template>
  <div class="report-page">
    <div class="page-banner">
      <div class="banner-left">
        <div class="banner-icon">
          <el-icon :size="24"><DataAnalysis /></el-icon>
        </div>
        <div>
          <div class="banner-title">面试复盘报告</div>
          <div class="banner-desc">四维度评分、逐题批改与提升建议，让每一场面试都沉淀为下一次的底气。</div>
        </div>
      </div>
      <div class="banner-actions">
        <el-button type="primary" @click="router.push({ name: 'interview' })">
          <el-icon style="margin-right: 4px"><Plus /></el-icon>
          再来一场面试
        </el-button>
      </div>
    </div>
    <el-card v-loading="loading">

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
        <el-alert
          v-if="isGenerating"
          title="报告正在后台生成，页面将自动刷新，请稍候…"
          type="info"
          :closable="false"
          show-icon
        />
        <el-alert v-else :title="report.summary || '暂无总评'" type="info" :closable="false" />

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

        <!-- 知识覆盖统计 -->
        <template v-if="report.coverage">
          <el-divider content-position="left">知识覆盖统计</el-divider>
          <el-row :gutter="16">
            <el-col :span="12">
              <div class="cov-block covered">
                <div class="cov-title">
                  <el-icon><CircleCheckFilled /></el-icon>
                  已覆盖且表现较好（{{ report.coverage.covered?.length || 0 }}）
                </div>
                <el-tag
                  v-for="(c, i) in report.coverage.covered || []"
                  :key="i"
                  type="success"
                  effect="plain"
                  class="cov-tag"
                >
                  {{ c }}
                </el-tag>
                <el-empty v-if="!(report.coverage.covered || []).length" description="暂无" :image-size="40" />
              </div>
            </el-col>
            <el-col :span="12">
              <div class="cov-block uncovered">
                <div class="cov-title">
                  <el-icon><WarningFilled /></el-icon>
                  未覆盖 / 薄弱（{{ report.coverage.uncovered?.length || 0 }}）
                </div>
                <el-tag
                  v-for="(u, i) in report.coverage.uncovered || []"
                  :key="i"
                  type="danger"
                  effect="plain"
                  class="cov-tag clickable"
                  :title="`去题库练习：${u}`"
                  @click="goPractice(u)"
                >
                  {{ u }}
                </el-tag>
                <div v-if="(report.coverage.uncovered || []).length" class="cov-hint">
                  <el-icon><Pointer /></el-icon>
                  点击上方知识点可直达题库练习
                </div>
                <el-empty v-if="!(report.coverage.uncovered || []).length" description="暂无" :image-size="40" />
              </div>
            </el-col>
          </el-row>
        </template>

        <!-- 学习路线推荐 -->
        <template v-if="report.learning_path?.length">
          <el-divider content-position="left">个性化学习路线</el-divider>
          <el-steps :active="report.learning_path.length" align-center finish-status="success" class="lp-steps">
            <el-step
              v-for="(lp, i) in report.learning_path"
              :key="i"
              :title="lp.phase"
              :description="lp.duration"
            />
          </el-steps>
          <div v-for="(lp, i) in report.learning_path" :key="i" class="lp-item">
            <span class="lp-phase">【{{ lp.phase }}】{{ lp.duration }}</span>
            <span class="lp-action">{{ lp.action }}</span>
          </div>
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
import { DataAnalysis, Plus, Pointer } from '@element-plus/icons-vue'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getReport } from '@/api/report'

const route = useRoute()
const router = useRouter()

const DIMS = { tech: '技术能力', expression: '表达沟通', logic: '逻辑思维', project: '项目经验' }

// 与后端 REPORT_PENDING_SUMMARY 保持一致：总评为此值表示报告仍在后台生成
const PENDING_SUMMARY = '报告生成中，请稍后刷新查看…'

const loading = ref(false)
const report = ref(null)
let pollTimer = null

const isGenerating = computed(() => report.value?.summary === PENDING_SUMMARY)

function goPractice(knowledge) {
  router.push({ name: 'questions', query: { keyword: knowledge } })
}

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
    // 报告仍在后台生成：轮询直到完成
    if (report.value?.summary === PENDING_SUMMARY) {
      startPolling(id)
    }
  } catch {
    report.value = null
  } finally {
    loading.value = false
  }
}

function startPolling(id) {
  if (pollTimer) return
  pollTimer = setInterval(async () => {
    try {
      const r = await getReport(id)
      if (r?.summary !== PENDING_SUMMARY) {
        report.value = r
        clearInterval(pollTimer)
        pollTimer = null
      }
    } catch {
      // 瞬时网络错误忽略，继续轮询
    }
  }, 2500)
}

onMounted(load)

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})
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
.cov-block {
  border-radius: 8px;
  padding: 12px 14px;
  min-height: 80px;
}
.cov-block.covered {
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
}
.cov-tag.clickable {
  cursor: pointer;
  transition: all 0.2s ease;
}
.cov-tag.clickable:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.2);
}
.cov-hint {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--app-text-muted);
  font-size: 12px;
}
.cov-block.uncovered {
  background: #fef0f0;
  border: 1px solid #fde2e2;
}
.cov-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 10px;
  color: #303133;
}
.cov-tag {
  margin: 0 8px 8px 0;
}
.lp-steps {
  margin-bottom: 18px;
}
.lp-item {
  display: flex;
  gap: 8px;
  font-size: 13px;
  line-height: 1.8;
  color: #606266;
}
.lp-phase {
  font-weight: 700;
  color: #303133;
  white-space: nowrap;
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

/* ==================== 深色液态玻璃覆盖 ==================== */
.overall-num { color: var(--app-cyan); }
.cov-block.covered {
  background: rgba(67, 217, 163, 0.1);
  border: 1px solid rgba(67, 217, 163, 0.25);
}
.cov-block.uncovered {
  background: rgba(255, 107, 122, 0.1);
  border: 1px solid rgba(255, 107, 122, 0.25);
}
.cov-title { color: var(--app-text); }
.lp-item { color: var(--app-text-secondary); }
.lp-phase { color: var(--app-text); }
.qf-body { color: var(--app-text-secondary); }
</style>