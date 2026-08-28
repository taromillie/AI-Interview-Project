<template>
  <div class="real-page">
    <div class="page-head">
      <div class="page-title">真实面试复盘</div>
      <div class="page-desc">把真实面试的问答记录下来，AI 逐题批改、维度评分并给出改进建议，让每次面试都成为成长燃料</div>
    </div>

    <!-- ============ 向导式录入 ============ -->
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
          <!-- ① 面试信息 -->
          <section v-if="currentStep === 1" key="s1" class="w-card">
            <div class="w-head">
              <span class="w-ico"><el-icon :size="20"><OfficeBuilding /></el-icon></span>
              <div>
                <div class="w-title">这次面试的基本信息</div>
                <div class="w-desc">用于记录归档与复盘标注</div>
              </div>
            </div>
            <el-form label-position="top">
              <div class="two-col">
                <el-form-item label="公司" required>
                  <el-input v-model="form.company" placeholder="如：字节跳动" />
                </el-form-item>
                <el-form-item label="岗位">
                  <el-input v-model="form.position" placeholder="如：后端开发工程师" />
                </el-form-item>
              </div>
              <div class="two-col">
                <el-form-item label="面试日期">
                  <el-date-picker
                    v-model="form.interview_date"
                    type="date"
                    value-format="YYYY-MM-DD"
                    placeholder="选择日期"
                    class="full"
                  />
                </el-form-item>
                <el-form-item label="轮次">
                  <el-select v-model="form.round_type" class="full" placeholder="选择轮次">
                    <el-option v-for="r in roundTypes" :key="r" :label="r" :value="r" />
                  </el-select>
                </el-form-item>
              </div>
              <el-form-item label="面试备注">
                <el-input
                  v-model="form.notes"
                  type="textarea"
                  :rows="3"
                  placeholder="如：一面是简历深挖，被追问了项目细节…"
                />
              </el-form-item>
            </el-form>
          </section>

          <!-- ② 问答录入 -->
          <section v-else-if="currentStep === 2" key="s2" class="w-card">
            <div class="w-head">
              <span class="w-ico grad"><el-icon :size="20"><ChatDotSquare /></el-icon></span>
              <div>
                <div class="w-title">问答记录（可增删）</div>
                <div class="w-desc">尽量回忆完整回答，AI 批改会更准确</div>
              </div>
            </div>
            <div
              v-for="(item, idx) in form.items"
              :key="idx"
              class="qa-item"
            >
              <div class="qa-head">
                <span class="qa-no">Q{{ idx + 1 }}</span>
                <el-button
                  size="small"
                  type="danger"
                  text
                  :disabled="form.items.length <= 1"
                  @click="removeItem(idx)"
                >
                  删除
                </el-button>
              </div>
              <el-input
                v-model="item.question"
                placeholder="面试问题"
                class="qa-question"
              />
              <el-input
                v-model="item.answer"
                type="textarea"
                :rows="2"
                placeholder="你的回答（尽量回忆完整）"
                class="qa-answer"
              />
            </div>
            <el-button class="add-qa" @click="addItem">+ 添加一条问答</el-button>
          </section>

          <!-- ③ 历史 + 保存 -->
          <section v-else key="s3" class="w-card">
            <div class="w-head">
              <span class="w-ico green"><el-icon :size="20"><Document /></el-icon></span>
              <div>
                <div class="w-title">确认保存</div>
                <div class="w-desc">保存后即可生成 AI 复盘，也可从历史记录直接打开</div>
              </div>
            </div>

            <div class="start-summary">
              <span class="sum-item">
                <span class="sum-label">公司</span>
                <b>{{ form.company || '—' }}</b>
              </span>
              <span class="sum-item">
                <span class="sum-label">岗位</span>
                <b>{{ form.position || '—' }}</b>
              </span>
              <span class="sum-item">
                <span class="sum-label">问答</span>
                <b>{{ form.items.filter((i) => i.question.trim()).length }} 条</b>
              </span>
            </div>

            <template v-if="records.length">
              <div class="history-title">历史记录（{{ records.length }}）</div>
              <div class="history-list">
                <div
                  v-for="r in records"
                  :key="r.id"
                  class="history-item"
                  @click="selectRecord(r)"
                >
                  <div class="history-main">
                    <div class="history-route">
                      {{ r.company }}
                      <el-tag v-if="r.position" size="small" effect="plain">{{ r.position }}</el-tag>
                      <el-tag
                        v-if="r.review && r.review.overall_score"
                        size="small"
                        type="warning"
                      >
                        {{ r.review.overall_score }} 分
                      </el-tag>
                    </div>
                    <div class="history-preview">
                      {{ r.round_type || '未填轮次' }} · {{ r.interview_date || '未填日期' }}
                    </div>
                  </div>
                  <el-button size="small" text type="danger" @click.stop="removeRecord(r)">
                    删除
                  </el-button>
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
            {{ currentStep === 1 ? (form.company || '输入公司名称') : `${form.items.filter((i) => i.question.trim()).length} 条问答` }}
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
          :disabled="!form.company.trim()"
          @click="saveInterview"
        >
          <el-icon class="el-icon--left"><Check /></el-icon>
          保存并生成复盘
        </el-button>
      </div>
    </template>

    <!-- ============ AI 复盘 ============ -->
    <template v-else>
      <div class="result-head">
        <div class="result-route">
          <span class="route-from">{{ current.company }}</span>
          <el-tag v-if="current.position" size="small" effect="plain">{{ current.position }}</el-tag>
          <span class="route-sub">{{ current.round_type || '未填轮次' }} · {{ current.interview_date || '未填日期' }}</span>
        </div>
        <div class="result-actions">
          <el-button size="small" type="primary" :loading="reviewing" @click="runReview">
            <el-icon v-if="!reviewing" class="el-icon--left"><MagicStick /></el-icon>
            生成/刷新 AI 复盘
          </el-button>
          <el-button size="small" @click="current = null">
            <el-icon class="el-icon--left"><RefreshLeft /></el-icon>
            返回记录
          </el-button>
        </div>
      </div>

      <template v-if="current.review && current.review.item_reviews">
        <div class="result-grid">
          <div class="result-card score-card">
            <div class="rc-head">
              <span class="rc-ico blue"><el-icon :size="16"><DataAnalysis /></el-icon></span>
              <span class="rc-title">综合评分</span>
            </div>
            <div class="score-row">
              <el-progress
                type="dashboard"
                :percentage="Number(current.review.overall_score || 0)"
                :width="120"
                :color="scoreColor(current.review.overall_score)"
              />
              <div class="score-info">
                <div class="score-dim">
                  <span class="d-label">技术深度</span>
                  <el-progress
                    :percentage="Number(current.review.dimensions?.tech || 0)"
                    :stroke-width="8"
                    :color="scoreColor(current.review.dimensions?.tech)"
                  />
                </div>
                <div class="score-dim">
                  <span class="d-label">表达清晰</span>
                  <el-progress
                    :percentage="Number(current.review.dimensions?.expression || 0)"
                    :stroke-width="8"
                    :color="scoreColor(current.review.dimensions?.expression)"
                  />
                </div>
                <div class="score-dim">
                  <span class="d-label">逻辑结构</span>
                  <el-progress
                    :percentage="Number(current.review.dimensions?.logic || 0)"
                    :stroke-width="8"
                    :color="scoreColor(current.review.dimensions?.logic)"
                  />
                </div>
                <div class="score-dim">
                  <span class="d-label">项目经验</span>
                  <el-progress
                    :percentage="Number(current.review.dimensions?.project || 0)"
                    :stroke-width="8"
                    :color="scoreColor(current.review.dimensions?.project)"
                  />
                </div>
              </div>
            </div>
            <div v-if="current.review.summary" class="summary-box">
              {{ current.review.summary }}
            </div>
          </div>

          <div class="result-card">
            <div class="rc-head">
              <span class="rc-ico orange"><el-icon :size="16"><ChatDotSquare /></el-icon></span>
              <span class="rc-title">逐题批改（{{ current.review.item_reviews.length }}）</span>
            </div>
            <div v-for="(ir, i) in current.review.item_reviews" :key="i" class="item-review">
              <div class="ir-head">
                <span class="ir-q">Q{{ i + 1 }}：{{ ir.question }}</span>
                <el-tag size="small" :type="tagType(ir.score)">{{ ir.score }} 分</el-tag>
              </div>
              <div v-if="ir.comment" class="ir-comment">{{ ir.comment }}</div>
            </div>
          </div>

          <div class="result-card">
            <div class="rc-head">
              <span class="rc-ico green"><el-icon :size="16"><TrendCharts /></el-icon></span>
              <span class="rc-title">整体建议</span>
            </div>
            <el-timeline v-if="current.review.suggestions?.length">
              <el-timeline-item v-for="(s, i) in current.review.suggestions" :key="i" type="primary">
                <span class="suggestion-item">{{ s }}</span>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无建议" :image-size="40" />
          </div>
        </div>
      </template>

      <div v-else class="empty-review">
        <el-empty description="选择记录后，点击「生成 AI 复盘」" :image-size="80">
          <el-button type="primary" :loading="reviewing" @click="runReview">
            生成 AI 复盘
          </el-button>
        </el-empty>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  ArrowRight,
  ChatDotSquare,
  Check,
  DataAnalysis,
  Document,
  MagicStick,
  OfficeBuilding,
  RefreshLeft,
  TrendCharts,
} from '@element-plus/icons-vue'
import {
  createRealInterview,
  deleteRealInterview,
  getRealInterview,
  listRealInterviews,
  reviewRealInterview,
} from '@/api/realInterview'

const roundTypes = ['技术面', '业务面', 'HR 面', '交叉面', '终面']

const wizardSteps = [
  { id: 1, title: '面试信息' },
  { id: 2, title: '问答记录' },
  { id: 3, title: '确认保存' },
]
const currentStep = ref(1)
const maxStep = ref(1)

const form = ref({
  company: '',
  position: '',
  interview_date: '',
  round_type: '',
  notes: '',
  items: [{ question: '', answer: '' }],
})

const records = ref([])
const current = ref(null)
const reviewing = ref(false)

const canNext = computed(() => {
  if (currentStep.value === 1) return !!form.value.company.trim()
  return true
})

function addItem() {
  form.value.items.push({ question: '', answer: '' })
}
function removeItem(idx) {
  form.value.items.splice(idx, 1)
}

function goNext() {
  if (currentStep.value === 1 && !form.value.company.trim()) {
    ElMessage.warning('请输入公司名称')
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

async function loadRecords() {
  try {
    records.value = await listRealInterviews()
  } catch { /* 忽略 */ }
}

async function saveInterview() {
  const payload = {
    ...form.value,
    items: form.value.items.filter((i) => i.question.trim()),
  }
  if (!payload.items.length) {
    ElMessage.warning('请至少填写一条面试问题')
    return
  }
  await createRealInterview(payload)
  ElMessage.success('面试记录已保存，正在打开…')
  form.value.items = [{ question: '', answer: '' }]
  await loadRecords()
  const created = records.value[0]
  if (created) {
    current.value = await getRealInterview(created.id)
  }
}

async function selectRecord(r) {
  try {
    current.value = await getRealInterview(r.id)
  } catch { /* 忽略 */ }
}

async function runReview() {
  if (!current.value) return
  reviewing.value = true
  try {
    current.value = await reviewRealInterview(current.value.id)
    ElMessage.success('AI 复盘完成')
    await loadRecords()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message || '复盘生成失败')
  } finally {
    reviewing.value = false
  }
}

async function removeRecord(r) {
  await ElMessageBox.confirm(`确定删除 ${r.company} 的面试记录？`, '提示', { type: 'warning' })
  await deleteRealInterview(r.id)
  if (current.value && current.value.id === r.id) current.value = null
  ElMessage.success('已删除')
  await loadRecords()
}

function scoreColor(v) {
  const n = Number(v || 0)
  if (n >= 80) return '#67c23a'
  if (n >= 60) return '#e6a23c'
  return '#f56c6c'
}
function tagType(v) {
  const n = Number(v || 0)
  if (n >= 80) return 'success'
  if (n >= 60) return 'warning'
  return 'danger'
}

onMounted(() => {
  loadRecords()
})
</script>

<style scoped>
.real-page {
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
  color: #0f172a;
}
.page-desc {
  margin-top: 6px;
  font-size: 13px;
  color: #64748b;
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
  box-shadow: var(--app-shadow-sm, 0 1px 3px rgba(15, 23, 42, 0.06));
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
  color: #94a3b8;
  background: #f1f5f9;
  border: 2px solid #e2e8f0;
  transition: all 0.3s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.w-step.active .w-dot {
  color: #fff;
  background: linear-gradient(135deg, #2563eb, #4f46e5);
  border-color: transparent;
  box-shadow: 0 0 0 5px rgba(37, 99, 235, 0.14), 0 6px 16px rgba(37, 99, 235, 0.28);
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
  color: #64748b;
  transition: color 0.25s ease;
}
.w-step.active .w-label { color: #2563eb; }
.w-step.done .w-label { color: #0f172a; }
.w-line {
  width: 52px;
  height: 3px;
  border-radius: 2px;
  background: #e2e8f0;
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
  box-shadow: var(--app-shadow-md, 0 4px 16px rgba(15, 23, 42, 0.08));
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
  background: linear-gradient(135deg, #2563eb, #4f46e5);
  box-shadow: 0 6px 14px rgba(37, 99, 235, 0.25);
}
.w-ico.grad {
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  box-shadow: 0 6px 14px rgba(139, 92, 246, 0.28);
}
.w-ico.green {
  background: linear-gradient(135deg, #10b981, #059669);
  box-shadow: 0 6px 14px rgba(16, 185, 129, 0.25);
}
.w-title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}
.w-desc {
  font-size: 13px;
  color: #64748b;
  margin-top: 2px;
}

/* 表单 */
.full { width: 100%; }
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.qa-item {
  border: 1px solid #eef1f6;
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 10px;
  background: #fafbfe;
}
.qa-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.qa-no {
  font-size: 12px;
  font-weight: 700;
  color: #2563eb;
  background: rgba(37, 99, 235, 0.08);
  border-radius: 6px;
  padding: 2px 8px;
}
.qa-question {
  margin-bottom: 8px;
}
.add-qa {
  width: 100%;
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
  color: #94a3b8;
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wizard-enter-active { transition: all 0.32s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1)); }
.wizard-leave-active { transition: all 0.18s ease; }
.wizard-enter-from { opacity: 0; transform: translateY(18px) scale(0.99); }
.wizard-leave-to { opacity: 0; transform: translateY(-10px) scale(0.99); }

/* 摘要 */
.start-summary {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
  background: #f8fafc;
  border: 1px dashed #dbe3ef;
  border-radius: 12px;
  padding: 12px 16px;
  margin-top: 8px;
}
.sum-item { font-size: 13px; color: #64748b; }
.sum-label { margin-right: 6px; }
.sum-item b { color: #0f172a; }

/* 历史 */
.history-title {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
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
  border: 1px solid #eef1f6;
  border-radius: 12px;
  cursor: pointer;
  background: #fff;
  transition: transform 160ms var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1)), border-color 0.2s;
}
.history-item:active { transform: scale(0.99); }
.history-item:hover { border-color: rgba(37, 99, 235, 0.4); }
.history-main { flex: 1; min-width: 0; }
.history-route {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 4px;
}
.history-preview {
  font-size: 12px;
  color: #94a3b8;
}
.history-item :deep(.el-button + .el-button) { margin-left: 0; }

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
  box-shadow: var(--app-shadow-sm, 0 1px 3px rgba(15, 23, 42, 0.06));
}
.result-route {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 17px;
  font-weight: 800;
  min-width: 0;
}
.route-from { color: #2563eb; }
.route-sub {
  font-size: 12px;
  font-weight: 400;
  color: #94a3b8;
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
  box-shadow: var(--app-shadow-sm, 0 1px 3px rgba(15, 23, 42, 0.06));
  padding: 18px 20px;
}
.score-card { grid-column: 1 / -1; }
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
.rc-ico.blue { background: linear-gradient(135deg, #2563eb, #4f46e5); }
.rc-ico.orange { background: linear-gradient(135deg, #f59e0b, #ea580c); }
.rc-ico.green { background: linear-gradient(135deg, #10b981, #059669); }
.rc-title {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}
.score-row {
  display: flex;
  align-items: center;
  gap: 28px;
  padding: 4px 0 12px;
}
.score-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.score-dim {
  display: flex;
  align-items: center;
  gap: 12px;
}
.d-label {
  width: 70px;
  font-size: 12px;
  color: #606266;
  flex-shrink: 0;
}
.summary-box {
  background: rgba(37, 99, 235, 0.06);
  border: 1px solid rgba(37, 99, 235, 0.15);
  border-radius: 10px;
  padding: 12px 14px;
  font-size: 13px;
  color: #1f2937;
  line-height: 1.7;
  margin-top: 4px;
}
.item-review {
  border: 1px solid #eef1f6;
  border-radius: 10px;
  padding: 10px 12px;
  margin-bottom: 10px;
  background: #fafbfe;
}
.ir-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.ir-q {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
}
.ir-comment {
  margin-top: 8px;
  font-size: 13px;
  color: #475569;
  line-height: 1.7;
}
.suggestion-item {
  font-size: 13px;
  color: #1f2937;
  line-height: 1.6;
}
.empty-review {
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: var(--app-radius-lg, 16px);
  box-shadow: var(--app-shadow-sm, 0 1px 3px rgba(15, 23, 42, 0.06));
  padding: 40px 0;
}
</style>
