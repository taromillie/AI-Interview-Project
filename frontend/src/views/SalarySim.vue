<template>
  <div class="salary">
    <el-alert
      title="输入目标岗位、技能栈、工作年限与城市，AI 结合市场行情与你的简历给出合理薪资区间与可执行的谈薪策略。"
      type="info"
      :closable="false"
      class="tip"
    />

    <el-row :gutter="16">
      <el-col :span="10">
        <el-card>
          <template #header>① 输入评估条件</template>
          <el-form label-position="top">
            <el-form-item label="目标岗位" required>
              <el-input v-model="targetPosition" placeholder="如：后端开发工程师" />
            </el-form-item>
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
                <el-option
                  v-for="s in commonSkills"
                  :key="s"
                  :label="s"
                  :value="s"
                />
              </el-select>
            </el-form-item>
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="工作年限" required>
                  <el-input-number v-model="years" :min="0" :max="30" controls-position="right" class="full" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="城市" required>
                  <el-select
                    v-model="city"
                    filterable
                    allow-create
                    default-first-option
                    placeholder="选择或输入"
                    class="full"
                  >
                    <el-option v-for="c in commonCities" :key="c" :label="c" :value="c" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
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
            <el-button
              type="primary"
              :loading="evaluating"
              :disabled="!targetPosition.trim() || !city.trim()"
              class="action"
              @click="runEvaluate"
            >
              开始谈薪评估
            </el-button>
          </el-form>

          <template v-if="evals.length">
            <el-divider content-position="left">历史评估（{{ evals.length }}）</el-divider>
            <div class="history-list">
              <div
                v-for="e in evals"
                :key="e.id"
                class="history-item"
                :class="{ active: result && result.id === e.id }"
                @click="loadEval(e)"
              >
                <div class="history-main">
                  <div class="history-title">
                    {{ e.target_position }} · {{ e.city }} · {{ e.years }} 年
                  </div>
                  <div class="history-preview">
                    {{ e.result.salary_range[0] }} ~ {{ e.result.salary_range[2] }} 元/月
                  </div>
                </div>
                <span class="history-time">{{ formatTime(e.created_at) }}</span>
              </div>
            </div>
          </template>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card>
          <template #header>
            ② 评估结果
            <el-tag v-if="result && result.id" size="small" type="warning" class="head-tag">历史记录</el-tag>
            <el-tag v-else-if="result" size="small" type="success" class="head-tag">本次评估</el-tag>
            <el-tag v-if="combinedResume" size="small" type="success" class="head-tag">
              已结合简历
            </el-tag>
          </template>

          <template v-if="result">
            <div class="range-row">
              <div class="range-card">
                <div class="range-label">最低</div>
                <div class="range-value">{{ formatMoney(result.salary_range[0]) }}</div>
              </div>
              <div class="range-card main">
                <div class="range-label">合理区间中位</div>
                <div class="range-value">{{ formatMoney(result.salary_range[1]) }}</div>
              </div>
              <div class="range-card">
                <div class="range-label">最高</div>
                <div class="range-value">{{ formatMoney(result.salary_range[2]) }}</div>
              </div>
            </div>
            <div class="range-hint">均为人民币月薪（税前，元）</div>

            <div class="section-title">影响因素（{{ result.factors.length }}）</div>
            <ul v-if="result.factors.length" class="factor-list">
              <li v-for="(f, i) in result.factors" :key="i">{{ f }}</li>
            </ul>
            <el-empty v-else description="暂无因素分析" :image-size="50" />

            <div class="section-title">谈薪策略（{{ result.strategy.length }}）</div>
            <el-timeline v-if="result.strategy.length">
              <el-timeline-item v-for="(s, i) in result.strategy" :key="i" type="primary">
                <span class="strategy-item">{{ s }}</span>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无策略建议" :image-size="50" />
          </template>

          <el-empty
            v-else
            description="填写左侧评估条件后，点击「开始谈薪评估」"
            :image-size="80"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listResumes } from '@/api/diagnostic'
import { listSalaryEvals, salaryEvaluate } from '@/api/salary'

const targetPosition = ref('')
const skillStack = ref([])
const years = ref(3)
const city = ref('')
const resumeId = ref(0) // 0=最近一份，-1=不结合，>0=指定简历
const evaluating = ref(false)
const result = ref(null)
const evals = ref([])
const resumes = ref([])

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

async function loadEvals() {
  try {
    evals.value = await listSalaryEvals()
  } catch {
    /* 忽略 */
  }
}

function loadEval(e) {
  targetPosition.value = e.target_position
  city.value = e.city
  years.value = e.years
  skillStack.value = e.skill_stack || []
  result.value = {
    id: e.id,
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
  } finally {
    evaluating.value = false
  }
}

async function loadResumes() {
  try {
    resumes.value = await listResumes()
  } catch {
    /* 忽略 */
  }
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
.tip {
  margin-bottom: 16px;
}
.full {
  width: 100%;
}
.action {
  width: 100%;
}
.history-list {
  max-height: 300px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.history-item:hover {
  border-color: #409eff;
}
.history-item.active {
  border-color: #409eff;
  background: #ecf5ff;
}
.history-main {
  flex: 1;
  min-width: 0;
}
.history-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}
.history-preview {
  font-size: 12px;
  color: #909399;
}
.history-time {
  font-size: 12px;
  color: #c0c4cc;
  flex-shrink: 0;
}
.head-tag {
  margin-left: 8px;
}
.range-row {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}
.range-card {
  flex: 1;
  padding: 16px 12px;
  text-align: center;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #f8f9fb;
}
.range-card.main {
  border-color: #409eff;
  background: #ecf5ff;
  transform: scale(1.04);
}
.range-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}
.range-value {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
}
.range-card.main .range-value {
  color: #409eff;
}
.range-hint {
  margin-top: 10px;
  font-size: 12px;
  color: #c0c4cc;
  text-align: center;
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 18px 0 10px;
}
.factor-list {
  margin: 0;
  padding-left: 20px;
}
.factor-list li {
  font-size: 13px;
  color: #606266;
  line-height: 1.9;
}
.strategy-item {
  font-size: 13px;
  color: #303133;
  line-height: 1.6;
}
</style>
