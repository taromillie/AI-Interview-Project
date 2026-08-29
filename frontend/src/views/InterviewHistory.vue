<template>
  <div class="page">
    <div class="page-head">
      <div>
        <div class="page-title">面试记录</div>
        <div class="page-desc">每场面试的完整问答与评估都会自动保存，点击任意一场即可复盘。</div>
      </div>
      <el-button type="primary" @click="router.push({ name: 'interview' })">
        <el-icon style="margin-right: 4px"><Plus /></el-icon>
        开始新面试
      </el-button>
    </div>

    <div v-loading="loading" class="list-wrap">
      <el-empty v-if="!loading && !interviews.length" description="还没有面试记录，去完成一场模拟面试吧" />
      <div v-else class="cards">
        <div v-for="it in interviews" :key="it.id" class="card" @click="openDetail(it)">
          <div class="card-main">
            <div class="card-title">
              {{ it.position_name || it.target_position || '未指定岗位' }}
              <el-tag v-if="it.report_id" size="small" type="success" effect="light">已复盘</el-tag>
              <el-tag v-else-if="it.status === 'reported'" size="small" type="warning" effect="light">已结束</el-tag>
              <el-tag v-else size="small" effect="plain" type="info">{{ statusText(it.status) }}</el-tag>
            </div>
            <div class="card-meta">
              <span>{{ typeText(it.interview_type) }}</span>
              <span class="dot">·</span>
              <span>{{ it.message_count }} 条对话</span>
              <span class="dot">·</span>
              <span>{{ formatTime(it.created_at) }}</span>
            </div>
          </div>
          <div class="card-side">
            <div v-if="it.overall_score != null" class="score-box">
              <div class="score">{{ Math.round(it.overall_score) }}</div>
              <div class="score-label">分</div>
            </div>
            <el-button size="small" type="primary" plain @click.stop="openDetail(it)">查看</el-button>
            <el-button v-if="it.report_id" size="small" @click.stop="goReport(it.report_id)">复盘报告</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 详情抽屉 -->
    <el-drawer
      v-model="drawer"
      size="min(920px, 92vw)"
      :title="drawerTitle"
      destroy-on-close
    >
      <div v-loading="loadingDetail" class="detail">
        <template v-if="detail">
          <!-- 概览 -->
          <div class="overview">
            <div class="ov-left">
              <div class="ov-pos">{{ detail.position_name || detail.target_position || '未指定岗位' }}</div>
              <div class="ov-meta">
                <span>{{ typeText(detail.interview_type) }}</span>
                <span class="dot">·</span>
                <span>{{ formatTime(detail.created_at) }}</span>
                <span class="dot">·</span>
                <span>{{ detail.messages.length }} 条对话</span>
              </div>
            </div>
            <div v-if="detail.overall_score != null" class="ov-score">
              <div class="score">{{ Math.round(detail.overall_score) }}</div>
              <div class="score-label">综合得分</div>
            </div>
          </div>

          <!-- 问答时间线 -->
          <div class="section-title">逐轮问答</div>
          <el-timeline class="qa-timeline">
            <el-timeline-item
              v-for="m in detail.messages"
              :key="m.id"
              :type="m.role === 'assistant' ? 'primary' : 'success'"
              :hollow="m.role === 'user'"
            >
              <div class="msg" :class="m.role">
                <div class="msg-head">
                  <span class="msg-role">{{ m.role === 'assistant' ? '面试官' : '我的回答' }}</span>
                  <el-tag v-if="m.role === 'assistant' && m.strategy && m.strategy !== 'none'" size="small" effect="plain">
                    {{ strategyText(m.strategy) }}
                  </el-tag>
                </div>
                <div class="msg-body">{{ m.content }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>

          <!-- 复盘报告 -->
          <template v-if="detail.report">
            <div class="section-title">复盘报告</div>
            <div class="report-card">
              <div class="rep-dims">
                <div v-for="(v, k) in detail.report.dimensions" :key="k" class="dim-row">
                  <span class="dim-name">{{ DIM_LABELS[k] || k }}</span>
                  <el-progress :percentage="Math.round(v)" :stroke-width="8" :show-text="false" />
                  <span class="dim-val">{{ Math.round(v) }}</span>
                </div>
              </div>
              <div v-if="detail.report.weak_points?.length" class="rep-weak">
                <div class="weak-title">面试官关注的弱点</div>
                <el-tag v-for="w in detail.report.weak_points" :key="w" size="small" type="danger" effect="plain" class="weak-tag">
                  {{ w }}
                </el-tag>
              </div>
              <div class="rep-qa">
                <div v-for="(item, idx) in detail.report.question_feedback" :key="idx" class="rep-item">
                  <div class="rep-item-head">
                    <span class="rep-q">Q{{ idx + 1 }} · {{ item.question }}</span>
                    <el-tag size="small" :type="scoreType(item.score)">{{ item.score }} 分</el-tag>
                  </div>
                  <div class="rep-answer">答：{{ item.answer }}</div>
                  <div class="rep-comment">点评：{{ item.comment }}</div>
                </div>
              </div>
              <el-button type="primary" plain class="rep-cta" @click="goReport(detail.report.id)">
                查看完整复盘报告
              </el-button>
            </div>
          </template>
          <div v-else class="no-report">
            本场面试尚未生成报告，结束面试后自动生成复盘报告。
            <el-button size="small" type="primary" plain @click="router.push({ name: 'interview' })">去完成面试</el-button>
          </div>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { Plus, Tickets } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getInterviewDetail, listInterviews } from '@/api/interview'
import { formatDateTime } from '@/utils/time'

const router = useRouter()
const interviews = ref([])
const loading = ref(false)
const drawer = ref(false)
const detail = ref(null)
const loadingDetail = ref(false)

const DIM_LABELS = { tech: '技术深度', expression: '表达清晰', logic: '逻辑思维', project: '项目颗粒度' }

const drawerTitle = computed(() => {
  const d = detail.value
  if (!d) return '面试详情'
  const pos = d.position_name || d.target_position || '未指定岗位'
  return `${pos} · ${formatTime(d.created_at)}`
})

function formatTime(s) {
  return formatDateTime(s)
}

function statusText(s) {
  return (
    {
      created: '待开始',
      warming: '进行中',
      asking: '进行中',
      decide_next: '进行中',
      finishing: '生成报告中',
      reported: '已结束',
    }[s] || s
  )
}

function typeText(t) {
  return { normal: '标准面试', switch: '转行面试', salary: '谈薪面试' }[t] || t
}

function strategyText(s) {
  return (
    {
      deep_dive: '深挖追问',
      remedy: '补问',
      switch_topic: '换题',
      project_probe: '项目追问',
      none: '',
    }[s] || s
  )
}

function scoreType(score) {
  if (score == null) return 'info'
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

async function load() {
  loading.value = true
  try {
    interviews.value = await listInterviews()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function openDetail(it) {
  drawer.value = true
  loadingDetail.value = true
  detail.value = null
  try {
    detail.value = await getInterviewDetail(it.id)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message || '加载详情失败')
  } finally {
    loadingDetail.value = false
  }
}

function goReport(reportId) {
  drawer.value = false
  router.push({ name: 'report', params: { id: reportId } })
}

onMounted(load)
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
}
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: var(--app-radius-lg, 16px);
  padding: 14px 20px;
  box-shadow: var(--app-shadow-sm, 0 1px 3px rgba(20, 20, 20, 0.06));
}
.page-title {
  font-size: 17px;
  font-weight: 800;
  color: var(--app-text);
}
.page-desc {
  font-size: 12px;
  color: var(--app-text-muted);
  margin-top: 2px;
}
.list-wrap {
  min-height: 200px;
}
.cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: #fff;
  border: 1px solid #eef2f7;
  border-radius: 12px;
  padding: 16px 20px;
  cursor: pointer;
  transition: transform 160ms var(--ease-out), box-shadow 0.2s var(--ease-out), border-color 0.2s ease;
}
.card:active {
  transform: scale(0.99);
}
@media (hover: hover) and (pointer: fine) {
  .card:hover {
    box-shadow: 0 6px 20px rgba(20, 20, 20, 0.08);
    transform: translateY(-2px);
    border-color: rgba(26, 26, 26, 0.3);
  }
}
.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 700;
  color: var(--app-text);
}
.card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--app-text-muted);
  margin-top: 6px;
}
.card-side {
  display: flex;
  align-items: center;
  gap: 10px;
}
.score-box {
  display: flex;
  align-items: baseline;
  gap: 2px;
}
.score {
  font-size: 24px;
  font-weight: 800;
  color: #1a1a1a;
}
.score-label {
  font-size: 12px;
  color: var(--app-text-muted);
}
.dot {
  color: var(--app-border-strong);
}

/* 抽屉内 */
.detail {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.overview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(120deg, #fafaf9 0%, #f0f0ee 100%);
  border: 1px solid #f0f0ee;
  border-radius: 12px;
  padding: 16px 18px;
}
.ov-pos {
  font-size: 16px;
  font-weight: 800;
  color: var(--app-text);
}
.ov-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--app-text-secondary);
  margin-top: 6px;
}
.ov-score {
  display: flex;
  align-items: baseline;
  gap: 4px;
}
.ov-score .score {
  font-size: 32px;
}
.section-title {
  font-size: 15px;
  font-weight: 800;
  color: var(--app-text);
  border-left: 3px solid #1a1a1a;
  padding-left: 10px;
}
.msg {
  background: #fafaf9;
  border-radius: 10px;
  padding: 10px 14px;
  border: 1px solid #eef2f7;
}
.msg.user {
  background: #f0f0ee;
  border-color: #f0f0ee;
}
.msg-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.msg-role {
  font-size: 12px;
  font-weight: 700;
  color: var(--app-text-secondary);
}
.msg.user .msg-role {
  color: #1a1a1a;
}
.msg-body {
  font-size: 14px;
  line-height: 1.7;
  color: var(--app-text);
  white-space: pre-wrap;
  word-break: break-word;
}
.report-card {
  background: #fff;
  border: 1px solid #eef2f7;
  border-radius: 12px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.dim-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.dim-name {
  width: 72px;
  font-size: 13px;
  font-weight: 600;
  color: var(--app-text-secondary);
}
.dim-val {
  width: 28px;
  text-align: right;
  font-size: 13px;
  font-weight: 700;
  color: #1a1a1a;
}
.weak-title {
  font-size: 13px;
  font-weight: 700;
  color: #b91c1c;
  margin-bottom: 8px;
}
.weak-tag {
  margin-right: 6px;
  margin-bottom: 6px;
}
.rep-item {
  border: 1px solid #eef2f7;
  border-radius: 10px;
  padding: 12px 14px;
  background: #fbfdff;
}
.rep-item + .rep-item {
  margin-top: 10px;
}
.rep-item-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.rep-q {
  font-size: 14px;
  font-weight: 700;
  color: var(--app-text);
}
.rep-answer {
  font-size: 13px;
  color: var(--app-text-secondary);
  margin-top: 8px;
  white-space: pre-wrap;
  word-break: break-word;
}
.rep-comment {
  font-size: 13px;
  color: #3a3a3a;
  margin-top: 6px;
  white-space: pre-wrap;
  word-break: break-word;
}
.rep-cta {
  align-self: flex-start;
}
.no-report {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fffbeb;
  border: 1px dashed #fcd34d;
  border-radius: 12px;
  padding: 16px 18px;
  color: #92400e;
  font-size: 14px;
}

/* ==================== 深色液态玻璃覆盖 ==================== */
.page-head {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-highlight), var(--app-shadow-sm);
}
.card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-highlight);
}
@media (hover: hover) and (pointer: fine) {
  .card:hover {
    box-shadow: var(--glass-highlight), var(--glass-shadow);
    border-color: rgba(90, 208, 230, 0.4);
  }
}
.score { color: var(--app-cyan); }
.overview {
  background: var(--app-brand-soft);
  border: 1px solid rgba(90, 208, 230, 0.25);
}
.section-title {
  border-left: 3px solid var(--app-cyan);
}
.msg {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--app-border);
}
.msg.user {
  background: var(--app-brand-soft);
  border-color: rgba(90, 208, 230, 0.25);
}
.msg.user .msg-role { color: var(--app-cyan); }
.report-card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
}
.dim-val { color: var(--app-cyan); }
.weak-title { color: var(--app-danger); }
.rep-item {
  border: 1px solid var(--app-border);
  background: rgba(255, 255, 255, 0.03);
}
.rep-comment { color: var(--app-text-secondary); }
.no-report {
  background: rgba(242, 193, 78, 0.1);
  border: 1px dashed rgba(242, 193, 78, 0.5);
  color: var(--app-amber);
}
</style>