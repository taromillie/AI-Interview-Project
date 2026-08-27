<template>
  <div class="career">
    <el-alert
      title="输入当前岗位与目标岗位，AI 将对比两者任职要求，输出可迁移技能、技能缺口与学习路径。可关联一份历史简历让诊断更精准。"
      type="info"
      :closable="false"
      class="tip"
    />

    <el-row :gutter="16">
      <el-col :span="10">
        <el-card>
          <template #header>① 输入诊断条件</template>
          <el-form label-position="top">
            <el-form-item label="当前岗位" required>
              <el-input v-model="fromPosition" placeholder="如：测试工程师" />
            </el-form-item>
            <el-form-item label="目标岗位" required>
              <el-input v-model="toPosition" placeholder="如：后端开发工程师" />
            </el-form-item>
            <el-form-item label="关联简历（可选）">
              <el-select v-model="resumeId" placeholder="不选则仅基于岗位判断" clearable class="full">
                <el-option
                  v-for="r in resumes"
                  :key="r.id"
                  :label="`${formatTime(r.created_at)}（${r.skills.length} 项技能）`"
                  :value="r.id"
                />
              </el-select>
            </el-form-item>
            <el-button
              type="primary"
              :loading="diagnosing"
              :disabled="!fromPosition.trim() || !toPosition.trim()"
              class="action"
              @click="runDiagnosis"
            >
              开始转行诊断
            </el-button>
          </el-form>

          <template v-if="plans.length">
            <el-divider content-position="left">历史诊断（{{ plans.length }}）</el-divider>
            <div class="history-list">
              <div
                v-for="p in plans"
                :key="p.id"
                class="history-item"
                :class="{ active: result && result.id === p.id }"
                @click="loadPlan(p)"
              >
                <div class="history-main">
                  <div class="history-title">{{ p.from_position }} → {{ p.to_position }}</div>
                  <div class="history-preview">{{ p.summary }}</div>
                </div>
                <span class="history-time">{{ formatTime(p.created_at) }}</span>
              </div>
            </div>
          </template>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card>
          <template #header>
            ② 诊断结果
            <el-tag v-if="result && result.id" size="small" type="warning" class="head-tag">历史记录</el-tag>
            <el-tag v-else-if="result" size="small" type="success" class="head-tag">本次诊断</el-tag>
          </template>

          <template v-if="result">
            <el-alert :title="result.summary" type="success" :closable="false" class="summary" />

            <div class="section-title">可迁移技能（{{ result.transferable.length }}）</div>
            <div v-if="result.transferable.length" class="transfer-grid">
              <div v-for="(t, i) in result.transferable" :key="i" class="transfer-card">
                <div class="transfer-skill">{{ t.skill }}</div>
                <div class="transfer-evidence">{{ t.evidence }}</div>
              </div>
            </div>
            <el-empty v-else description="暂无可迁移技能分析" :image-size="50" />

            <div class="section-title">技能缺口（{{ result.gaps.length }}）</div>
            <el-table :data="result.gaps" size="small" empty-text="未识别到明显技能缺口">
              <el-table-column prop="skill" label="缺失技能" min-width="120" />
              <el-table-column label="要求程度" width="90">
                <template #default="{ row }">
                  <el-tag :type="levelTag(row.level)" size="small">{{ row.level }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="suggestion" label="补足建议" />
            </el-table>

            <div class="section-title">学习路径（{{ result.roadmap.length }}）</div>
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
            <el-empty v-else description="暂无学习路径" :image-size="50" />
          </template>

          <el-empty
            v-else
            description="填写左侧诊断条件后，点击「开始转行诊断」"
            :image-size="80"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { careerDiagnosis, listCareerPlans } from '@/api/career'
import { listResumes } from '@/api/diagnostic'

const fromPosition = ref('')
const toPosition = ref('')
const resumeId = ref(null)
const diagnosing = ref(false)
const result = ref(null)
const resumes = ref([])
const plans = ref([])

async function loadResumes() {
  try {
    resumes.value = await listResumes()
  } catch {
    /* 忽略 */
  }
}

async function loadPlans() {
  try {
    plans.value = await listCareerPlans()
  } catch {
    /* 忽略 */
  }
}

function loadPlan(p) {
  result.value = p
  ElMessage.info(`已加载 ${p.from_position} → ${p.to_position} 的诊断记录`)
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
  } finally {
    diagnosing.value = false
  }
}

function formatTime(dt) {
  if (!dt) return ''
  const d = new Date(dt)
  if (Number.isNaN(d.getTime())) return String(dt)
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
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
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 260px;
}
.history-time {
  font-size: 12px;
  color: #c0c4cc;
  flex-shrink: 0;
}
.head-tag {
  margin-left: 8px;
}
.summary {
  margin-bottom: 8px;
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 16px 0 10px;
}
.transfer-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.transfer-card {
  padding: 10px 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #f8f9fb;
}
.transfer-skill {
  font-size: 13px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 4px;
}
.transfer-evidence {
  font-size: 12px;
  color: #606266;
}
.roadmap-stage {
  font-weight: 600;
  color: #303133;
}
.roadmap-action {
  font-size: 13px;
  color: #606266;
  margin-top: 2px;
}
</style>
