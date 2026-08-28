<template>
  <div class="career-page">
    <div class="page-head">
      <div class="page-title">转行诊断</div>
      <div class="page-desc">输入当前岗位与目标岗位，AI 对比任职要求，输出可迁移技能、技能缺口与学习路径</div>
    </div>

    <!-- ============ 向导式输入 ============ -->
    <template v-if="!result">
      <!-- 步骤条 -->
      <WizardStepper :steps="wizardSteps" :current-step="currentStep" :max-step="maxStep" @step="goStep" />

      <div class="w-body">
        <transition name="wizard" mode="out-in">
          <!-- ① 当前岗位 -->
          <section v-if="currentStep === 1" key="s1" class="w-card">
            <div class="w-head">
              <span class="w-ico"><el-icon :size="20"><Position /></el-icon></span>
              <div>
                <div class="w-title">你现在从事什么岗位？</div>
                <div class="w-desc">基于当前岗位的技能沉淀，评估可迁移能力</div>
              </div>
            </div>
            <el-form label-position="top">
              <el-form-item label="当前岗位">
                <el-input
                  v-model="fromPosition"
                  placeholder="如：测试工程师、运营专员、教师…"
                  maxlength="60"
                  @keyup.enter="goNext"
                />
              </el-form-item>
            </el-form>
            <div class="quick-row">
              <span class="quick-label">热门</span>
              <button
                v-for="q in hotFrom"
                :key="q"
                class="quick-chip"
                :class="{ on: fromPosition === q }"
                @click="fromPosition = q"
              >
                {{ q }}
              </button>
            </div>
          </section>

          <!-- ② 目标岗位 -->
          <section v-else-if="currentStep === 2" key="s2" class="w-card">
            <div class="w-head">
              <span class="w-ico grad"><el-icon :size="20"><Aim /></el-icon></span>
              <div>
                <div class="w-title">你想转到什么岗位？</div>
                <div class="w-desc">AI 将对比两者的任职要求，输出你的技能差距</div>
              </div>
            </div>
            <el-form label-position="top">
              <el-form-item label="目标岗位">
                <el-input
                  v-model="toPosition"
                  placeholder="如：后端开发工程师、产品经理、数据分析师…"
                  maxlength="60"
                  @keyup.enter="goNext"
                />
              </el-form-item>
            </el-form>
            <div class="quick-row">
              <span class="quick-label">热门</span>
              <button
                v-for="q in hotTo"
                :key="q"
                class="quick-chip"
                :class="{ on: toPosition === q }"
                @click="toPosition = q"
              >
                {{ q }}
              </button>
            </div>
          </section>

          <!-- ③ 简历 + 开始 -->
          <section v-else key="s3" class="w-card">
            <div class="w-head">
              <span class="w-ico green"><el-icon :size="20"><Document /></el-icon></span>
              <div>
                <div class="w-title">关联简历（可选）</div>
                <div class="w-desc">上传过简历后关联一份，让诊断基于真实经历更精准</div>
              </div>
            </div>
            <el-form label-position="top">
              <el-form-item label="选择简历">
                <el-select v-model="resumeId" clearable placeholder="不选则仅基于岗位判断" class="full">
                  <el-option
                    v-for="r in resumes"
                    :key="r.id"
                    :label="`${formatTime(r.created_at)}（${r.skills.length} 项技能）`"
                    :value="r.id"
                  />
                </el-select>
              </el-form-item>
            </el-form>

            <div class="start-summary">
              <span class="sum-item">
                <span class="sum-label">当前岗位</span>
                <b>{{ fromPosition }}</b>
              </span>
              <span class="sum-item">
                <span class="sum-label">目标岗位</span>
                <b>{{ toPosition }}</b>
              </span>
              <span class="sum-item">
                <span class="sum-label">简历</span>
                <b>{{ resumeLabel || '未关联' }}</b>
              </span>
            </div>

            <template v-if="plans.length">
              <div class="history-title">历史诊断（{{ plans.length }}）</div>
              <div class="history-list">
                <div
                  v-for="p in plans"
                  :key="p.id"
                  class="history-item"
                  @click="loadPlan(p)"
                >
                  <div class="history-main">
                    <div class="history-route">{{ p.from_position }} → {{ p.to_position }}</div>
                    <div class="history-preview">{{ p.summary }}</div>
                  </div>
                  <span class="history-time">{{ formatTime(p.created_at) }}</span>
                </div>
              </div>
            </template>
          </section>
        </transition>
      </div>

      <!-- 底部导航 -->
      <div class="w-nav">
        <el-button v-if="currentStep > 1" size="large" @click="goPrev">
          <el-icon><ArrowLeft /></el-icon>
          <span class="nav-text">上一步</span>
        </el-button>
        <div class="w-nav-spacer"></div>
        <template v-if="currentStep < 3">
          <div class="nav-hint">
            {{ currentStep === 1 ? (fromPosition || '输入当前岗位') : (toPosition || '输入目标岗位') }}
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
          :loading="diagnosing"
          :disabled="!canStart"
          @click="runDiagnosis"
        >
          <el-icon v-if="!diagnosing" class="el-icon--left"><MagicStick /></el-icon>
          {{ diagnosing ? 'AI 正在对比分析…' : '开始转行诊断' }}
        </el-button>
      </div>
    </template>

    <!-- ============ 诊断结果 ============ -->
    <template v-else>
      <div class="result-head">
        <div class="result-route">
          <span class="route-from">{{ result.from_position }}</span>
          <span class="route-arrow"><el-icon><Right /></el-icon></span>
          <span class="route-to">{{ result.to_position }}</span>
        </div>
        <div class="result-actions">
          <el-tag v-if="result.id" size="small" type="warning" effect="light">历史记录</el-tag>
          <el-tag v-else size="small" type="success" effect="light">本次诊断</el-tag>
          <el-button size="small" @click="reset">
            <el-icon class="el-icon--left"><RefreshLeft /></el-icon>
            重新诊断
          </el-button>
        </div>
      </div>

      <div class="result-grid">
        <!-- 概览 -->
        <div class="result-card summary-card">
          <div class="rc-head">
            <span class="rc-ico blue"><el-icon :size="16"><MagicStick /></el-icon></span>
            <span class="rc-title">诊断结论</span>
          </div>
          <p class="rc-summary">{{ result.summary }}</p>
        </div>

        <!-- 可迁移技能 -->
        <div class="result-card">
          <div class="rc-head">
            <span class="rc-ico green"><el-icon :size="16"><TrendCharts /></el-icon></span>
            <span class="rc-title">可迁移技能（{{ result.transferable.length }}）</span>
          </div>
          <div v-if="result.transferable.length" class="transfer-list">
            <div v-for="(t, i) in result.transferable" :key="i" class="transfer-item">
              <div class="transfer-skill">{{ t.skill }}</div>
              <div class="transfer-evidence">{{ t.evidence }}</div>
            </div>
          </div>
          <el-empty v-else description="暂无可迁移技能分析" :image-size="40" />
        </div>

        <!-- 技能缺口 -->
        <div class="result-card">
          <div class="rc-head">
            <span class="rc-ico orange"><el-icon :size="16"><Warning /></el-icon></span>
            <span class="rc-title">技能缺口（{{ result.gaps.length }}）</span>
          </div>
          <el-table :data="result.gaps" size="small" empty-text="未识别到明显技能缺口">
            <el-table-column prop="skill" label="缺失技能" min-width="110" />
            <el-table-column label="要求程度" width="86">
              <template #default="{ row }">
                <el-tag :type="levelTag(row.level)" size="small">{{ row.level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="suggestion" label="补足建议" />
          </el-table>
        </div>

        <!-- 学习路径 -->
        <div class="result-card">
          <div class="rc-head">
            <span class="rc-ico purple"><el-icon :size="16"><Odometer /></el-icon></span>
            <span class="rc-title">学习路径（{{ result.roadmap.length }}）</span>
          </div>
          <el-timeline v-if="result.roadmap.length">
            <el-timeline-item
              v-for="(r, i) in result.roadmap"
              :key="i"
              :timestamp="r.duration"
              :type="i === result.roadmap.length - 1 ? 'success' : 'primary'"
            >
              <div class="roadmap-stage">{{ r.stage }}</div>
              <div class="roadmap-action">{{ r.action }}</div>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无学习路径" :image-size="40" />
        </div>

        <!-- 过渡项目 -->
        <div v-if="result.transition_projects?.length" class="result-card projects-card">
          <div class="rc-head">
            <span class="rc-ico pink"><el-icon :size="16"><FolderOpened /></el-icon></span>
            <span class="rc-title">过渡项目推荐（{{ result.transition_projects.length }}）</span>
          </div>
          <div class="proj-tip">
            以下项目可直接写进简历，用于证明目标岗位技能，弥补经历空白。
          </div>
          <div v-for="(pr, i) in result.transition_projects" :key="i" class="project-item">
            <div class="project-head">
              <span class="project-name">{{ pr.name }}</span>
              <el-tag size="small" effect="plain">{{ pr.duration }}</el-tag>
            </div>
            <div class="project-desc">{{ pr.description }}</div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Aim,
  ArrowLeft,
  ArrowRight,
  Check,
  Document,
  FolderOpened,
  MagicStick,
  Odometer,
  Position,
  RefreshLeft,
  Right,
  TrendCharts,
  Warning,
} from '@element-plus/icons-vue'
import { careerDiagnosis, listCareerPlans } from '@/api/career'
import { listResumes } from '@/api/diagnostic'
import { formatDateTime } from '@/utils/time'
import WizardStepper from '@/components/wizard/WizardStepper.vue'

const wizardSteps = [
  { id: 1, title: '当前岗位' },
  { id: 2, title: '目标岗位' },
  { id: 3, title: '简历确认' },
]
const currentStep = ref(1)
const maxStep = ref(1)

const fromPosition = ref('')
const toPosition = ref('')
const resumeId = ref(null)
const diagnosing = ref(false)
const result = ref(null)
const resumes = ref([])
const plans = ref([])

const hotFrom = ['测试工程师', '运维工程师', '运营专员', '教师', '销售顾问']
const hotTo = ['后端开发工程师', '前端开发工程师', '产品经理', '数据分析师', '算法工程师']

const canNext = computed(() => {
  if (currentStep.value === 1) return !!fromPosition.value.trim()
  if (currentStep.value === 2) return !!toPosition.value.trim()
  return true
})
const canStart = computed(() => fromPosition.value.trim() && toPosition.value.trim())
const resumeLabel = computed(() => {
  const r = resumes.value.find((x) => x.id === resumeId.value)
  return r ? r.name || `简历 #${r.id}` : ''
})

function goNext() {
  if (currentStep.value === 1 && !fromPosition.value.trim()) {
    ElMessage.warning('请输入当前岗位')
    return
  }
  if (currentStep.value === 2 && !toPosition.value.trim()) {
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

function reset() {
  result.value = null
  currentStep.value = 1
  maxStep.value = 1
}

async function runDiagnosis() {
  diagnosing.value = true
  try {
    result.value = await careerDiagnosis({
      from_position: fromPosition.value.trim(),
      to_position: toPosition.value.trim(),
      resume_id: resumeId.value,
    })
    ElMessage.success('转行诊断完成')
    await loadPlans()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message || '诊断失败')
  } finally {
    diagnosing.value = false
  }
}

function loadPlan(p) {
  result.value = p
  ElMessage.info(`已加载 ${p.from_position} → ${p.to_position} 的诊断记录`)
}

async function loadResumes() {
  try {
    resumes.value = await listResumes()
  } catch { /* 忽略 */ }
}

async function loadPlans() {
  try {
    plans.value = await listCareerPlans()
  } catch { /* 忽略 */ }
}

function formatTime(dt) {
  return formatDateTime(dt)
}

function levelTag(level) {
  if (level === '精通') return 'danger'
  if (level === '熟练') return 'warning'
  return 'info'
}

onMounted(() => {
  loadResumes()
  loadPlans()
})
</script>

<style scoped>
.career-page {
  max-width: 880px;
  margin: 0 auto;
}

/* ── 页头 ── */
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

/* ── 步骤条（与面试向导一致） ── */
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

/* ── 步骤卡片 ── */
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

/* ── 快捷岗位 chips ── */
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

/* ── 底部导航 ── */
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

/* ── 切换动画 ── */
.wizard-enter-active { transition: all 0.32s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1)); }
.wizard-leave-active { transition: all 0.18s ease; }
.wizard-enter-from { opacity: 0; transform: translateY(18px) scale(0.99); }
.wizard-leave-to { opacity: 0; transform: translateY(-10px) scale(0.99); }

/* ── 开始摘要 ── */
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
.sum-item {
  font-size: 13px;
  color: var(--app-text-secondary);
}
.sum-label {
  margin-right: 6px;
}
.sum-item b {
  color: var(--app-text);
}

/* ── 历史诊断 ── */
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
  font-size: 13px;
  font-weight: 600;
  color: var(--app-text);
  margin-bottom: 3px;
}
.history-preview {
  font-size: 12px;
  color: var(--app-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 360px;
}
.history-time {
  font-size: 12px;
  color: #c0c4cc;
  flex-shrink: 0;
}

/* ── 结果视图 ── */
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
  font-size: 17px;
  font-weight: 800;
}
.route-from { color: var(--app-text-secondary); }
.route-arrow { color: #1a1a1a; display: flex; }
.route-to {
  color: #1a1a1a;
  background: rgba(26, 26, 26, 0.08);
  padding: 2px 10px;
  border-radius: 8px;
}
.result-actions {
  display: flex;
  align-items: center;
  gap: 10px;
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
.summary-card,
.projects-card {
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
.rc-ico.orange { background: linear-gradient(135deg, #f59e0b, #ea580c); }
.rc-ico.purple { background: linear-gradient(135deg, #444444, #333333); }
.rc-ico.pink { background: linear-gradient(135deg, #ec4899, #db2777); }
.rc-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--app-text);
}
.rc-summary {
  margin: 0;
  font-size: 14px;
  line-height: 1.8;
  color: var(--app-text-secondary);
}

.transfer-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.transfer-item {
  padding: 10px 12px;
  border: 1px solid var(--app-border);
  border-radius: 10px;
  background: #fafaf9;
}
.transfer-skill {
  font-size: 13px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 3px;
}
.transfer-evidence {
  font-size: 12px;
  color: var(--app-text-secondary);
  line-height: 1.6;
}

.roadmap-stage {
  font-weight: 600;
  color: var(--app-text);
}
.roadmap-action {
  font-size: 13px;
  color: var(--app-text-secondary);
  margin-top: 2px;
}

.proj-tip {
  font-size: 12px;
  color: #b45309;
  background: rgba(245, 158, 11, 0.1);
  border-radius: 8px;
  padding: 8px 12px;
  margin-bottom: 12px;
}
.project-item {
  border: 1px solid var(--app-border);
  border-radius: 10px;
  padding: 10px 12px;
  margin-bottom: 8px;
  background: #fafaf9;
}
.project-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}
.project-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--app-text);
}
.project-desc {
  font-size: 12px;
  color: var(--app-text-secondary);
  line-height: 1.7;
}
</style>
