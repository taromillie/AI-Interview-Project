<template>
  <div class="offer-compare">
    <el-alert
      title="录入手上拿到的多个 Offer，系统自动计算年化总包并生成结构化对比表，AI 再结合城市生活成本与岗位成长性给出综合建议。"
      type="info"
      :closable="false"
      class="tip"
    />

    <el-row :gutter="16">
      <el-col :span="10">
        <el-card>
          <template #header>① Offer 录入（至少 2 个可对比）</template>
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
            <div class="form-actions">
              <el-button type="primary" :disabled="!form.company.trim()" @click="saveOffer">
                添加 Offer
              </el-button>
              <el-button
                type="success"
                :disabled="offers.length < 2"
                :loading="comparing"
                @click="runCompare"
              >
                AI 对比分析
              </el-button>
            </div>
          </el-form>
        </el-card>

        <el-card class="offer-list-card">
          <template #header>
            我的 Offer（{{ offers.length }}）
            <el-button
              v-if="compare.table.length"
              type="primary"
              text
              size="small"
              @click="runCompare"
            >
              重新对比
            </el-button>
          </template>
          <div v-if="offers.length" class="offer-list">
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
          <el-empty v-else description="还没有 Offer，先添加吧" :image-size="50" />
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card>
          <template #header>② 对比结果</template>

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
            description="录入至少 2 个 Offer 后点击「AI 对比分析」"
            :image-size="80"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
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
  await ElMessageBox.confirm(`确定删除 ${o.company} 的 Offer？`, '提示', { type: 'warning' })
  await deleteOffer(o.id)
  ElMessage.success('已删除')
  compare.value = { table: [], analysis: '' }
  await loadOffers()
}

async function runCompare() {
  comparing.value = true
  try {
    compare.value = await compareOffers()
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
.tip {
  margin-bottom: 16px;
}
.full {
  width: 100%;
}
.form-actions {
  display: flex;
  gap: 10px;
}
.offer-list-card {
  margin-top: 16px;
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
  padding: 10px 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
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
