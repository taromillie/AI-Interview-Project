<template>
  <div class="salary-page">
    <div class="page-head">
      <div class="page-title">谈薪评估</div>
      <div class="page-desc">输入岗位、技能、年限与城市，AI 结合市场行情给出合理薪资区间与可执行的谈薪策略</div>
    </div>

    <!-- ============ 向导式输入 ============ -->
    <template v-if="!result">
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
          <!-- ① 岗位 + 城市 -->
          <section v-if="currentStep === 1" key="s1" class="w-card">
            <div class="w-head">
              <span class="w-ico"><el-icon :size="20"><Money /></el-icon></span>
              <div>
                <div class="w-title">你要评估什么岗位？</div>
                <div class="w-desc">岗位与城市是薪资区间的两大基础变量</div>
              </div>
            </div>
            <el-form label-position="top">
              <el-form-item label="目标岗位" required>
                <el-input v-model="targetPosition" placeholder="如：后端开发工程师" @keyup.enter="goNext" />
              </el-form-item>
              <el-form-item label="工作城市" required>
                <el-select
                  v-model="city"
                  filterable
                  allow-create
                  default-first-option
                  placeholder="选择或输入城市"
                  class="full"
                >
                  <el-option v-for="c in commonCities" :key="c" :label="c" :value="c" />
                </el-select>
              </el-form-item>
            </el-form>
          </section>

          <!-- ② 技能 + 年限 -->
          <section v-else-if="currentStep === 2" key="s2" class="w-card">
            <div class="w-head">
              <span class="w-ico grad"><el-icon :size="20"><TrendCharts /></el-icon></span>
              <div>
                <div class="w-title">你的技能栈与经验</div>
                <div class="w-desc">技能栈直接影响定价，年限决定职级区间</div>
              </div>
            </div>
            <el-form label-position="top">
              <el-form-item label="技能栈">
                <el-select
                  v-model="skillStack"
                  multiple
                  filterable
                  allow-create
                  default-first-option
                  placeholder="输入后回车，或从列表选择"
                  class="full"
                >
                  <el-option v-for="s in commonSkills" :key="s" :label="s" :value="s" />
                </el-select>
              </el-form-item>
              <el-form-item label="工作年限" required>
                <el-input-number v-model="years" :min="0" :max="30" controls-position="right" class="full" />
              </el-form-item>
            </el-form>
          </section>

          <!-- ③ 简历 + 开始 -->
          <section v-else key="s3" class="w-card">
            <div class="w-head">
              <span class="w-ico green"><el-icon :size="20"><Document /></el-icon></span>
              <div>
                <div class="w-title">关联简历（选填）</div>
                <div class="w-desc">结合简历中的项目与职级，让评估更贴合真实情况</div>
              </div>
            </div>
            <el-form label-position="top">
              <el-form-item label="选择简历">
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

            <div class="start-summary">
              <span class="sum-item">
                <span class="sum-label">岗位</span>
                <b>{{ targetPosition }}</b>
              </span>
              <span class="sum-item">
                <span class="sum-label">城市</span>
                <b>{{ city }}</b>
              </span>
              <span class="sum-item">
                <span class="sum-label">年限</span>
                <b>{{ years }} 年</b>
              </span>
              <span class="sum-item">
                <span class="sum-label">技能</span>
                <b>{{ skillStack.length ? `${skillStack.length} 项` : '未填' }}</b>
              </span>
            </div>

            <template v-if="evals.length">
              <div class="history-title">历史评估（{{ evals.length }}）</div>
              <div class="history-list">
                <div
                  v-for="e in evals"
                  :key="e.id"
                  class="history-item"
                  @click="loadEval(e)"
                >
                  <div class="history-main">
                    <div class="history-route">{{ e.target_position }} · {{ e.city }} · {{ e.years }} 年</div>
                    <div class="history-preview">
                      {{ e.result.salary_range[0] }} ~ {{ e.result.salary_range[2] }} 元/月
                    </div>
                  </div>
                  <span class="history-time">{{ formatTime(e.created_at) }}</span>
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
            {{ currentStep === 1 ? (targetPosition || '输入目标岗位') : `${years} 年 · ${skillStack.length} 项技能` }}
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
          :loading="evaluating"
          :disabled="!targetPosition.trim() || !city.trim()"
          @click="runEvaluate"
        >
          <el-icon v-if="!evaluating" class="el-icon--left"><MagicStick /></el-icon>
          {{ evaluating ? 'AI 正在评估…' : '开始谈薪评估' }}
        </el-button>
      </div>
    </template>

    <!-- ============ 评估结果 ============ -->
    <template v-else>
      <div class="result-head">
        <div class="result-route">
          <span class="route-from">{{ result.target_position || targetPosition }}</span>
          <span class="route-arrow"><el-icon><Right /></el-icon></span>
          <span class="route-to">{{ result.city || city }}</span>
          <span class="route-sub">{{ result.years || years }} 年经验</span>
        </div>
        <div class="result-actions">
          <el-tag v-if="result.id" size="small" type="warning" effect="light">历史记录</el-tag>
          <el-tag v-else size="small" type="success" effect="light">本次评估</el-tag>
          <el-tag v-if="combinedResume" size="small" effect="plain">已结合简历</el-tag>
          <el-button size="small" @click="reset">
            <el-icon class="el-icon--left"><RefreshLeft /></el-icon>
            重新评估
          </el-button>
        </div>
      </div>

      <div class="result-grid">
        <div class="result-card salary-card">
          <div class="rc-head">
            <span class="rc-ico blue"><el-icon :size="16"><Money /></el-icon></span>
            <span class="rc-title">薪资区间（税前月薪）</span>
          </div>
          <div class="range-row">
            <div class="range-card">
              <div class="range-label">最低</div>
              <div class="range-value">{{ formatMoney(result.salary_range[0]) }}</div>
            </div>
            <div class="range-card main">
              <div class="range-label">合理中位</div>
              <div class="range-value">{{ formatMoney(result.salary_range[1]) }}</div>
            </div>
            <div class="range-card">
              <div class="range-label">最高</div>
              <div class="range-value">{{ formatMoney(result.salary_range[2]) }}</div>
            </div>
          </div>
        </div>

        <div class="result-card">
          <div class="rc-head">
            <span class="rc-ico orange"><el-icon :size="16"><Warning /></el-icon></span>
            <span class="rc-title">影响因素（{{ result.factors.length }}）</span>
          </div>
          <ul v-if="result.factors.length" class="factor-list">
            <li v-for="(f, i) in result.factors" :key="i">{{ f }}</li>
          </ul>
          <el-empty v-else description="暂无因素分析" :image-size="40" />
        </div>

        <div class="result-card">
          <div class="rc-head">
            <span class="rc-ico green"><el-icon :size="16"><TrendCharts /></el-icon></span>
            <span class="rc-title">谈薪策略（{{ result.strategy.length }}）</span>
          </div>
          <el-timeline v-if="result.strategy.length">
            <el-timeline-item v-for="(s, i) in result.strategy" :key="i" type="primary">
              <span class="strategy-item">{{ s }}</span>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无策略建议" :image-size="40" />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Document,
  MagicStick,
  Money,
  RefreshLeft,
  Right,
  TrendCharts,
  Warning,
} from '@element-plus/icons-vue'
import { listResumes } from '@/api/diagnostic'
import { listSalaryEvals, salaryEvaluate } from '@/api/salary'

const wizardSteps = [
  { id: 1, title: '岗位城市' },
  { id: 2, title: '技能年限' },
  { id: 3, title: '简历确认' },
]
const currentStep = ref(1)
const maxStep = ref(1)

const targetPosition = ref('')
const skillStack = ref([])
const years = ref(3)
const city = ref('')
const resumeId = ref(0) // 0=最近一份，-1=不结合，>0=指定简历
const evaluating = ref(false)
const result = ref(null)
const evals = ref([])
const resumes = ref([])

const canNext = computed(() => {
  if (currentStep.value === 1) return !!targetPosition.value.trim() && !!city.value.trim()
  return true
})

const combinedResume = computed(() => {
  if (!result.value || resumeId.value === -1) return ''
  if (resumeId.value > 0) {
    const r = resumes.value.find((x) => x.id === resumeId.value)
    return r ? r.name || `简历 #${r.id}` : ''
  }
  return '最近一份简历'
})

const commonSkills = ['Python', 'Java', 'Go', 'JavaScript', 'TypeScript', 'Vue', 'React', 'Node.js', 'MySQL', 'Redis', 'MongoDB', 'Docker', 'Kubernetes', 'Linux', 'Git', 'FastAPI', 'Spring Boot', '机器学习', '数据分析']
const commonCities = ['北京', '上海', '深圳', '广州', '杭州', '南京', '苏州', '成都', '武汉', '西安', '长沙', '重庆']

function goNext() {
  if (currentStep.value === 1 && (!targetPosition.value.trim() || !city.value.trim())) {
    ElMessage.warning('请填写目标岗位与城市')
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

async function loadEvals() {
  try {
    evals.value = await listSalaryEvals()
  } catch { /* 忽略 */ }
}

function loadEval(e) {
  targetPosition.value = e.target_position
  city.value = e.city
  years.value = e.years
  skillStack.value = e.skill_stack || []
  result.value = {
    id: e.id,
    target_position: e.target_position,
    city: e.city,
    years: e.years,
    salary_range: e.result.salary_range,
    factors: e.result.factors,
    strategy: e.result.strategy,
  }
  ElMessage.info(`已加载 ${e.target_position} 的评估记录`)
}

async function runEvaluate() {
  evaluating.value = true
  try {
    result.value = await salaryEvaluate({
      target_position: targetPosition.value.trim(),
      city: city.value.trim(),
      years: years.value,
      skill_stack: skillStack.value,
      resume_id: resumeId.value === 0 ? undefined : resumeId.value,
    })
    ElMessage.success('谈薪评估完成')
    await loadEvals()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message || '评估失败')
  } finally {
    evaluating.value = false
  }
}

async function loadResumes() {
  try {
    resumes.value = await listResumes()
  } catch { /* 忽略 */ }
}

function formatMoney(v) {
  return `¥${Number(v || 0).toLocaleString()}`
}

function formatTime(dt) {
  if (!dt) return ''
  const d = new Date(dt)
  if (Number.isNaN(d.getTime())) return String(dt)
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

onMounted(() => {
  loadEvals()
  loadResumes()
})
</script>

<style scoped>
.salary-page {
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
  font-size: 13px;
  font-weight: 600;
  color: var(--app-text);
  margin-bottom: 3px;
}
.history-preview {
  font-size: 12px;
  color: var(--app-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 380px;
}
.history-time {
  font-size: 12px;
  color: #c0c4cc;
  flex-shrink: 0;
}

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
}
.route-from { color: var(--app-text-secondary); }
.route-arrow { color: #1a1a1a; display: flex; }
.route-to {
  color: #1a1a1a;
  background: rgba(26, 26, 26, 0.08);
  padding: 2px 10px;
  border-radius: 8px;
}
.route-sub {
  font-size: 13px;
  font-weight: 500;
  color: var(--app-text-muted);
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
.salary-card { grid-column: 1 / -1; }
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
.rc-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--app-text);
}
.range-row {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}
.range-card {
  flex: 1;
  padding: 18px 12px;
  text-align: center;
  border: 1px solid var(--app-border);
  border-radius: 12px;
  background: #fafaf9;
}
.range-card.main {
  border-color: #1a1a1a;
  background: rgba(26, 26, 26, 0.06);
  transform: scale(1.04);
}
.range-label {
  font-size: 12px;
  color: var(--app-text-muted);
  margin-bottom: 6px;
}
.range-value {
  font-size: 22px;
  font-weight: 800;
  color: var(--app-text);
}
.range-card.main .range-value {
  color: #1a1a1a;
}
.factor-list {
  margin: 0;
  padding-left: 20px;
}
.factor-list li {
  font-size: 13px;
  color: var(--app-text-secondary);
  line-height: 2;
}
.strategy-item {
  font-size: 13px;
  color: #1f2937;
  line-height: 1.6;
}
</style>
