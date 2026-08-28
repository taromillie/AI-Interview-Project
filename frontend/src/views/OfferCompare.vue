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
            <el-divider content-position="left">已添加（{{ offers.length }} 个）</el-divider>
            <div class="offer-list">
              <div v-for="o in offers" :key="o.id" class="offer-item">
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

          <template v-if="compare.table.length">
            <el-table :data="compare.table" border size="small" class="cmp-table">
              <el-table-column prop="field" label="维度" width="130" />
              <el-table-column
                v-for="(_, i) in compare.table[0]?.values || []"
                :key="i"
                :label="offers[i]?.company || `Offer ${i + 1}`"
              >
                <template #default="{ row }">
                  <span
                    :class="{
                      best: isBest(row.field, i),
                      total: row.field.includes('年化总包'),
                    }"
                  >
                    {{ row.values[i] }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
            <div class="best-hint">绿色高亮 = 该维度最优</div>

            <div class="section-title">AI 综合建议</div>
            <div class="analysis-box">{{ compare.analysis }}</div>
          </template>

          <el-empty
            v-else
            description="录入至少 2 个 Offer 后点击「开始对比」"
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
        <div class="nav-hint">{{ offers.length < 2 ? `还需 ${2 - offers.length} 个 Offer` : `已添加 ${offers.length} 个，可以对比了` }}</div>
        <el-button
          type="primary"
          size="large"
          :loading="comparing"
          :disabled="offers.length < 2"
          @click="goNext"
        >
          {{ comparing ? '正在对比…' : '开始对比' }}
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
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Check,
  DataAnalysis,
  MagicStick,
  Plus,
  RefreshRight,
  Trophy,
} from '@element-plus/icons-vue'
import {
  compareOffers,
  createOffer,
  deleteOffer,
  listOffers,
} from '@/api/offer'

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
const compare = ref({ table: [], analysis: '' })
const comparing = ref(false)

// ── 向导状态 ──
const wizardSteps = [
  { id: 1, title: '录入 Offer' },
  { id: 2, title: '查看对比' },
]
const currentStep = ref(1)
const maxStep = ref(1)

function goNext() {
  if (offers.value.length < 2) {
    ElMessage.warning('至少需要 2 个 Offer 才能对比')
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

function isBest(field, i) {
  const t = compare.value.table
  const row = t.find((r) => r.field === field)
  if (!row) return false
  const values = row.values.map((v) => Number(String(v).replace(/[^\d.]/g, '')) || 0)
  if (field.includes('生活平衡')) {
    return values[i] === Math.max(...values) && values[i] > 0
  }
  if (values[i] === Math.max(...values) && values[i] > 0) {
    return true
  }
  return false
}

async function loadOffers() {
  try {
    offers.value = await listOffers()
  } catch {
    /* 忽略 */
  }
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
    await ElMessageBox.confirm(`确定删除 ${o.company} 的 Offer？`, '提示', { type: 'warning' })
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
    compare.value = await compareOffers()
    currentStep.value = 2
    maxStep.value = 2
    ElMessage.success('对比分析完成')
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
.cmp-table {
  width: 100%;
}
.best {
  color: #67c23a;
  font-weight: 700;
}
.total {
  font-weight: 700;
  color: #303133;
}
.best-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #c0c4cc;
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 20px 0 10px;
}
.analysis-box {
  background: #f0f7ff;
  border: 1px solid #d6e9ff;
  border-radius: 8px;
  padding: 14px 16px;
  font-size: 13px;
  color: #303133;
  line-height: 1.8;
  white-space: pre-wrap;
}
</style>
