<template>
  <div class="diagnosis">
    <div class="page-banner">
      <div class="banner-left">
        <div class="banner-icon">
          <el-icon :size="24"><Document /></el-icon>
        </div>
        <div>
          <div class="banner-title">简历 × JD 诊断</div>
          <div class="banner-desc">保存简历、粘贴目标岗位 JD，一键查看匹配分、技能缺口与优化建议</div>
        </div>
      </div>
    </div>

    <!-- 向导步骤条 -->
    <WizardStepper :steps="wizardSteps" :current-step="currentStep" :max-step="maxStep" @step="goStep" />

    <!-- 步骤内容 -->
    <div class="w-body">
      <transition name="wizard" mode="out-in">
        <!-- ① 简历 -->
        <section v-if="currentStep === 1" key="s1" class="w-card">
          <div class="w-head">
            <span class="w-ico"><el-icon :size="20"><Document /></el-icon></span>
            <div>
              <div class="w-title">上传你的简历</div>
              <div class="w-desc">粘贴文本或上传文件，AI 会自动解析技能清单</div>
            </div>
          </div>

          <el-radio-group v-model="inputMode" class="mode-group">
            <el-radio-button value="paste">粘贴文本</el-radio-button>
            <el-radio-button value="file">上传文件</el-radio-button>
          </el-radio-group>

          <el-input
            v-model="resumeName"
            placeholder="简历名称（可选），留空自动按「姓名 · 目标岗位」命名"
            maxlength="60"
            clearable
            class="mb-8"
          />

          <el-input
            v-if="inputMode === 'paste'"
            v-model="resumeText"
            type="textarea"
            :rows="8"
            placeholder="粘贴你的简历内容（教育背景、工作经历、项目、技能……）"
          />
          <el-upload
            v-else
            drag
            :auto-upload="false"
            :limit="1"
            accept=".pdf,.txt,.md"
            :on-change="onFileChange"
            :on-remove="() => (file = null)"
            class="uploader"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽简历到此处，或 <em>点击选择</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 PDF / TXT，大小不超过 2MB</div>
            </template>
          </el-upload>

          <el-button type="primary" :loading="uploading" class="action" @click="saveResume">
            {{ uploading ? '正在解析并保存简历…' : (editingId ? '保存修改' : '保存简历') }}
          </el-button>

          <template v-if="resumes.length">
            <el-divider content-position="left">历史简历（{{ resumes.length }}）</el-divider>
            <div class="history-list">
              <div class="history-item" :class="{ selected: selectedResumeId === null }">
                <div class="history-main">
                  <div class="history-title">
                    最近一份简历
                    <el-tag v-if="selectedResumeId === null" type="success" size="small" class="selected-tag">
                      诊断中
                    </el-tag>
                  </div>
                  <div class="history-hint">未手动选择时默认使用最近保存的简历</div>
                </div>
                <el-button size="small" type="primary" plain @click="selectedResumeId = null">
                  使用
                </el-button>
              </div>
              <div
                v-for="r in resumes"
                :key="r.id"
                class="history-item"
                :class="{ selected: selectedResumeId === r.id, active: editingId === r.id }"
              >
                <div class="history-main">
                  <div class="history-title">
                    {{ r.name || '未命名简历' }}
                    <el-tag v-if="selectedResumeId === r.id" type="success" size="small" class="selected-tag">
                      诊断中
                    </el-tag>
                    <el-tag v-if="editingId === r.id" type="warning" size="small" class="selected-tag">
                      编辑中
                    </el-tag>
                  </div>
                  <div class="history-meta">
                    保存于 {{ formatTime(r.created_at) }} · {{ r.skills.length }} 项技能
                  </div>
                  <div class="history-skills">
                    <el-tag v-for="s in r.skills.slice(0, 4)" :key="s" size="small" class="skill-tag">
                      {{ s }}
                    </el-tag>
                    <span v-if="r.skills.length > 4" class="more">+{{ r.skills.length - 4 }}</span>
                  </div>
                </div>
                <el-button size="small" type="primary" plain @click="selectedResumeId = r.id">
                  用于诊断
                </el-button>
                <el-button size="small" @click="loadResume(r)">编辑</el-button>
                <el-button size="small" type="danger" plain @click="confirmDeleteResume(r)">删除</el-button>
              </div>
            </div>
          </template>
          <el-empty v-else description="保存简历后，可在历史列表中选择用于诊断的一份" :image-size="60" />

          <template v-if="diagnostics.length">
            <el-divider content-position="left">历史诊断（{{ diagnostics.length }}）</el-divider>
            <div class="history-list">
              <div
                v-for="d in diagnostics"
                :key="d.id"
                class="history-item"
                tabindex="0"
                role="button"
                @click="openHistoryDiagnostic(d)"
                @keydown.enter="openHistoryDiagnostic(d)"
                @keydown.space.prevent="openHistoryDiagnostic(d)"
              >
                <div class="history-main">
                  <div class="history-title">
                    {{ d.resume_name || '未命名简历' }}
                    <el-tag :type="scoreTag(d.match_score)" size="small">
                      {{ Math.round(d.match_score) }} 分
                    </el-tag>
                  </div>
                  <div class="history-meta">{{ formatTime(d.created_at) }}</div>
                  <div class="history-preview">JD：{{ d.jd_excerpt || '（无摘要）' }}</div>
                </div>
                <el-button size="small" type="primary" plain @click.stop="openHistoryDiagnostic(d)">
                  查看报告
                </el-button>
              </div>
            </div>
          </template>
        </section>

        <!-- ② JD -->
        <section v-else-if="currentStep === 2" key="s2" class="w-card">
          <div class="w-head">
            <span class="w-ico grad"><el-icon :size="20"><Search /></el-icon></span>
            <div>
              <div class="w-title">粘贴目标岗位 JD</div>
              <div class="w-desc">粘贴 JD 内容或从历史中选择，系统将按它评估你的简历</div>
            </div>
          </div>

          <el-input
            v-model="jdTitle"
            placeholder="JD 标题（可选），如：后端开发工程师"
            class="mb-8"
          />
          <el-input
            v-model="jdText"
            type="textarea"
            :rows="8"
            placeholder="粘贴目标岗位 JD 内容（至少 20 字），例如：招聘后端开发工程师，要求熟练掌握 Python、MySQL、FastAPI……"
          />
          <el-button type="primary" :loading="jdSaving" class="action" @click="saveJd">
            {{ editingJdId ? '保存修改' : '保存 JD' }}
          </el-button>

          <template v-if="jds.length">
            <el-divider content-position="left">JD 历史（{{ jds.length }}）</el-divider>
            <div class="history-list">
              <div
                v-for="j in jds"
                :key="j.id"
                class="history-item"
                :class="{ selected: selectedJdId === j.id, active: editingJdId === j.id }"
              >
                <div class="history-main">
                  <div class="history-title">
                    {{ j.title || '未命名 JD' }} · {{ formatTime(j.created_at) }}
                    <el-tag v-if="selectedJdId === j.id" type="success" size="small" class="selected-tag">
                      诊断中
                    </el-tag>
                    <el-tag v-if="editingJdId === j.id" type="warning" size="small" class="selected-tag">
                      编辑中
                    </el-tag>
                  </div>
                  <div class="history-preview">{{ j.content }}</div>
                </div>
                <el-button size="small" type="primary" plain @click="selectJd(j)">用于诊断</el-button>
                <el-button size="small" @click="loadJd(j)">编辑</el-button>
                <el-button size="small" type="danger" plain @click="removeJd(j)">删除</el-button>
              </div>
            </div>
          </template>
          <el-empty v-else description="保存 JD 后可在历史中快速复用" :image-size="60" />
        </section>

        <!-- ③ 结果 -->
        <section v-else key="s3" class="w-card">
          <div class="w-head">
            <span class="w-ico green"><el-icon :size="20"><DataAnalysis /></el-icon></span>
            <div>
              <div class="w-title">诊断结果</div>
              <div class="w-desc">匹配分、技能缺口与优化建议</div>
            </div>
          </div>

          <template v-if="result">
            <div class="used-row">
              <span class="used-label">诊断对象</span>
              <el-tag size="small">{{ usedResumeLabel }}</el-tag>
              <span class="used-arrow">×</span>
              <el-tag size="small" type="success">{{ usedJdLabel }}</el-tag>
            </div>

            <div class="score-row">
              <el-progress
                type="dashboard"
                :percentage="Math.round(result.match_score)"
                :color="scoreColor(result.match_score)"
                :width="140"
              >
                <template #default>
                  <span class="score-num">{{ Math.round(result.match_score) }}</span>
                </template>
              </el-progress>
              <div class="score-side">
                <div class="score-title">简历匹配度</div>
                <el-tag :type="scoreTag(result.match_score)" size="large">
                  {{ scoreText(result.match_score) }}
                </el-tag>
                <div class="score-hint">基于 JD 必需技能（85%）+ 加分技能（15%）计算</div>
              </div>
            </div>

            <el-divider content-position="left">技能缺口（{{ result.gaps.length }}）</el-divider>
            <el-table :data="result.gaps" size="small" empty-text="没有硬性技能缺口，很棒！">
              <el-table-column prop="skill" label="缺失技能" min-width="110" />
              <el-table-column prop="required_level" label="要求程度" min-width="80" />
              <el-table-column prop="current_level" label="当前状态" min-width="90" />
              <el-table-column prop="suggestion" label="弥补建议" min-width="160" />
            </el-table>
            <div class="gaps-actions">
              <el-button type="primary" :icon="VideoPlay" :disabled="!result.gaps.length" @click="practiceGaps">
                针对这些缺口练一场
              </el-button>
              <span class="gaps-actions-hint">将以上缺口作为练习主题，直接进入模拟面试</span>
            </div>

            <el-divider content-position="left">简历优化建议</el-divider>
            <el-alert
              v-for="(s, i) in result.resume_suggestions"
              :key="i"
              :title="s"
              type="success"
              :closable="false"
              class="suggestion"
            />
          </template>

          <el-empty v-else description="正在等待诊断结果…" :image-size="80" />
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
      <template v-if="currentStep === 1">
        <div class="nav-hint">保存简历后继续</div>
        <el-button type="primary" size="large" @click="goNext">
          下一步
          <el-icon class="el-icon--right"><ArrowRight /></el-icon>
        </el-button>
      </template>
      <template v-else-if="currentStep === 2">
        <div class="nav-hint" v-if="!canDiagnose">JD 内容至少 20 字</div>
        <el-button
          type="primary"
          size="large"
          :loading="diagnosing"
          :disabled="!canDiagnose"
          @click="goNext"
        >
          {{ diagnosing ? '正在诊断…' : '开始匹配诊断' }}
          <el-icon v-if="!diagnosing" class="el-icon--right"><MagicStick /></el-icon>
        </el-button>
      </template>
      <template v-else>
        <el-button size="large" @click="goHome">
          <el-icon><ArrowLeft /></el-icon>
          <span class="nav-text">返回</span>
        </el-button>
        <el-button size="large" @click="goPrev">
          <el-icon><RefreshLeft /></el-icon>
          <span class="nav-text">换个 JD 重新诊断</span>
        </el-button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { formatDateTime } from '@/utils/time'
import {
  ArrowLeft,
  ArrowRight,
  Check,
  DataAnalysis,
  Document,
  MagicStick,
  RefreshLeft,
  Search,
  UploadFilled,
  VideoPlay,
} from '@element-plus/icons-vue'
import {
  createJd,
  deleteJd,
  deleteResume,
  diagnose,
  listDiagnostics,
  listJds,
  listResumes,
  updateJd,
  updateResume,
  updateResumeFile,
  uploadResumeFile,
  uploadResumeText,
} from '@/api/diagnostic'
import WizardStepper from '@/components/wizard/WizardStepper.vue'

const inputMode = ref('paste')
const resumeName = ref('')
const resumeText = ref('')
const file = ref(null)
const jdTitle = ref('')
const jdText = ref('')
const uploading = ref(false)
const jdSaving = ref(false)
const diagnosing = ref(false)
const result = ref(null)
const resumes = ref([])
const editingId = ref(null)
const selectedResumeId = ref(null) // null = 最近一份
const jds = ref([])
const editingJdId = ref(null)
const selectedJdId = ref(null) // null = 使用当前输入
const diagnostics = ref([])
const historyLabels = ref(null) // 从历史诊断打开结果页时，展示历史对象标签

// ── 向导状态 ──
const wizardSteps = [
  { id: 1, title: '上传简历' },
  { id: 2, title: '粘贴 JD' },
  { id: 3, title: '查看结果' },
]
const currentStep = ref(1) // 当前展示哪一步
const maxStep = ref(1) // 到达过的最深步骤（决定步骤条"已完成"态）

const canDiagnose = computed(() => !!selectedJdId.value || jdText.value.trim().length >= 20)

const router = useRouter()

// 诊断 → 模拟面试：把技能缺口拼成练习主题，从基础难度练起
function practiceGaps() {
  const skills = (result.value?.gaps || []).map((g) => g.skill).filter(Boolean)
  router.push({
    name: 'interview',
    query: {
      target: skills.length ? skills.slice(0, 3).join('、').slice(0, 80) : undefined,
      difficulty: 'easy',
    },
  })
}

// 结果页"返回"= 回到第一页（历史列表所在页）
function goHome() {
  currentStep.value = 1
  historyLabels.value = null
}

function goPrev() {
  if (currentStep.value === 3 && result.value) {
    // 结果页"上一步"= 回 JD 步骤重新调整
    currentStep.value = 2
    return
  }
  if (currentStep.value > 1) currentStep.value--
}

function goNext() {
  if (currentStep.value === 1) {
    if (!resumes.value.length) {
      ElMessage.warning('请先保存一份简历，再进行下一步')
      return
    }
    currentStep.value = 2
    maxStep.value = Math.max(maxStep.value, 2)
  } else if (currentStep.value === 2) {
    runDiagnose()
  }
}

function goStep(n) {
  if (n === currentStep.value) return
  // 只允许跳转：已完成步骤，或紧邻的下一步
  if (n <= maxStep.value || n === currentStep.value + 1) {
    if (n === currentStep.value + 1) goNext()
    else currentStep.value = n
  }
}

function onFileChange(uploadFile) {
  file.value = uploadFile.raw
}

async function loadResumes() {
  try {
    resumes.value = await listResumes()
  } catch {
    /* 拦截器已统一提示 */
  }
}

async function loadJds() {
  try {
    jds.value = await listJds()
  } catch {
    /* 拦截器已统一提示 */
  }
}

async function loadDiagnostics() {
  try {
    diagnostics.value = await listDiagnostics()
  } catch {
    /* 拦截器已统一提示 */
  }
}

function openHistoryDiagnostic(d) {
  historyLabels.value = {
    resume: d.resume_name || `简历 #${d.resume_id}`,
    jd: d.jd_excerpt
      ? (d.jd_excerpt.length > 18 ? `${d.jd_excerpt.slice(0, 18)}…` : d.jd_excerpt)
      : '历史 JD',
  }
  result.value = {
    diagnostic_id: d.id,
    match_score: d.match_score,
    gaps: d.gaps || [],
    resume_suggestions: d.suggestions || [],
  }
  currentStep.value = 3
  maxStep.value = 3
}

function loadResume(r) {
  editingId.value = r.id
  inputMode.value = 'paste'
  resumeText.value = r.raw_text || ''
  resumeName.value = r.name || ''
  ElMessage.info(`已加载「${r.name || '该份'}简历」（${r.skills.length} 项技能），修改后点击「保存修改」`)
}

function loadJd(j) {
  editingJdId.value = j.id
  jdTitle.value = j.title || ''
  jdText.value = j.content
}

function selectJd(j) {
  selectedJdId.value = j.id
  jdText.value = j.content
}

async function saveJd() {
  if (jdText.value.trim().length < 20) {
    ElMessage.warning('JD 内容至少 20 字')
    return
  }
  jdSaving.value = true
  try {
    if (editingJdId.value) {
      await updateJd(editingJdId.value, {
        title: jdTitle.value.trim(),
        content: jdText.value,
      })
      ElMessage.success('JD 已更新')
      editingJdId.value = null
    } else {
      const jd = await createJd({
        title: jdTitle.value.trim(),
        content: jdText.value,
      })
      selectedJdId.value = jd.id
      ElMessage.success('JD 已保存并设为诊断对象')
    }
    await loadJds()
  } finally {
    jdSaving.value = false
  }
}

async function removeJd(j) {
  try {
    await ElMessageBox.confirm(`确定删除「${j.title || '未命名 JD'}」吗？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  await deleteJd(j.id)
  if (selectedJdId.value === j.id) selectedJdId.value = null
  if (editingJdId.value === j.id) {
    editingJdId.value = null
    jdTitle.value = ''
    jdText.value = ''
  }
  await loadJds()
  ElMessage.success('JD 已删除')
}

// 手动修改 JD 文本时，自动取消对历史 JD 的选中
watch(jdText, (v) => {
  if (!selectedJdId.value) return
  const j = jds.value.find((x) => x.id === selectedJdId.value)
  if (j && v !== j.content) selectedJdId.value = null
})

function formatTime(dt) {
  return formatDateTime(dt)
}

async function saveResume() {
  if (inputMode.value === 'paste') {
    if (!resumeText.value.trim()) {
      ElMessage.warning('请先粘贴简历内容')
      return
    }
  } else if (!file.value) {
    ElMessage.warning('请先选择简历文件')
    return
  }

  uploading.value = true
  try {
    const customName = resumeName.value.trim()
    let r
    if (editingId.value) {
      r =
        inputMode.value === 'paste'
          ? await updateResume(editingId.value, resumeText.value, customName)
          : await updateResumeFile(editingId.value, file.value, customName)
      ElMessage.success(`简历「${r.name}」已更新，识别到 ${r.skills.length} 项技能`)
      editingId.value = null
    } else {
      r =
        inputMode.value === 'paste'
          ? await uploadResumeText(resumeText.value, customName)
          : await uploadResumeFile(file.value, customName)
      ElMessage.success(`简历「${r.name}」已保存，识别到 ${r.skills.length} 项技能`)
    }
    resumeName.value = ''
    await loadResumes()
  } finally {
    uploading.value = false
  }
}

async function confirmDeleteResume(r) {
  try {
    await ElMessageBox.confirm(
      `确定删除简历「${r.name || '未命名简历'}」吗？该简历的诊断记录也会一并删除，操作不可恢复。`,
      '删除简历',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  try {
    await deleteResume(r.id)
    ElMessage.success('简历已删除')
    if (selectedResumeId.value === r.id) selectedResumeId.value = null
    if (editingId.value === r.id) {
      editingId.value = null
      inputMode.value = 'paste'
      resumeText.value = ''
      resumeName.value = ''
      file.value = null
    }
    await loadResumes()
  } catch {
    /* 拦截器已统一提示 */
  }
}

async function runDiagnose() {
  if (!selectedJdId.value && jdText.value.trim().length < 20) {
    ElMessage.warning('请填写 JD 内容（至少 20 字），或从历史 JD 中选择一份')
    return
  }
  diagnosing.value = true
  try {
    result.value = await diagnose({
      jd_text: jdText.value.trim(),
      resume_id: selectedResumeId.value,
      jd_id: selectedJdId.value,
    })
    historyLabels.value = null
    currentStep.value = 3
    maxStep.value = 3
    ElMessage.success('匹配诊断完成')
    loadDiagnostics()
  } finally {
    diagnosing.value = false
  }
}

const usedResumeLabel = computed(() => {
  if (historyLabels.value) return historyLabels.value.resume
  if (!selectedResumeId.value) return '最近一份简历'
  const r = resumes.value.find((x) => x.id === selectedResumeId.value)
  return r ? (r.name || `简历 #${r.id}`) : `简历 #${selectedResumeId.value}`
})

const usedJdLabel = computed(() => {
  if (historyLabels.value) return historyLabels.value.jd
  if (selectedJdId.value) {
    const j = jds.value.find((x) => x.id === selectedJdId.value)
    return j ? j.title || '历史 JD' : `JD #${selectedJdId.value}`
  }
  return '当前输入'
})

function scoreColor(s) {
  if (s >= 80) return '#67c23a'
  if (s >= 60) return '#e6a23c'
  return '#f56c6c'
}
function scoreTag(s) {
  return s >= 80 ? 'success' : s >= 60 ? 'warning' : 'danger'
}
function scoreText(s) {
  return s >= 80 ? '高度匹配' : s >= 60 ? '基本匹配' : '差距较大'
}

onMounted(() => {
  loadResumes()
  loadJds()
  loadDiagnostics()
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
.w-ico.grad {
  background: linear-gradient(135deg, #444444, #333333);
  box-shadow: 0 6px 14px rgba(139, 92, 246, 0.28);
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
.mode-group {
  margin-bottom: 14px;
}
.uploader {
  width: 100%;
}
.action {
  margin-top: 14px;
  width: 100%;
}
.mb-8 {
  margin-bottom: 10px;
}
.full {
  width: 100%;
}
.score-row {
  display: flex;
  align-items: center;
  gap: 28px;
  padding: 8px 0 16px;
}
.score-num {
  font-size: 32px;
  font-weight: 700;
}
.score-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}
.score-hint {
  margin-top: 8px;
  color: var(--app-text-muted);
  font-size: 12px;
}
.suggestion {
  margin-bottom: 8px;
}
.gaps-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 14px;
}
.gaps-actions-hint {
  color: var(--app-text-muted);
  font-size: 12px;
}
.used-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0 12px;
}
.used-label {
  font-size: 13px;
  color: var(--app-text-muted);
}
.used-arrow {
  color: #c0c4cc;
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
  border-radius: 10px;
  cursor: pointer;
  transition: transform 160ms var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1)),
    border-color 0.2s ease, background-color 0.2s ease;
}
.history-item:hover {
  border-color: var(--app-brand, #1a1a1a);
  background: rgba(26, 26, 26, 0.04);
}
.history-item.selected {
  border-color: var(--app-brand, #1a1a1a);
  background: rgba(26, 26, 26, 0.06);
}
.history-main {
  flex: 1;
  min-width: 0;
}
.history-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}
.history-meta {
  font-size: 12px;
  color: var(--app-text-muted);
  margin-top: 4px;
}
.history-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}
.history-hint {
  font-size: 12px;
  color: var(--app-text-muted);
  margin-top: 4px;
}
.history-preview {
  font-size: 12px;
  color: var(--app-text-muted);
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 420px;
}
.more {
  font-size: 12px;
  color: var(--app-text-muted);
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
.w-ico.grad { background: linear-gradient(135deg, #6b8bff, #8b6bff); }
.w-ico.green { background: linear-gradient(135deg, #43d9a3, #2fb589); }
.score-num { color: var(--app-cyan); }
.history-item {
  border: 1px solid var(--app-border);
  background: rgba(255, 255, 255, 0.03);
}
.history-item:hover {
  border-color: rgba(90, 208, 230, 0.4);
  background: rgba(255, 255, 255, 0.07);
}
.history-item.selected {
  border-color: var(--app-cyan);
  background: var(--app-brand-soft);
}
.history-title { color: var(--app-text); }
</style>