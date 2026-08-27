<template>
  <div class="diagnosis">
    <el-alert
      title="三步完成匹配诊断：① 保存简历（可保存多份，勾选用于诊断的一份）→ ② 粘贴或保存目标岗位 JD（可保存多份对比）→ ③ 查看匹配分、技能缺口与优化建议。简历解析与诊断由大模型完成，请确保已在「模型配置」页设置 API Key。"
      type="info"
      :closable="false"
      class="tip"
    />

    <el-row :gutter="16">
      <!-- 左侧：输入 -->
      <el-col :span="12">
        <el-card>
          <template #header>① 上传简历</template>
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
            :rows="10"
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
              <div
                class="history-item"
                :class="{ selected: selectedResumeId === null }"
              >
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
        </el-card>

        <el-card class="mt-16">
          <template #header>② 岗位 JD（可保存多份对比）</template>
          <el-input
            v-model="jdTitle"
            placeholder="JD 标题（可选），如：后端开发工程师"
            class="mb-8"
          />
          <el-input
            v-model="jdText"
            type="textarea"
            :rows="6"
            placeholder="粘贴目标岗位 JD 内容（至少 20 字），例如：招聘后端开发工程师，要求熟练掌握 Python、MySQL、FastAPI……"
          />
          <el-row :gutter="8" class="mt-8">
            <el-col :span="12">
              <el-button type="success" plain :loading="jdSaving" class="full" @click="saveJd">
                {{ editingJdId ? '保存修改' : '保存 JD' }}
              </el-button>
            </el-col>
            <el-col :span="12">
              <el-button
                type="primary"
                :loading="diagnosing"
                :disabled="!canDiagnose"
                class="full"
                @click="runDiagnose"
              >
                开始匹配诊断
              </el-button>
            </el-col>
          </el-row>

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
        </el-card>
      </el-col>

      <!-- 右侧：结果 -->
      <el-col :span="12">
        <el-card>
          <template #header>③ 诊断结果</template>

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
                :width="130"
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
              <el-table-column prop="skill" label="缺失技能" width="130" />
              <el-table-column prop="required_level" label="要求程度" width="90" />
              <el-table-column prop="current_level" label="当前状态" width="110" />
              <el-table-column prop="suggestion" label="弥补建议" />
            </el-table>

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

          <el-empty
            v-else
            description="选择简历与 JD 后，点击「开始匹配诊断」查看匹配结果"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import {
  createJd,
  deleteJd,
  deleteResume,
  diagnose,
  listJds,
  listResumes,
  updateJd,
  updateResume,
  updateResumeFile,
  uploadResumeFile,
  uploadResumeText,
} from '@/api/diagnostic'

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

const canDiagnose = computed(() => !!selectedJdId.value || jdText.value.trim().length >= 20)

function onFileChange(uploadFile) {
  file.value = uploadFile.raw
}

async function loadResumes() {
  try {
    resumes.value = await listResumes()
  } catch {
    /* 忽略 */
  }
}

async function loadJds() {
  try {
    jds.value = await listJds()
  } catch {
    /* 忽略 */
  }
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
  if (!dt) return ''
  const d = new Date(dt)
  if (Number.isNaN(d.getTime())) return String(dt)
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
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
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message || '删除失败')
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
    ElMessage.success('匹配诊断完成')
  } finally {
    diagnosing.value = false
  }
}

const usedResumeLabel = computed(() => {
  if (!selectedResumeId.value) return '最近一份简历'
  const r = resumes.value.find((x) => x.id === selectedResumeId.value)
  return r ? (r.name || `简历 #${r.id}`) : `简历 #${selectedResumeId.value}`
})

const usedJdLabel = computed(() => {
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
})
</script>

<style scoped>
.tip {
  margin-bottom: 16px;
}
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
.mt-16 {
  margin-top: 16px;
}
.mt-8 {
  margin-top: 10px;
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
  gap: 24px;
  padding: 8px 0 16px;
}
.score-num {
  font-size: 30px;
  font-weight: 700;
}
.score-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}
.score-hint {
  margin-top: 8px;
  color: #909399;
  font-size: 12px;
}
.suggestion {
  margin-bottom: 8px;
}
.used-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0 12px;
}
.used-label {
  font-size: 13px;
  color: #909399;
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
  border-radius: 8px;
  transition: all 0.2s;
}
.history-item.selected {
  border-color: #67c23a;
  background: #f0f9eb;
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
  margin-bottom: 6px;
}
.selected-tag {
  margin-left: 6px;
}
.history-meta {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}
.history-hint {
  font-size: 12px;
  color: #909399;
}
.history-preview {
  font-size: 12px;
  color: #606266;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 360px;
}
.history-skills {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}
.skill-tag {
  margin-right: 0;
}
.more {
  font-size: 12px;
  color: #909399;
}
</style>
