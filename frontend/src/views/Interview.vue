<template>
  <div class="interview-page">
    <!-- ================= 向导式设置区 ================= -->
    <template v-if="!session">
      <div class="page-head">
        <div class="page-title">模拟面试</div>
        <div class="page-desc">三步完成设置，选择你的目标岗位、面试官与难度</div>
      </div>

      <!-- 步骤条 -->
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
          <!-- ① 目标岗位 -->
          <section v-if="currentStep === 1" key="s1" class="w-card">
            <div class="w-head">
              <span class="w-ico"><el-icon :size="20"><Aim /></el-icon></span>
              <div>
                <div class="w-title">选择目标岗位</div>
                <div class="w-desc">面试问题将围绕该岗位的技能要求展开</div>
              </div>
            </div>

            <el-form label-position="top">
              <el-form-item label="岗位">
                <el-radio-group v-model="positionMode" class="mode-group">
                  <el-radio-button value="preset">岗位库</el-radio-button>
                  <el-radio-button value="custom">自定义</el-radio-button>
                </el-radio-group>
              </el-form-item>

              <el-form-item v-if="positionMode === 'preset'">
                <el-select
                  v-model="selectedPositionId"
                  filterable
                  placeholder="从岗位库选择（支持关键词搜索）"
                  class="full"
                >
                  <el-option v-for="p in positions" :key="p.id" :label="positionOptionLabel(p)" :value="p.id">
                    <span class="opt-company">{{ p.company || '未知公司' }}</span>
                    <span class="opt-position">{{ p.name }}</span>
                    <span class="opt-meta">{{ positionMeta(p) }}</span>
                  </el-option>
                </el-select>
              </el-form-item>

              <el-form-item v-else label="岗位名称">
                <el-input
                  v-model="customPosition"
                  placeholder="如：后端开发工程师、AI 产品经理…"
                  maxlength="60"
                  @keyup.enter="goNext"
                />
              </el-form-item>

              <el-form-item label="使用简历（可选）">
                <el-select v-model="selectedResumeId" clearable placeholder="不选则使用最近一份简历" class="full">
                  <el-option v-for="r in resumes" :key="r.id" :label="r.name || `简历 #${r.id}`" :value="r.id" />
                </el-select>
              </el-form-item>
            </el-form>
          </section>

          <!-- ② 面试官 -->
          <section v-else-if="currentStep === 2" key="s2" class="w-card">
            <div class="w-head">
              <span class="w-ico grad"><el-icon :size="20"><User /></el-icon></span>
              <div>
                <div class="w-title">选择面试官</div>
                <div class="w-desc">不同角色的人设与提问风格会注入本次面试</div>
              </div>
            </div>

            <div class="interviewer-grid">
              <button
                v-for="iv in interviewers"
                :key="iv.id"
                class="iv-card"
                :class="{ on: selectedInterviewerId === iv.id }"
                @click="selectedInterviewerId = iv.id"
              >
                <div class="iv-top">
                  <div class="iv-avatar">{{ iv.name.slice(0, 1) }}</div>
                  <div class="iv-info">
                    <div class="iv-name">{{ iv.name }}</div>
                    <div class="iv-title">{{ iv.title || '面试官' }}</div>
                  </div>
                  <el-icon v-if="selectedInterviewerId === iv.id" class="iv-check"><Check /></el-icon>
                </div>
                <div class="iv-persona">{{ iv.persona || '专业、严谨，关注你的真实能力。' }}</div>
                <div class="iv-tags">
                  <span class="iv-tag">{{ typeText(iv.interview_type) }}</span>
                  <span class="iv-tag">{{ biasText(iv.difficulty_bias) }}</span>
                </div>
              </button>
            </div>
            <div v-if="!interviewers.length" class="loading-text">正在加载面试官角色…</div>
          </section>

          <!-- ③ 难度 + 开始 -->
          <section v-else key="s3" class="w-card">
            <div class="w-head">
              <span class="w-ico green"><el-icon :size="20"><DataAnalysis /></el-icon></span>
              <div>
                <div class="w-title">选择面试难度</div>
                <div class="w-desc">难度决定问题深度与追问强度</div>
              </div>
            </div>

            <div class="difficulty-grid">
              <button
                v-for="d in difficulties"
                :key="d.value"
                class="diff-card"
                :class="{ on: selectedDifficulty === d.value }"
                @click="selectedDifficulty = d.value"
              >
                <div class="diff-name">{{ d.label }}</div>
                <div class="diff-desc">{{ d.desc }}</div>
              </button>
            </div>

            <el-form label-position="top" class="rounds-form">
              <el-form-item label="面试轮数">
                <el-slider v-model="maxRounds" :min="3" :max="12" :marks="{ 3: '3', 6: '6', 9: '9', 12: '12' }" />
              </el-form-item>
            </el-form>

            <div class="start-summary">
              <span class="sum-item">
                <span class="sum-label">岗位</span>
                <b>{{ positionLabel }}</b>
              </span>
              <span class="sum-item">
                <span class="sum-label">面试官</span>
                <b>{{ interviewerLabel }}</b>
              </span>
              <span class="sum-item">
                <span class="sum-label">难度</span>
                <b>{{ difficultyLabel }}</b>
              </span>
            </div>
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
        <template v-if="currentStep < 3">
          <div v-if="currentStep === 1" class="nav-hint">{{ positionLabel }}</div>
          <div v-else class="nav-hint">{{ interviewerLabel || '选择一个面试官' }}</div>
          <el-button
            type="primary"
            size="large"
            :disabled="!canNext"
            @click="goNext"
          >
            下一步
            <el-icon class="el-icon--right"><ArrowRight /></el-icon>
          </el-button>
        </template>
        <template v-else>
          <el-button type="primary" size="large" :loading="creating" @click="createSession">
            <el-icon v-if="!creating" class="el-icon--left"><MagicStick /></el-icon>
            {{ creating ? '正在准备面试…' : '开始面试' }}
          </el-button>
        </template>
      </div>
    </template>

    <!-- ================= 对话区 ================= -->
    <div v-else class="chat-shell">
      <div class="chat-head">
        <div class="chat-meta">
          <div class="chat-title">{{ sessionPositionLabel }}</div>
          <div class="chat-sub">
            <span>{{ interviewerLabel || 'AI 面试官' }}</span>
            <span class="chat-dot">·</span>
            <span>{{ difficultyLabel }}</span>
            <span class="chat-dot">·</span>
            <span>第 {{ chatMessages.filter((m) => m.role === 'ai').length }}/{{ maxRounds }} 轮</span>
          </div>
        </div>
        <div class="chat-tools">
          <button
            class="tool-btn"
            :class="{ on: voiceEnabled }"
            :title="voiceEnabled ? '关闭语音播报' : '开启语音播报'"
            @click="toggleVoice"
          >
            <el-icon :size="16"><Bell v-if="voiceEnabled" /><BellFilled v-else /></el-icon>
          </button>
          <el-button size="small" @click="endEarly">结束面试</el-button>
        </div>
      </div>

      <div ref="chatBody" class="chat-body">
        <template v-for="(m, i) in chatMessages" :key="i">
          <div v-if="m.role === 'ai'" class="msg ai">
            <div class="msg-avatar ai-avatar">{{ interviewerLabel.slice(0, 1) }}</div>
            <div class="msg-bubble ai-bubble">{{ m.content }}</div>
          </div>
          <div v-else class="msg user">
            <div class="msg-bubble user-bubble">{{ m.content }}</div>
          </div>
        </template>
        <div v-if="chatLoading" class="msg ai">
          <div class="msg-avatar ai-avatar">AI</div>
          <div class="msg-bubble ai-bubble thinking">
            <span class="tdot"></span><span class="tdot"></span><span class="tdot"></span>
          </div>
        </div>
      </div>

      <div class="chat-input">
        <button
          v-if="micSupported"
          class="mic-btn"
          :class="{ on: recording }"
          :disabled="!waitingAnswer"
          :title="recording ? '停止语音输入' : '语音输入回答'"
          @click="toggleRecording"
        >
          <el-icon :size="18"><Microphone /></el-icon>
        </button>
        <el-input
          v-model="answerDraft"
          type="textarea"
          :rows="2"
          :disabled="!waitingAnswer"
          :placeholder="recording ? '正在聆听你的回答…' : (waitingAnswer ? '输入你的回答，Enter 发送，Shift+Enter 换行' : '面试官正在提问…')"
          resize="none"
          @keydown.enter.exact.prevent="sendAnswer"
        />
        <button class="send-btn" :disabled="!waitingAnswer || !answerDraft.trim()" @click="sendAnswer">
          <el-icon :size="18"><Promotion /></el-icon>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  ArrowRight,
  Bell,
  BellFilled,
  Check,
  DataAnalysis,
  Aim,
  MagicStick,
  Microphone,
  Promotion,
  User,
} from '@element-plus/icons-vue'
import { listResumes } from '@/api/diagnostic'
import { listPositions } from '@/api/question'
import { listInterviewers } from '@/api/interviewer'
import { answerInterview, createInterview, finishInterview, startInterview } from '@/api/interview'

const route = useRoute()

// ── 向导状态 ──
const wizardSteps = [
  { id: 1, title: '目标岗位' },
  { id: 2, title: '面试官' },
  { id: 3, title: '难度' },
]
const currentStep = ref(1)
const maxStep = ref(1)

// ── 设置数据 ──
const positionMode = ref('preset')
const positions = ref([])
const selectedPositionId = ref(null)
const customPosition = ref('')
const resumes = ref([])
const selectedResumeId = ref(null)

const interviewers = ref([])
const selectedInterviewerId = ref(null)

const difficulties = [
  { value: 'easy', label: '简单', desc: '基础概念为主，答不上会引导提示，适合初次练习' },
  { value: 'normal', label: '标准', desc: '常规深度，正常追问，适合系统备战' },
  { value: 'hard', label: '困难', desc: '原理深挖 + 组合场景，少提示低容错，模拟大厂压测' },
]
const selectedDifficulty = ref('normal')
const maxRounds = ref(6)

const session = ref(null)
const creating = ref(false)
const chatMessages = ref([])
const chatLoading = ref(false)
const waitingAnswer = ref(false)
const answerDraft = ref('')
const interviewId = ref(null)
const chatBody = ref(null)

// ── 语音面试（Web Speech API）──
const voiceEnabled = ref(true)
const micSupported = typeof window !== 'undefined' && (
  'SpeechRecognition' in window || 'webkitSpeechRecognition' in window
)
const recording = ref(false)
let finalTranscript = ''
let recognition = null

// ── 派生 ──
const positionLabel = computed(() => {
  if (positionMode.value === 'preset') {
    const p = positions.value.find((x) => x.id === selectedPositionId.value)
    return p ? positionOptionLabel(p) : ''
  }
  return customPosition.value.trim() || ''
})

function positionOptionLabel(p) {
  return p.company ? `${p.company} ${p.name}` : p.name
}

const canNext = computed(() => {
  if (currentStep.value === 1) return !!positionLabel.value
  if (currentStep.value === 2) return selectedInterviewerId.value != null
  return true
})

const interviewerLabel = computed(() => {
  const iv = interviewers.value.find((x) => x.id === selectedInterviewerId.value)
  return iv ? iv.name : ''
})

const difficultyLabel = computed(() => {
  const d = difficulties.find((x) => x.value === selectedDifficulty.value)
  return d ? d.label : ''
})

const sessionPositionLabel = computed(() => {
  const p = positions.value.find((x) => x.id === selectedPositionId.value)
  return p ? positionOptionLabel(p) : (customPosition.value.trim() || '模拟面试')
})

function positionMeta(p) {
  const d = { junior: '初级', mid: '中级', senior: '高级' }[p.difficulty] || p.difficulty || ''
  const dir = { backend: '后端', frontend: '前端', algorithm: '算法', product: '产品', operations: '运营', data: '数据' }[p.direction] || ''
  return `${dir} ${d}`.trim()
}

function typeText(t) {
  return { all: '通用', normal: '常规面', switch: '转行面', salary: '谈薪面' }[t] || t
}
function biasText(b) {
  return b === 1 ? '偏难' : b === -1 ? '偏易' : '难度中性'
}

// ── 步骤导航 ──
function goNext() {
  if (currentStep.value === 1 && !positionLabel.value) {
    ElMessage.warning('请先选择或输入目标岗位')
    return
  }
  if (currentStep.value === 2 && selectedInterviewerId.value == null) {
    ElMessage.warning('请选择一个面试官')
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

// ── 创建面试 ──
async function createSession() {
  creating.value = true
  try {
    const payload = {
      mode: 'text',
      interview_type: 'normal',
      max_rounds: maxRounds.value,
      difficulty: selectedDifficulty.value,
      interviewer_id: selectedInterviewerId.value,
    }
    if (positionMode.value === 'preset') payload.position_id = selectedPositionId.value
    else payload.target_position = customPosition.value.trim()
    if (selectedResumeId.value) payload.resume_id = selectedResumeId.value

    const s = await createInterview(payload)
    session.value = s
    interviewId.value = s.id
    chatMessages.value = []
    await beginChat()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message || '创建面试失败')
  } finally {
    creating.value = false
  }
}

async function beginChat() {
  chatLoading.value = true
  waitingAnswer.value = true
  try {
    await startInterview(interviewId.value, {
      onEvent: (event, data) => {
        if (event === 'question') {
          chatMessages.value.push({ role: 'ai', content: data?.question })
          speakText(data?.question)
        } else if (event === 'finished') {
          waitingAnswer.value = false
        }
      },
    })
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message || '面试启动失败')
    await finishInterview(interviewId.value)
    session.value = null
    return
  } finally {
    chatLoading.value = false
  }
  scrollToBottom()
}

// ── 语音播报 ──
function speakText(text) {
  if (!voiceEnabled.value || !text) return
  if (!('speechSynthesis' in window)) return
  stopSpeak()
  const u = new SpeechSynthesisUtterance(text)
  u.lang = 'zh-CN'
  u.rate = 1.05
  window.speechSynthesis.speak(u)
}

function stopSpeak() {
  if ('speechSynthesis' in window) window.speechSynthesis.cancel()
}

function toggleVoice() {
  voiceEnabled.value = !voiceEnabled.value
  if (!voiceEnabled.value) stopSpeak()
}

// ── 语音输入 ──
function getRecognition() {
  if (recognition) return recognition
  const Ctor = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!Ctor) return null
  const r = new Ctor()
  r.lang = 'zh-CN'
  r.continuous = true
  r.interimResults = true
  r.onresult = (e) => {
    let interim = ''
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const res = e.results[i]
      if (res.isFinal) finalTranscript += res[0].transcript
      else interim += res[0].transcript
    }
    answerDraft.value = (finalTranscript + interim).trimStart()
  }
  r.onerror = () => {
    recording.value = false
  }
  r.onend = () => {
    if (recording.value) {
      try { r.start() } catch { recording.value = false }
    }
  }
  recognition = r
  return r
}

function stopRecording() {
  if (!recording.value) return
  recording.value = false
  if (recognition) {
    try { recognition.stop() } catch { /* 忽略 */ }
  }
}

function toggleRecording() {
  if (!micSupported || !waitingAnswer.value) return
  const r = getRecognition()
  if (!r) {
    ElMessage.warning('当前浏览器不支持语音输入，请使用 Chrome / Edge')
    return
  }
  if (recording.value) {
    stopRecording()
  } else {
    finalTranscript = ''
    answerDraft.value = ''
    recording.value = true
    try { r.start() } catch {
      recording.value = false
      ElMessage.warning('无法启动麦克风，请检查浏览器权限')
    }
  }
}

async function sendAnswer() {
  stopRecording()
  const content = answerDraft.value.trim()
  if (!content || !waitingAnswer.value) return
  chatMessages.value.push({ role: 'user', content })
  answerDraft.value = ''
  waitingAnswer.value = false
  chatLoading.value = true
  scrollToBottom()
  try {
    await answerInterview(interviewId.value, content, {
      onEvent: (event, data) => {
        if (event === 'question') {
          chatMessages.value.push({ role: 'ai', content: data?.question })
          speakText(data?.question)
          waitingAnswer.value = true
        } else if (event === 'finished') {
          const detail = data || {}
          ElMessage.success(detail.analysis ? '面试完成，报告已生成' : '面试结束')
          waitingAnswer.value = false
        }
      },
    })
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message || '提交失败')
  } finally {
    chatLoading.value = false
  }
  scrollToBottom()
}

async function endEarly() {
  if (chatMessages.value.length === 0) {
    session.value = null
    return
  }
  try {
    await finishInterview(interviewId.value)
    ElMessage.success('面试已结束，报告已生成')
  } catch {
    ElMessage.warning('面试已结束')
  }
  session.value = null
}

function scrollToBottom() {
  nextTick(() => {
    if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
  })
}

// 从岗位广场 / 首页跳转时带入岗位
function applyQueryParams() {
  const pid = Number(route.query.position_id)
  if (pid && positions.value.some((x) => x.id === pid)) {
    positionMode.value = 'preset'
    selectedPositionId.value = pid
  }
  const t = route.query.target
  if (t) {
    positionMode.value = 'custom'
    customPosition.value = String(t)
  }
}

watch(currentStep, scrollToBottom)

onUnmounted(() => {
  stopSpeak()
  if (recognition) {
    try { recognition.abort() } catch { /* 忽略 */ }
  }
})

onMounted(async () => {
  try {
    positions.value = await listPositions()
  } catch { /* 忽略 */ }
  try {
    resumes.value = await listResumes()
  } catch { /* 忽略 */ }
  try {
    interviewers.value = await listInterviewers()
    if (interviewers.value.length) {
      selectedInterviewerId.value = interviewers.value[0].id
    }
  } catch { /* 忽略 */ }
  applyQueryParams()
})
</script>

<style scoped>
.interview-page {
  max-width: 880px;
  margin: 0 auto;
}

/* ── 页头 ── */
.page-head {
  padding: 4px 0 18px;
  text-align: center;
}
.page-title {
  font-size: 26px;
  font-weight: 800;
  color: var(--app-text);
}
.page-desc {
  margin-top: 6px;
  font-size: 13px;
  color: var(--app-text-secondary);
}

/* ── 步骤条 ── */
.wizard {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 18px;
  padding: 16px 26px;
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
.w-step.active .w-label { color: #1a1a1a; }
.w-step.done .w-label { color: var(--app-text); }
.w-line {
  width: 52px;
  height: 3px;
  border-radius: 2px;
  background: var(--app-border);
  margin: 0 12px;
  transition: background 0.3s ease;
}
.w-line.done { background: linear-gradient(90deg, #10b981, #34d399); }

/* ── 步骤卡片 ── */
.w-body { margin-bottom: 0; }
.w-card {
  background: #fff;
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: var(--app-radius-lg, 16px);
  box-shadow: var(--app-shadow-md, 0 4px 16px rgba(20, 20, 20, 0.08));
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
  font-size: 16px;
  font-weight: 700;
  color: var(--app-text);
}
.w-desc {
  font-size: 13px;
  color: var(--app-text-secondary);
  margin-top: 2px;
}

/* ── 底部导航 ── */
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
  color: var(--app-text-muted);
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── 切换动画 ── */
.wizard-enter-active { transition: all 0.32s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1)); }
.wizard-leave-active { transition: all 0.18s ease; }
.wizard-enter-from { opacity: 0; transform: translateY(18px) scale(0.99); }
.wizard-leave-to { opacity: 0; transform: translateY(-10px) scale(0.99); }

/* ── 表单 ── */
.full { width: 100%; }
.mode-group { margin-bottom: 4px; }
.opt-company { color: #303133; font-weight: 600; font-size: 13px; }
.opt-position { margin-left: 8px; color: #909399; font-size: 12px; }
.opt-meta { float: right; color: #c0c4cc; font-size: 12px; }

/* ── 面试官卡片 ── */
.interviewer-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
}
.iv-card {
  background: #fff;
  border: 1.5px solid #e4e9f2;
  border-radius: 14px;
  padding: 14px;
  text-align: left;
  cursor: pointer;
  transition: all 0.22s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.iv-card:hover {
  border-color: rgba(139, 92, 246, 0.5);
  box-shadow: var(--app-shadow-sm, 0 1px 3px rgba(20, 20, 20, 0.06));
}
.iv-card.on {
  border-color: #333333;
  background: rgba(26, 26, 26, 0.05);
  box-shadow: 0 0 0 4px rgba(26, 26, 26, 0.1);
}
.iv-top {
  display: flex;
  align-items: center;
  gap: 10px;
}
.iv-avatar {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #444444, #333333);
}
.iv-info {
  flex: 1;
  min-width: 0;
}
.iv-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--app-text);
}
.iv-title {
  font-size: 11px;
  color: var(--app-text-muted);
  margin-top: 1px;
}
.iv-check {
  color: #333333;
  font-size: 16px;
  flex-shrink: 0;
}
.iv-persona {
  margin-top: 10px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--app-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.iv-tags {
  display: flex;
  gap: 6px;
  margin-top: 10px;
}
.iv-tag {
  font-size: 11px;
  color: #333333;
  background: rgba(26, 26, 26, 0.1);
  border-radius: 999px;
  padding: 2px 10px;
}
.loading-text {
  text-align: center;
  color: var(--app-text-muted);
  padding: 30px 0;
}

/* ── 难度卡片 ── */
.difficulty-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.diff-card {
  background: #fff;
  border: 1.5px solid #e4e9f2;
  border-radius: 14px;
  padding: 16px 14px;
  text-align: center;
  cursor: pointer;
  transition: all 0.22s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.diff-card:hover {
  border-color: rgba(16, 185, 129, 0.5);
}
.diff-card.on {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.06);
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.1);
}
.diff-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--app-text);
}
.diff-desc {
  margin-top: 6px;
  font-size: 12px;
  color: var(--app-text-secondary);
  line-height: 1.55;
}
.rounds-form {
  margin-top: 16px;
}
.start-summary {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
  background: #fafaf9;
  border: 1px dashed #dbe3ef;
  border-radius: 12px;
  padding: 12px 16px;
  margin-top: 8px;
}
.sum-item {
  font-size: 13px;
  color: var(--app-text-secondary);
}
.sum-label {
  margin-right: 6px;
}
.sum-item b {
  color: var(--app-text);
}

/* ── 对话区 ── */
.chat-shell {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 132px);
  min-height: 480px;
  background: #fff;
  border-radius: var(--app-radius-lg, 16px);
  border: 1px solid rgba(226, 232, 240, 0.8);
  box-shadow: var(--app-shadow-md, 0 4px 16px rgba(20, 20, 20, 0.08));
  overflow: hidden;
}
.chat-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--app-border);
}
.chat-tools {
  display: flex;
  align-items: center;
  gap: 10px;
}
.tool-btn {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--app-border);
  background: #fff;
  cursor: pointer;
  color: var(--app-text-muted);
  transition: all 0.2s ease;
}
.tool-btn:hover { border-color: #1a1a1a; color: #1a1a1a; }
.tool-btn.on { color: #fff; background: #1a1a1a; border-color: #1a1a1a; }
.mic-btn {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--app-border);
  background: #fff;
  cursor: pointer;
  color: var(--app-text-secondary);
  transition: all 0.2s ease;
}
.mic-btn:hover:not(:disabled) { border-color: #1a1a1a; color: #1a1a1a; }
.mic-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.mic-btn.on {
  color: #fff;
  background: #ef4444;
  border-color: #ef4444;
  animation: mic-pulse 1.2s ease-in-out infinite;
}
@keyframes mic-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.45); }
  50% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
}
.chat-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--app-text);
}
.chat-sub {
  font-size: 12px;
  color: var(--app-text-muted);
  margin-top: 3px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.chat-dot { color: var(--app-border-strong); }
.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  background: #fafbfe;
}
.msg {
  display: flex;
  gap: 10px;
  max-width: 84%;
}
.msg.user {
  align-self: flex-end;
  justify-content: flex-end;
}
.msg-avatar {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}
.ai-avatar {
  background: linear-gradient(135deg, #1a1a1a, #1a1a1a);
}
.msg-bubble {
  padding: 11px 14px;
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}
.ai-bubble {
  background: #fff;
  border: 1px solid var(--app-border);
  color: #1f2937;
  border-top-left-radius: 4px;
}
.user-bubble {
  background: linear-gradient(135deg, #1a1a1a, #1a1a1a);
  color: #fff;
  border-top-right-radius: 4px;
}
.thinking {
  display: flex;
  align-items: center;
  gap: 5px;
}
.tdot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--app-text-muted);
  animation: tbounce 1.1s infinite ease-in-out;
}
.tdot:nth-child(2) { animation-delay: 0.15s; }
.tdot:nth-child(3) { animation-delay: 0.3s; }
@keyframes tbounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
  30% { transform: translateY(-4px); opacity: 1; }
}
.chat-input {
  display: flex;
  gap: 10px;
  padding: 14px 16px;
  border-top: 1px solid var(--app-border);
  background: #fff;
}
.send-btn {
  width: 48px;
  height: 48px;
  border: none;
  border-radius: 14px;
  background: linear-gradient(135deg, #1a1a1a, #1a1a1a);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: transform 160ms var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1)), opacity 0.2s;
}
.send-btn:hover { transform: scale(1.04); }
.send-btn:active { transform: scale(0.94); }
.send-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
</style>
