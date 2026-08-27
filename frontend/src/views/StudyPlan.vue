<template>
  <div class="study-plan">
    <el-alert
      title="AI 结合你的能力画像缺口与目标岗位，自动生成「冲刺备战计划」。逐日勾选任务，跟踪备战进度，坚持到面试那天。"
      type="info"
      :closable="false"
      class="tip"
    />

    <el-row :gutter="16">
      <el-col :span="10">
        <el-card>
          <template #header>① 生成备战计划</template>
          <el-form label-position="top">
            <el-form-item label="目标岗位">
              <el-input v-model="targetPosition" placeholder="如：Java 后端开发工程师" />
            </el-form-item>
            <el-form-item label="备战天数" required>
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
            <el-button
              type="primary"
              :loading="generating"
              class="action"
              @click="runGenerate"
            >
              AI 生成备战计划
            </el-button>
          </el-form>

          <template v-if="plans.length">
            <el-divider content-position="left">历史计划（{{ plans.length }}）</el-divider>
            <div class="history-list">
              <div
                v-for="p in plans"
                :key="p.id"
                class="history-item"
                :class="{ active: current && current.id === p.id }"
                @click="selectPlan(p)"
              >
                <div class="history-main">
                  <div class="history-title">
                    {{ p.title }}
                    <el-tag
                      v-if="p.status === 'completed'"
                      size="small"
                      type="success"
                      class="done-tag"
                    >
                      已完成
                    </el-tag>
                  </div>
                  <el-progress
                    :percentage="progressOf(p)"
                    :stroke-width="6"
                    class="mini-progress"
                  />
                </div>
              </div>
            </div>
          </template>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card v-if="current">
          <template #header>
            ② {{ current.title }}
            <el-tag v-if="current.status === 'completed'" size="small" type="success" class="head-tag">
              已完成
            </el-tag>
            <span class="plan-summary">{{ current.summary }}</span>
          </template>

          <div class="progress-row">
            <el-progress
              type="dashboard"
              :percentage="currentProgress"
              :width="120"
              color="#409eff"
            />
            <div class="progress-info">
              <div class="pi-line">总天数：{{ current.days }} 天</div>
              <div class="pi-line">已完成：{{ doneCount }} / {{ current.days }}</div>
              <div class="pi-line">阶段：{{ current.status === 'completed' ? '全部完成' : '备战中' }}</div>
              <el-button size="small" type="danger" plain @click="removePlan">
                删除计划
              </el-button>
            </div>
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
        </el-card>

        <el-card v-else>
          <el-empty
            description="生成一个备战计划，或从左侧选择历史计划查看"
            :image-size="80"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listResumes } from '@/api/diagnostic'
import {
  deleteStudyPlan,
  generateStudyPlan,
  listStudyPlans,
  toggleStudyPlanTask,
} from '@/api/studyPlan'

const targetPosition = ref('')
const days = ref(14)
const resumeId = ref(0)
const generating = ref(false)
const plans = ref([])
const current = ref(null)
const resumes = ref([])

const sortedTasks = computed(() => {
  const tasks = (current.value?.tasks || []).slice()
  return tasks.sort((a, b) => a.day - b.day)
})

const doneCount = computed(
  () => (current.value?.tasks || []).filter((t) => t.done).length
)
const currentProgress = computed(() => {
  if (!current.value || !current.value.days) return 0
  return Math.round((doneCount.value / current.value.days) * 100)
})

function progressOf(p) {
  const tasks = p.tasks || []
  if (!tasks.length) return 0
  return Math.round((tasks.filter((t) => t.done).length / tasks.length) * 100)
}

async function loadPlans() {
  try {
    plans.value = await listStudyPlans()
  } catch {
    /* 忽略 */
  }
}

async function loadResumes() {
  try {
    resumes.value = await listResumes()
  } catch {
    /* 忽略 */
  }
}

async function runGenerate() {
  generating.value = true
  try {
    const plan = await generateStudyPlan({
      target_position: targetPosition.value.trim(),
      days: days.value,
      resume_id: resumeId.value === 0 ? undefined : resumeId.value,
    })
    current.value = plan
    ElMessage.success('备战计划已生成')
    await loadPlans()
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

onMounted(() => {
  loadPlans()
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
.history-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
}
.done-tag {
  margin-left: 6px;
}
.mini-progress {
  width: 100%;
}
.head-tag {
  margin-left: 8px;
}
.plan-summary {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
  font-weight: 400;
}
.progress-row {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 6px 0 18px;
}
.progress-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.pi-line {
  font-size: 13px;
  color: #606266;
}
.task-timeline {
  margin-top: 8px;
}
.task-item {
  padding: 4px 0;
}
.task-item.done .task-title {
  text-decoration: line-through;
  color: #c0c4cc;
}
.task-head {
  display: flex;
  align-items: center;
  gap: 10px;
}
.task-day {
  font-size: 12px;
  font-weight: 700;
  color: #409eff;
  background: #ecf5ff;
  border-radius: 6px;
  padding: 2px 8px;
}
.task-title {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
.task-desc {
  margin-top: 6px;
  font-size: 13px;
  color: #606266;
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
