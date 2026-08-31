<template>
  <div class="offer-compare">
    <div class="page-banner">
      <div class="banner-left">
        <div class="banner-icon">
          <el-icon :size="24"><Trophy /></el-icon>
        </div>
        <div>
          <div class="banner-title">Offer 对比</div>
          <div class="banner-desc">录入多个 Offer，一键对比总包与 AI 综合建议</div>
        </div>
      </div>
    </div>

    <!-- 向导步骤条 -->
    <WizardStepper :steps="wizardSteps" :current-step="currentStep" :max-step="maxStep" @step="goStep" />

    <!-- 步骤内容 -->
    <div class="w-body">
      <transition name="wizard" mode="out-in">
        <!-- ① 录入 -->
        <section v-if="currentStep === 1" key="s1" class="w-card">
          <div class="w-head">
            <span class="w-ico"><el-icon :size="20"><Trophy /></el-icon></span>
            <div>
              <div class="w-title">录入你的 Offer</div>
              <div class="w-desc">至少添加 2 个 Offer 才能开始对比</div>
            </div>
            <button class="history-btn" @click="openHistory">
              <el-icon :size="15"><Clock /></el-icon>
              历史记录
            </button>
          </div>

          <el-form label-position="top">
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="公司" required>
                  <el-input v-model="form.company" placeholder="如：腾讯" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="岗位">
                  <el-input v-model="form.position" placeholder="如：后端开发" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="城市">
              <el-select
                v-model="form.city"
                filterable
                allow-create
                default-first-option
                class="full"
                placeholder="选择或输入"
              >
                <el-option v-for="c in commonCities" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="月薪（元）">
                  <el-input-number v-model="form.monthly_salary" :min="0" :step="1000" controls-position="right" class="full" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="年终奖（月）">
                  <el-input-number v-model="form.bonus_months" :min="0" :max="24" controls-position="right" class="full" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="股票年化（元/年）">
                  <el-input-number v-model="form.stock_value" :min="0" :step="5000" controls-position="right" class="full" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="生活平衡（1-10）">
                  <el-rate v-model="form.work_balance" :max="10" show-score />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="福利">
              <el-input v-model="form.benefits" placeholder="如：公积金 12%、餐补、房补、年假 15 天" />
            </el-form-item>
            <el-form-item label="备注">
              <el-input v-model="form.notes" placeholder="如：技术成长空间大 / 需要 995" />
            </el-form-item>
            <el-button type="primary" :disabled="!form.company.trim()" class="add-btn" @click="saveOffer">
              <el-icon class="el-icon--left"><Plus /></el-icon>
              添加 Offer
            </el-button>
          </el-form>

          <template v-if="offers.length">
            <el-divider content-position="left">
              已添加（{{ offers.length }} 个）
              <el-checkbox
                class="select-all"
                :model-value="selectedIds.length === offers.length"
                :indeterminate="selectedIds.length > 0 && selectedIds.length < offers.length"
                @change="toggleSelectAll"
              >全选</el-checkbox>
            </el-divider>
            <div class="offer-list">
              <div v-for="o in offers" :key="o.id" class="offer-item">
                <el-checkbox
                  :model-value="selectedIds.includes(o.id)"
                  class="offer-check"
                  @change="(v) => toggleSelect(o.id, v)"
                />
                <div class="offer-main">
                  <div class="offer-title">
                    {{ o.company }}
                    <el-tag v-if="o.position" size="small" effect="plain">{{ o.position }}</el-tag>
                    <el-tag v-if="o.city" size="small" effect="plain" type="info">{{ o.city }}</el-tag>
                  </div>
                  <div class="offer-sub">
                    月薪 {{ o.monthly_salary }} 元 × {{ 12 + o.bonus_months }} 薪
                    <template v-if="o.stock_value"> + 股票 {{ o.stock_value }} 元/年</template>
                    · 年化总包 {{ formatMoney(annualOf(o)) }}
                  </div>
                </div>
                <div class="offer-ops">
                  <el-tag size="small" :type="balanceType(o.work_balance)">
                    平衡 {{ o.work_balance }}/10
                  </el-tag>
                  <el-button size="small" text type="danger" @click="removeOffer(o)">删除</el-button>
                </div>
              </div>
            </div>
          </template>
          <el-empty v-else description="还没有 Offer，先在上方添加吧" :image-size="60" />
        </section>

        <!-- ② 结果 -->
        <section v-else key="s2" class="w-card">
          <div class="w-head">
            <span class="w-ico green"><el-icon :size="20"><DataAnalysis /></el-icon></span>
            <div>
              <div class="w-title">对比结果</div>
              <div class="w-desc">各维度对比与 AI 综合建议</div>
            </div>
          </div>

          <CompareResult
            v-if="compare.table.length"
            :table="compare.table"
            :analysis="compare.analysis"
          />

          <el-empty
            v-else
            description="录入至少 2 个 Offer 后勾选并点击「开始对比」"
            :image-size="80"
          />
        </section>
      </transition>
    </div>

    <!-- 底部导航 -->
    <div class="w-nav">
      <el-button v-if="currentStep === 2" size="large" @click="currentStep = 1">
        <el-icon><ArrowLeft /></el-icon>
        <span class="nav-text">返回修改</span>
      </el-button>
      <div class="w-nav-spacer"></div>
      <template v-if="currentStep === 1">
        <div class="nav-hint">
          <template v-if="selectedIds.length < 2">
            请至少勾选 2 个 Offer（已选 {{ selectedIds.length }} / {{ offers.length }}）
          </template>
          <template v-else>已选 {{ selectedIds.length }} 个，可以对比了</template>
        </div>
        <el-button
          type="primary"
          size="large"
          :loading="comparing"
          :disabled="selectedIds.length < 2"
          @click="goNext"
        >
          {{ comparing ? '正在对比…' : `对比所选 ${selectedIds.length} 个` }}
          <el-icon v-if="!comparing" class="el-icon--right"><MagicStick /></el-icon>
        </el-button>
      </template>
      <template v-else>
        <el-button type="primary" size="large" :loading="comparing" @click="runCompare">
          重新对比
          <el-icon class="el-icon--right"><RefreshRight /></el-icon>
        </el-button>
      </template>
    </div>

    <!-- 对比历史记录抽屉 -->
    <el-drawer v-model="historyOpen" title="对比历史记录" size="440px">
      <div v-loading="historyLoading" class="history-wrap">
        <template v-if="historyDetail">
          <div class="history-back" @click="historyDetail = null">← 返回列表</div>
          <div class="history-title">{{ historyDetail.company_names }}</div>
          <div class="history-time">{{ formatTime(historyDetail.created_at) }}</div>
          <CompareResult :table="historyDetail.table" :analysis="historyDetail.analysis" />
        </template>
        <template v-else>
          <el-empty v-if="!historyList.length" description="暂无对比历史" :image-size="60" />
          <div v-for="h in historyList" :key="h.id" class="history-item">
            <div class="history-main" @click="openHistoryDetail(h.id)">
              <div class="history-company">{{ h.company_names }}</div>
              <div class="history-time">{{ formatTime(h.created_at) }}</div>
            </div>
            <el-button size="small" text type="danger" @click="removeHistory(h.id)">删除</el-button>
          </div>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Check,
  Clock,
  DataAnalysis,
  MagicStick,
  Plus,
  RefreshRight,
  Trophy,
} from '@element-plus/icons-vue'
import {
  compareOffers,
  createOffer,
  deleteCompareHistory,
  deleteOffer,
  getCompareHistory,
  listCompareHistory,
  listOffers,
  streamCompareAnalysis,
} from '@/api/offer'
import CompareResult from '@/components/offer/CompareResult.vue'
import WizardStepper from '@/components/wizard/WizardStepper.vue'
import { formatDateTime } from '@/utils/time'

const commonCities = ['北京', '上海', '深圳', '广州', '杭州', '成都', '武汉', '南京', '苏州', '西安']

const form = reactive({
  company: '',
  position: '',
  city: '',
  monthly_salary: 0,
  bonus_months: 0,
  stock_value: 0,
  work_balance: 5,
  benefits: '',
  notes: '',
})

const offers = ref([])
const selectedIds = ref([])
const compare = ref({ table: [], analysis: '' })
const comparing = ref(false)

// ── 对比历史 ──
const historyOpen = ref(false)
const historyList = ref([])
const historyDetail = ref(null)
const historyLoading = ref(false)

// ── 向导状态 ──
const wizardSteps = [
  { id: 1, title: '录入 Offer' },
  { id: 2, title: '查看对比' },
]
const currentStep = ref(1)
const maxStep = ref(1)

function goNext() {
  if (selectedIds.value.length < 2) {
    ElMessage.warning('请至少勾选 2 个 Offer 再对比')
    return
  }
  runCompare()
}

function goStep(n) {
  if (n === currentStep.value) return
  if (n <= maxStep.value || n === currentStep.value + 1) {
    if (n === currentStep.value + 1) goNext()
    else currentStep.value = n
  }
}

function annualOf(o) {
  return o.monthly_salary * (12 + o.bonus_months) + o.stock_value
}

function formatMoney(v) {
  return `¥${Number(v || 0).toLocaleString()}`
}

function balanceType(v) {
  const n = Number(v || 0)
  if (n >= 8) return 'success'
  if (n >= 5) return 'warning'
  return 'danger'
}

// ── 多选 ──
function toggleSelect(id, checked) {
  if (checked) {
    if (!selectedIds.value.includes(id)) selectedIds.value.push(id)
  } else {
    selectedIds.value = selectedIds.value.filter((x) => x !== id)
  }
}

function toggleSelectAll() {
  if (selectedIds.value.length === offers.value.length) {
    selectedIds.value = []
  } else {
    selectedIds.value = offers.value.map((o) => o.id)
  }
}

async function loadOffers() {
  try {
    offers.value = await listOffers()
    // 过滤掉已被删除的勾选，避免提交失效 id
    const valid = new Set(offers.value.map((o) => o.id))
    selectedIds.value = selectedIds.value.filter((id) => valid.has(id))
  } catch {
    /* 拦截器已统一提示 */
  }
}

// ── 对比历史 ──
async function openHistory() {
  historyOpen.value = true
  historyDetail.value = null
  historyLoading.value = true
  try {
    historyList.value = await listCompareHistory()
  } finally {
    historyLoading.value = false
  }
}

async function openHistoryDetail(id) {
  historyLoading.value = true
  try {
    historyDetail.value = await getCompareHistory(id)
  } finally {
    historyLoading.value = false
  }
}

async function removeHistory(id) {
  try {
    await ElMessageBox.confirm('确定删除这条对比历史？', '提示', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch {
    return
  }
  await deleteCompareHistory(id)
  ElMessage.success('已删除')
  historyList.value = historyList.value.filter((h) => h.id !== id)
}

function formatTime(t) {
  if (!t) return ''
  // 后端统一存 UTC naive 时间，走 utils/time 的 UTC 修正，避免本地时区差 8 小时
  return formatDateTime(t)
}

async function saveOffer() {
  const payload = { ...form }
  await createOffer(payload)
  ElMessage.success('Offer 已添加')
  Object.assign(form, {
    company: '',
    position: '',
    city: '',
    monthly_salary: 0,
    bonus_months: 0,
    stock_value: 0,
    work_balance: 5,
    benefits: '',
    notes: '',
  })
  await loadOffers()
}

async function removeOffer(o) {
  try {
    await ElMessageBox.confirm(`确定删除 ${o.company} 的 Offer？`, '提示', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch {
    return
  }
  await deleteOffer(o.id)
  ElMessage.success('已删除')
  compare.value = { table: [], analysis: '' }
  await loadOffers()
}

async function runCompare() {
  comparing.value = true
  try {
    const res = await compareOffers(selectedIds.value)
    compare.value = { table: res.table || [], analysis: res.analysis || '' }
    currentStep.value = 2
    maxStep.value = 2
    // 表格秒出；AI 分析未命中缓存时通过 SSE 流式补全（打字机显示）
    if (res.record_id && !res.analysis) {
      await streamCompareAnalysis(res.record_id, (chunk) => {
        compare.value = { ...compare.value, analysis: compare.value.analysis + chunk }
      })
    }
    ElMessage.success('对比分析完成')
  } catch (e) {
    if (e?.response?.status === 400) {
      ElMessage.warning('AI 分析暂不可用，已展示基础对比结果')
    }
  } finally {
    comparing.value = false
  }
}

onMounted(() => {
  loadOffers()
})
</script>

<style scoped>
/* ── 向导步骤条 ── */
.wizard {
  display: flex;
  align-items: center;
  justify-content: center;
  max-width: 880px;
  margin: 0 auto 20px;
  padding: 18px 28px;
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
.w-step:active {
  transform: scale(0.96);
}
.w-step:disabled {
  cursor: default;
  opacity: 0.55;
}
.w-dot {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
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
.w-step.active .w-label {
  color: #1a1a1a;
}
.w-step.done .w-label {
  color: var(--app-text);
}
.w-line {
  width: 56px;
  height: 3px;
  border-radius: 2px;
  background: var(--app-border);
  margin: 0 12px;
  transition: background 0.3s ease;
}
.w-line.done {
  background: linear-gradient(90deg, #10b981, #34d399);
}

/* ── 步骤卡片 ── */
.w-body {
  max-width: 880px;
  margin: 0 auto;
}
.w-card {
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: var(--app-radius-lg, 16px);
  box-shadow: var(--app-shadow-md, 0 4px 16px rgba(20, 20, 20, 0.08));
  padding: 26px 30px 30px;
}
.w-head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 22px;
}
.w-ico {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: linear-gradient(135deg, #1a1a1a, #1a1a1a);
  box-shadow: 0 6px 14px rgba(26, 26, 26, 0.25);
}
.w-ico.green {
  background: linear-gradient(135deg, #10b981, #059669);
  box-shadow: 0 6px 14px rgba(16, 185, 129, 0.25);
}
.w-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--app-text);
}
.w-desc {
  font-size: 13px;
  color: var(--app-text-secondary);
  margin-top: 3px;
}

/* ── 底部导航 ── */
.w-nav {
  max-width: 880px;
  margin: 18px auto 0;
  display: flex;
  align-items: center;
  gap: 12px;
}
.w-nav-spacer {
  flex: 1;
}
.nav-text {
  margin: 0 4px;
}
.nav-hint {
  font-size: 12px;
  color: var(--app-text-muted);
}

/* ── 切换动画 ── */
.wizard-enter-active {
  transition: all 0.32s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.wizard-leave-active {
  transition: all 0.18s ease;
}
.wizard-enter-from {
  opacity: 0;
  transform: translateY(18px) scale(0.99);
}
.wizard-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.99);
}

/* ── 原有表单/结果样式 ── */
.full {
  width: 100%;
}
.add-btn {
  width: 100%;
}
.offer-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.offer-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 14px;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  transition: transform 160ms var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1)),
    border-color 0.2s ease;
}
.offer-item:hover {
  border-color: var(--app-brand, #1a1a1a);
}
.offer-main {
  flex: 1;
  min-width: 0;
}
.offer-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}
.offer-sub {
  font-size: 12px;
  color: #606266;
}
.offer-ops {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

/* ── 多选 ── */
.select-all {
  margin-left: 10px;
  font-weight: 400;
}
.offer-check {
  flex-shrink: 0;
  margin-right: 4px;
}

/* ── 对比历史 ── */
.history-btn {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border: 1px solid #e4e7ed;
  border-radius: 9px;
  background: #fff;
  font-size: 13px;
  color: #606266;
  cursor: pointer;
  transition: all 0.2s ease;
}
.history-btn:hover {
  color: #1a1a1a;
  border-color: #1a1a1a;
}
.history-wrap {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.history-back {
  font-size: 13px;
  color: #409eff;
  cursor: pointer;
  padding: 2px 0;
}
.history-back:hover {
  text-decoration: underline;
}
.history-title {
  font-size: 15px;
  font-weight: 700;
  color: #303133;
}
.history-time {
  font-size: 12px;
  color: var(--app-text-muted);
}
.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 14px;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.2s ease;
}
.history-item:hover {
  border-color: var(--app-brand, #1a1a1a);
}
.history-main {
  flex: 1;
  min-width: 0;
}
.history-company {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 3px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ==================== 深色液态玻璃覆盖 ==================== */
.wizard,
.w-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-highlight), var(--app-shadow-sm);
}
.w-dot { background: rgba(255, 255, 255, 0.06); border: 2px solid var(--app-border); }
.w-step.active .w-dot {
  color: #071018;
  background: var(--app-brand-gradient);
  box-shadow: 0 0 0 5px rgba(90, 208, 230, 0.16), 0 6px 16px -4px rgba(107, 139, 255, 0.5);
}
.w-step.done .w-dot {
  color: #071018;
  background: linear-gradient(135deg, #43d9a3, #2fb589);
  box-shadow: 0 0 0 5px rgba(67, 217, 163, 0.16);
}
.w-step.active .w-label { color: var(--app-cyan); }
.w-line.done { background: linear-gradient(90deg, #43d9a3, #5ad0e6); }
.w-ico {
  color: #071018;
  background: var(--app-brand-gradient);
  box-shadow: 0 6px 14px -4px rgba(90, 208, 230, 0.5);
}
.w-ico.green { background: linear-gradient(135deg, #43d9a3, #2fb589); }
.offer-item {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--app-border);
}
.offer-item:hover { border-color: rgba(90, 208, 230, 0.4); }
.offer-title { color: var(--app-text); }
.offer-sub { color: var(--app-text-secondary); }
.history-btn {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--app-border);
  color: var(--app-text-secondary);
}
.history-btn:hover {
  color: var(--app-cyan);
  border-color: rgba(90, 208, 230, 0.4);
}
.history-title { color: var(--app-text); }
.history-company { color: var(--app-text); }
.history-time { color: var(--app-text-muted); }
.history-item {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--app-border);
}
.history-item:hover { border-color: rgba(90, 208, 230, 0.4); }
</style>