<template>
  <div class="study-page">
    <div class="page-head">
      <div class="page-title">备战日历</div>
      <div class="page-desc">AI 结合你的能力画像缺口与目标岗位，自动生成「冲刺备战计划」，逐日勾选任务跟踪进度</div>
    </div>

    <!-- ============ 向导式输入 ============ -->
    <template v-if="!current">
      <div class="wizard">
        <template v-for="(s, i) in wizardSteps" :key="s.id">
          <button
            class="w-step"
            :class="{ active: currentStep === s.id, done: maxStep > s.id }"
            :disabled="s.id > maxStep && s.id !== currentStep + 1"
            @click="goStep(s.id)"
          >
            <span class="w-dot">
              <el-icon v-if="maxStep > s.id" :size="14"><Check /></el-icon>
              <template v-else>{{ s.id }}</template>
            </span>
            <span class="w-label">{{ s.title }}</span>
          </button>
          <span
            v-if="i < wizardSteps.length - 1"
            class="w-line"
            :class="{ done: maxStep > wizardSteps[i].id }"
          ></span>
        </template>
      </div>

      <div class="w-body">
        <transition name="wizard" mode="out-in">
          <!-- ① 目标岗位 -->
          <section v-if="currentStep === 1" key="s1" class="w-card">
            <div class="w-head">
              <span class="w-ico"><el-icon :size="20"><Aim /></el-icon></span>
              <div>
                <div class="w-title">备战目标岗位是什么？</div>
                <div class="w-desc">计划将围绕该岗位的核心知识体系展开</div>
              </div>
            </div>
            <el-form label-position="top">
              <el-form-item label="目标岗位">
                <el-input v-model="targetPosition" placeholder="如：Java 后端开发工程师" @keyup.enter="goNext" />
              </el-form-item>
            </el-form>
            <div class="quick-row">
              <span class="quick-label">热门</span>
              <button
                v-for="q in hotPositions"
                :key="q"
                class="quick-chip"
                :class="{ on: targetPosition === q }"
                @click="targetPosition = q"
              >
                {{ q }}
              </button>
            </div>
          </section>

          <!-- ② 天数 + 简历 -->
          <section v-else-if="currentStep === 2" key="s2" class="w-card">
            <div class="w-head">
              <span class="w-ico grad"><el-icon :size="20"><Calendar /></el-icon></span>
              <div>
                <div class="w-title">规划备战周期</div>
                <div class="w-desc">按你的面试时间倒推，3~60 天均可</div>
              </div>
            </div>
            <el-form label-position="top">
              <el-form-item label="备战天数">
                <el-input-number v-model="days" :min="3" :max="60" controls-position="right" class="full" />
              </el-form-item>
              <el-form-item label="结合简历（选填）">
                <el-select v-model="resumeId" class="full" placeholder="选择要结合的简历">
                  <el-option label="最近一份简历" :value="0" />
                  <el-option label="不结合简历" :value="-1" />
                  <el-option
                    v-for="r in resumes"
                    :key="r.id"
                    :label="r.name || `简历 #${r.id}`"
                    :value="r.id"
                  />
                </el-select>
              </el-form-item>
            </el-form>
          </section>

          <!-- ③ 历史 + 开始 -->
          <section v-else key="s3" class="w-card">
            <div class="w-head">
              <span class="w-ico green"><el-icon :size="20"><Calendar /></el-icon></span>
              <div>
                <div class="w-title">确认并生成</div>
                <div class="w-desc">也可以从历史计划中直接查看进度</div>
              </div>
            </div>

            <div class="start-summary">
              <span class="sum-item">
                <span class="sum-label">岗位</span>
                <b>{{ targetPosition }}</b>
              </span>
              <span class="sum-item">
                <span class="sum-label">周期</span>
                <b>{{ days }} 天</b>
              </span>
              <span class="sum-item">
                <span class="sum-label">简历</span>
                <b>{{ resumeId === -1 ? '未结合' : (resumeId > 0 ? resumes.find((r) => r.id === resumeId)?.name || `简历 #${resumeId}` : '最近一份') }}</b>
              </span>
            </div>

            <template v-if="plans.length">
              <div class="history-title">历史计划（{{ plans.length }}）</div>
              <div class="history-list">
                <div
                  v-for="p in plans"
                  :key="p.id"
                  class="history-item"
                  @click="selectPlan(p)"
                >
                  <div class="history-main">
                    <div class="history-route">
                      {{ p.title }}
                      <el-tag v-if="p.status === 'completed'" size="small" type="success">已完成</el-tag>
                    </div>
                    <el-progress :percentage="progressOf(p)" :stroke-width="6" class="mini-progress" />
                  </div>
                  <span class="history-time">{{ formatTime(p.created_at) }}</span>
                </div>
              </div>
            </template>
          </section>
        </transition>
      </div>

      <div class="w-nav">
        <el-button v-if="currentStep > 1" size="large" @click="goPrev">
          <el-icon><ArrowLeft /></el-icon>
          <span class="nav-text">上一步</span>
        </el-button>
        <div class="w-nav-spacer"></div>
        <template v-if="currentStep < 3">
          <div class="nav-hint">
            {{ currentStep === 1 ? (targetPosition || '输入目标岗位') : `${days} 天备战周期` }}
          </div>
          <el-button type="primary" size="large" :disabled="!canNext" @click="goNext">
            下一步
            <el-icon class="el-icon--right"><ArrowRight /></el-icon>
          </el-button>
        </template>
        <el-button
          v-else
          type="primary"
          size="large"
          :loading="generating"
          :disabled="!targetPosition.trim()"
          @click="runGenerate"
        >
          <el-icon v-if="!generating" class="el-icon--left"><MagicStick /></el-icon>
          {{ generating ? 'AI 正在生成计划…' : 'AI 生成备战计划' }}
        </el-button>
      </div>
    </template>

    <!-- ============ 计划视图 ============ -->
    <template v-else>
      <div class="result-head">
        <div class="result-route">
          <span class="route-from">{{ current.title }}</span>
          <el-tag v-if="current.status === 'completed'" size="small" type="success">已完成</el-tag>
          <span class="route-sub">{{ current.summary }}</span>
        </div>
        <div class="result-actions">
          <el-button size="small" @click="current = null">
            <el-icon class="el-icon--left"><RefreshLeft /></el-icon>
            新建计划
          </el-button>
          <el-button size="small" type="danger" plain @click="removePlan">删除计划</el-button>
        </div>
      </div>

      <div class="result-grid">
        <div class="result-card progress-card">
          <div class="rc-head">
            <span class="rc-ico blue"><el-icon :size="16"><Odometer /></el-icon></span>
            <span class="rc-title">备战进度</span>
          </div>
          <div class="progress-row">
            <el-progress type="dashboard" :percentage="currentProgress" :width="120" :color="progressColor" />
            <div class="progress-info">
              <div class="pi-line">总天数：{{ current.days }} 天</div>
              <div class="pi-line">已完成：{{ doneCount }} / {{ current.days }}</div>
              <div class="pi-line">阶段：{{ current.status === 'completed' ? '全部完成' : '备战中' }}</div>
            </div>
          </div>
        </div>

        <div class="result-card tasks-card">
          <div class="rc-head">
            <span class="rc-ico green"><el-icon :size="16"><Calendar /></el-icon></span>
            <span class="rc-title">每日任务（{{ sortedTasks.length }} 天）</span>
          </div>
          <el-timeline class="task-timeline">
            <el-timeline-item
              v-for="t in sortedTasks"
              :key="t.day"
              :type="t.done ? 'success' : 'primary'"
              :hollow="!t.done"
            >
              <div class="task-item" :class="{ done: t.done }">
                <div class="task-head">
                  <span class="task-day">Day {{ t.day }}</span>
                  <span class="task-title">{{ t.title }}</span>
                  <el-checkbox
                    :model-value="Boolean(t.done)"
                    @change="(v) => toggleTask(t.day, v)"
                  >
                    {{ t.done ? '已完成' : '标记完成' }}
                  </el-checkbox>
                </div>
                <div class="task-desc">{{ t.description }}</div>
                <div v-if="t.topics && t.topics.length" class="task-topics">
                  <el-tag
                    v-for="tp in t.topics"
                    :key="tp"
                    size="small"
                    effect="plain"
                    class="topic-tag"
                  >
                    {{ tp }}
                  </el-tag>
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Aim,
  ArrowLeft,
  ArrowRight,
  Calendar,
  Check,
  MagicStick,
  Odometer,
  RefreshLeft,
} from '@element-plus/icons-vue'
import { listResumes } from '@/api/diagnostic'
import {
  deleteStudyPlan,
  generateStudyPlan,
  listStudyPlans,
  toggleStudyPlanTask,
} from '@/api/studyPlan'

const wizardSteps = [
  { id: 1, title: '目标岗位' },
  { id: 2, title: '备战周期' },
  { id: 3, title: '确认生成' },
]
const currentStep = ref(1)
const maxStep = ref(1)

const targetPosition = ref('')
const days = ref(14)
const resumeId = ref(0)
const generating = ref(false)
const plans = ref([])
const current = ref(null)
const resumes = ref([])

const hotPositions = ['Java 后端开发工程师', '前端开发工程师', '算法工程师', '产品经理', '数据分析师']

const canNext = computed(() => {
  if (currentStep.value === 1) return !!targetPosition.value.trim()
  return true
})

const sortedTasks = computed(() => {
  const tasks = (current.value?.tasks || []).slice()
  return tasks.sort((a, b) => a.day - b.day)
})

const doneCount = computed(() => (current.value?.tasks || []).filter((t) => t.done).length)
const currentProgress = computed(() => {
  if (!current.value || !current.value.days) return 0
  return Math.round((doneCount.value / current.value.days) * 100)
})
const progressColor = computed(() => {
  const p = currentProgress.value
  return p >= 100 ? '#10b981' : '#1a1a1a'
})

function progressOf(p) {
  const tasks = p.tasks || []
  if (!tasks.length) return 0
  return Math.round((tasks.filter((t) => t.done).length / tasks.length) * 100)
}

function goNext() {
  if (currentStep.value === 1 && !targetPosition.value.trim()) {
    ElMessage.warning('请输入目标岗位')
    return
  }
  if (currentStep.value < 3) {
    currentStep.value++
    maxStep.value = Math.max(maxStep.value, currentStep.value)
  }
}

function goPrev() {
  if (currentStep.value > 1) currentStep.value--
}

function goStep(n) {
  if (n === currentStep.value) return
  if (n <= maxStep.value || n === currentStep.value + 1) {
    if (n === currentStep.value + 1) goNext()
    else currentStep.value = n
  }
}

async function loadPlans() {
  try {
    plans.value = await listStudyPlans()
  } catch { /* 忽略 */ }
}

async function loadResumes() {
  try {
    resumes.value = await listResumes()
  } catch { /* 忽略 */ }
}

async function runGenerate() {
  generating.value = true
  try {
    current.value = await generateStudyPlan({
      target_position: targetPosition.value.trim(),
      days: days.value,
      resume_id: resumeId.value === 0 ? undefined : resumeId.value,
    })
    ElMessage.success('备战计划已生成')
    await loadPlans()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message || '生成失败')
  } finally {
    generating.value = false
  }
}

function selectPlan(p) {
  current.value = p
}

async function toggleTask(day, done) {
  if (!current.value) return
  current.value = await toggleStudyPlanTask(current.value.id, day, Boolean(done))
  await loadPlans()
}

async function removePlan() {
  if (!current.value) return
  await ElMessageBox.confirm('确定删除该备战计划？', '提示', { type: 'warning' })
  await deleteStudyPlan(current.value.id)
  current.value = null
  ElMessage.success('已删除')
  await loadPlans()
}

function formatTime(dt) {
  if (!dt) return ''
  const d = new Date(dt)
  if (Number.isNaN(d.getTime())) return String(dt)
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

onMounted(() => {
  loadPlans()
  loadResumes()
})
</script>

<style scoped>
.study-page {
  max-width: 880px;
  margin: 0 auto;
}
.page-head {
  padding: 4px 0 18px;
  text-align: center;
}
.page-title {
  font-size: 26px;
  font-weight: 800;
  color: var(--app-text);
}
.page-desc {
  margin-top: 6px;
  font-size: 13px;
  color: var(--app-text-secondary);
}

/* 步骤条 */
.wizard {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 18px;
  padding: 16px 26px;
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: var(--app-radius-lg, 16px);
  box-shadow: var(--app-shadow-sm, 0 1px 3px rgba(20, 20, 20, 0.06));
}
.w-step {
  display: flex;
  align-items: center;
  gap: 10px;
  border: none;
  background: none;
  padding: 4px 6px;
  cursor: pointer;
  border-radius: 10px;
  transition: transform 160ms var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.w-step:active { transform: scale(0.96); }
.w-step:disabled { cursor: default; opacity: 0.55; }
.w-dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: var(--app-text-muted);
  background: #f4f4f2;
  border: 2px solid var(--app-border);
  transition: all 0.3s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.w-step.active .w-dot {
  color: #fff;
  background: linear-gradient(135deg, #1a1a1a, #1a1a1a);
  border-color: transparent;
  box-shadow: 0 0 0 5px rgba(26, 26, 26, 0.14), 0 6px 16px rgba(26, 26, 26, 0.28);
}
.w-step.done .w-dot {
  color: #fff;
  background: #10b981;
  border-color: transparent;
  box-shadow: 0 0 0 5px rgba(16, 185, 129, 0.14);
}
.w-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text-secondary);
  transition: color 0.25s ease;
}
.w-step.active .w-label { color: #1a1a1a; }
.w-step.done .w-label { color: var(--app-text); }
.w-line {
  width: 52px;
  height: 3px;
  border-radius: 2px;
  background: var(--app-border);
  margin: 0 12px;
  transition: background 0.3s ease;
}
.w-line.done { background: linear-gradient(90deg, #10b981, #34d399); }

/* 步骤卡片 */
.w-body { margin-bottom: 0; }
.w-card {
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: var(--app-radius-lg, 16px);
  box-shadow: var(--app-shadow-md, 0 4px 16px rgba(20, 20, 20, 0.08));
  padding: 24px 28px 26px;
}
.w-head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 18px;
}
.w-ico {
  width: 44px;
  height: 44px;
  border-radius: 13px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: linear-gradient(135deg, #1a1a1a, #1a1a1a);
  box-shadow: 0 6px 14px rgba(26, 26, 26, 0.25);
}
.w-ico.grad {
  background: linear-gradient(135deg, #444444, #333333);
  box-shadow: 0 6px 14px rgba(139, 92, 246, 0.28);
}
.w-ico.green {
  background: linear-gradient(135deg, #10b981, #059669);
  box-shadow: 0 6px 14px rgba(16, 185, 129, 0.25);
}
.w-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--app-text);
}
.w-desc {
  font-size: 13px;
  color: var(--app-text-secondary);
  margin-top: 2px;
}

/* 快捷 chips */
.quick-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}
.quick-label {
  font-size: 12px;
  color: var(--app-text-muted);
}
.quick-chip {
  border: 1px solid var(--app-border);
  background: #fff;
  color: var(--app-text-secondary);
  font-size: 13px;
  padding: 5px 13px;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.18s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.quick-chip:hover {
  border-color: #1a1a1a;
  color: #1a1a1a;
}
.quick-chip.on {
  background: #1a1a1a;
  border-color: #1a1a1a;
  color: #fff;
  font-weight: 600;
}

/* 底部导航 */
.w-nav {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.w-nav-spacer { flex: 1; }
.nav-text { margin: 0 4px; }
.nav-hint {
  font-size: 12px;
  color: var(--app-text-muted);
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.full { width: 100%; }

.wizard-enter-active { transition: all 0.32s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1)); }
.wizard-leave-active { transition: all 0.18s ease; }
.wizard-enter-from { opacity: 0; transform: translateY(18px) scale(0.99); }
.wizard-leave-to { opacity: 0; transform: translateY(-10px) scale(0.99); }

/* 摘要 */
.start-summary {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
  background: #fafaf9;
  border: 1px dashed #dbe3ef;
  border-radius: 12px;
  padding: 12px 16px;
  margin-top: 8px;
}
.sum-item { font-size: 13px; color: var(--app-text-secondary); }
.sum-label { margin-right: 6px; }
.sum-item b { color: var(--app-text); }

/* 历史 */
.history-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--app-text);
  margin: 18px 0 10px;
}
.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 14px;
  border: 1px solid var(--app-border);
  border-radius: 12px;
  cursor: pointer;
  background: #fff;
  transition: transform 160ms var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1)), border-color 0.2s;
}
.history-item:active { transform: scale(0.99); }
.history-item:hover { border-color: rgba(26, 26, 26, 0.4); }
.history-main { flex: 1; min-width: 0; }
.history-route {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--app-text);
  margin-bottom: 4px;
}
.history-time {
  font-size: 12px;
  color: #c0c4cc;
  flex-shrink: 0;
}
.mini-progress { width: 100%; }

/* 结果 */
.result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: var(--app-radius-lg, 16px);
  padding: 14px 20px;
  box-shadow: var(--app-shadow-sm, 0 1px 3px rgba(20, 20, 20, 0.06));
}
.result-route {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 800;
  min-width: 0;
}
.route-from {
  color: #1a1a1a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.route-sub {
  font-size: 12px;
  font-weight: 400;
  color: var(--app-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.result-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.result-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.result-card {
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: var(--app-radius-lg, 16px);
  box-shadow: var(--app-shadow-sm, 0 1px 3px rgba(20, 20, 20, 0.06));
  padding: 18px 20px;
}
.tasks-card {
  grid-column: 1 / -1;
}
.rc-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.rc-ico {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.rc-ico.blue { background: linear-gradient(135deg, #1a1a1a, #1a1a1a); }
.rc-ico.green { background: linear-gradient(135deg, #10b981, #059669); }
.rc-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--app-text);
}
.progress-row {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 6px 0 8px;
}
.progress-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.pi-line {
  font-size: 13px;
  color: var(--app-text-secondary);
}
.task-timeline {
  margin-top: 8px;
}
.task-item {
  padding: 4px 0;
}
.task-item.done .task-title {
  text-decoration: line-through;
  color: var(--app-text-muted);
}
.task-head {
  display: flex;
  align-items: center;
  gap: 10px;
}
.task-day {
  font-size: 12px;
  font-weight: 700;
  color: #1a1a1a;
  background: rgba(26, 26, 26, 0.08);
  border-radius: 6px;
  padding: 2px 8px;
  flex-shrink: 0;
}
.task-title {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}
.task-desc {
  margin-top: 6px;
  font-size: 13px;
  color: var(--app-text-secondary);
  line-height: 1.6;
}
.task-topics {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.topic-tag {
  font-size: 12px;
}
</style>
