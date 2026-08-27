<template>
  <div class="real-interview">
    <el-alert
      title="把真实面试的问答记录下来，AI 会逐题批改、给出维度评分与可执行的改进建议，让每一次真实面试都变成成长燃料。"
      type="info"
      :closable="false"
      class="tip"
    />

    <el-row :gutter="16">
      <el-col :span="10">
        <el-card>
          <template #header>① 录入真实面试</template>
          <el-form label-position="top">
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="公司" required>
                  <el-input v-model="form.company" placeholder="如：字节跳动" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="岗位">
                  <el-input v-model="form.position" placeholder="如：后端开发工程师" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="面试日期">
                  <el-date-picker
                    v-model="form.interview_date"
                    type="date"
                    value-format="YYYY-MM-DD"
                    placeholder="选择日期"
                    class="full"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="轮次">
                  <el-select v-model="form.round_type" class="full" placeholder="选择轮次">
                    <el-option v-for="r in roundTypes" :key="r" :label="r" :value="r" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="面试备注">
              <el-input
                v-model="form.notes"
                type="textarea"
                :rows="2"
                placeholder="如：一面是简历深挖，被追问了项目细节…"
              />
            </el-form-item>

            <div class="qa-block-title">问答记录（可增删）</div>
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

            <el-button
              type="primary"
              :disabled="!form.company.trim()"
              class="action"
              @click="saveInterview"
            >
              保存记录
            </el-button>
          </el-form>

          <template v-if="records.length">
            <el-divider content-position="left">面试记录（{{ records.length }}）</el-divider>
            <div class="history-list">
              <div
                v-for="r in records"
                :key="r.id"
                class="history-item"
                :class="{ active: current && current.id === r.id }"
                @click="selectRecord(r)"
              >
                <div class="history-main">
                  <div class="history-title">
                    {{ r.company }}
                    <el-tag v-if="r.position" size="small" effect="plain">{{ r.position }}</el-tag>
                    <el-tag v-if="r.review && r.review.overall_score" size="small" type="warning">
                      {{ r.review.overall_score }} 分
                    </el-tag>
                  </div>
                  <div class="history-preview">
                    {{ r.round_type || '未填轮次' }} · {{ r.interview_date || '未填日期' }}
                  </div>
                </div>
                <el-button
                  size="small"
                  text
                  type="danger"
                  @click.stop="removeRecord(r)"
                >
                  删除
                </el-button>
              </div>
            </div>
          </template>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card>
          <template #header>
            ② AI 复盘
            <el-button
              v-if="current"
              type="primary"
              size="small"
              :loading="reviewing"
              class="review-btn"
              @click="runReview"
            >
              生成/刷新 AI 复盘
            </el-button>
          </template>

          <template v-if="current && current.review && current.review.item_reviews">
            <div class="score-row">
              <el-progress
                type="dashboard"
                :percentage="Number(current.review.overall_score || 0)"
                :width="130"
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

            <div class="section-title">逐题批改（{{ current.review.item_reviews.length }}）</div>
            <div
              v-for="(ir, i) in current.review.item_reviews"
              :key="i"
              class="item-review"
            >
              <div class="ir-head">
                <span class="ir-q">Q{{ i + 1 }}：{{ ir.question }}</span>
                <el-tag size="small" :type="tagType(ir.score)">{{ ir.score }} 分</el-tag>
              </div>
              <div v-if="ir.comment" class="ir-comment">{{ ir.comment }}</div>
            </div>

            <div class="section-title">整体建议</div>
            <el-timeline v-if="current.review.suggestions?.length">
              <el-timeline-item
                v-for="(s, i) in current.review.suggestions"
                :key="i"
                type="primary"
              >
                <span class="suggestion-item">{{ s }}</span>
              </el-timeline-item>
            </el-timeline>
          </template>

          <el-empty
            v-else
            description="选择一条面试记录，点击「生成 AI 复盘」"
            :image-size="80"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createRealInterview,
  deleteRealInterview,
  getRealInterview,
  listRealInterviews,
  reviewRealInterview,
} from '@/api/realInterview'

const roundTypes = ['技术面', '业务面', 'HR 面', '交叉面', '终面']

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

function addItem() {
  form.value.items.push({ question: '', answer: '' })
}
function removeItem(idx) {
  form.value.items.splice(idx, 1)
}

async function loadRecords() {
  try {
    records.value = await listRealInterviews()
  } catch {
    /* 忽略 */
  }
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
  ElMessage.success('面试记录已保存')
  form.value.items = [{ question: '', answer: '' }]
  await loadRecords()
}

async function selectRecord(r) {
  try {
    current.value = await getRealInterview(r.id)
  } catch {
    /* 忽略 */
  }
}

async function runReview() {
  if (!current.value) return
  reviewing.value = true
  try {
    current.value = await reviewRealInterview(current.value.id)
    ElMessage.success('AI 复盘完成')
    await loadRecords()
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
.tip {
  margin-bottom: 16px;
}
.full {
  width: 100%;
}
.action {
  width: 100%;
  margin-top: 14px;
}
.qa-block-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin: 10px 0 8px;
}
.qa-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 10px;
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
  color: #409eff;
  background: #ecf5ff;
  border-radius: 6px;
  padding: 2px 8px;
}
.qa-question {
  margin-bottom: 8px;
}
.add-qa {
  width: 100%;
}
.history-list {
  max-height: 300px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
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
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}
.history-preview {
  font-size: 12px;
  color: #909399;
}
.review-btn {
  margin-left: 12px;
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
  background: #f0f7ff;
  border: 1px solid #d6e9ff;
  border-radius: 8px;
  padding: 12px 14px;
  font-size: 13px;
  color: #303133;
  line-height: 1.7;
  margin: 10px 0 6px;
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 18px 0 10px;
}
.item-review {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 10px;
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
  color: #303133;
}
.ir-comment {
  margin-top: 8px;
  font-size: 13px;
  color: #606266;
  line-height: 1.7;
}
.suggestion-item {
  font-size: 13px;
  color: #303133;
  line-height: 1.6;
}
</style>
