<template>
  <div class="interview-page">
    <!-- ================= 向导式设置区 ================= -->
    <template v-if="!session">
      <div class="page-head">
        <div class="page-title">模拟面试</div>
        <div class="page-desc">三步完成设置，选择你的目标岗位、面试官与难度</div>
      </div>

      <!-- 步骤条 -->
      <WizardStepper :steps="wizardSteps" :current-step="currentStep" :max-step="maxStep" @step="goStep" />

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
                  <span class="iv-tag">{{ typeText(iv) }}</span>
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
              <el-form-item label="回答方式">
                <el-radio-group v-model="answerMode" class="mode-group">
                  <el-radio-button
                    v-for="m in answerModes"
                    :key="m.value"
                    :value="m.value"
                    :disabled="m.value !== 'text' && !micSupported"
                  >
                    {{ m.label }}
                  </el-radio-button>
                </el-radio-group>
                <div class="mode-hint">{{ answerModeHint }}</div>
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
          <button
            v-if="answerMode === 'video'"
            class="tool-btn"
            :class="{ on: camEnabled }"
            :title="camEnabled ? '关闭摄像头' : '开启摄像头'"
            @click="toggleCamera"
          >
            <el-icon :size="16"><VideoCamera /></el-icon>
          </button>
          <el-button size="small" :loading="ending" @click="endEarly">结束面试</el-button>
        </div>
      </div>

      <div class="chat-main">
        <div ref="chatBody" class="chat-body">
          <div v-if="connError" class="conn-banner">
            <el-icon :size="14"><Warning /></el-icon>
            <span class="conn-text">{{ connError }}</span>
            <button v-if="connAction" class="conn-retry" @click="connAction()">重试</button>
          </div>
          <template v-for="(m, i) in chatMessages" :key="i">
            <div v-if="m.role === 'ai'" class="msg ai" :class="{ typing: m.typing }" @click="m.typing && skipTyping(m)">
              <div class="msg-avatar ai-avatar">{{ interviewerLabel.slice(0, 1) }}</div>
              <div class="msg-bubble ai-bubble">
                {{ m.shown }}<span v-if="m.typing" class="typing-caret"></span>
              </div>
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

        <!-- 视频模式：右侧摄像头栏（含画面活动监测） -->
        <aside v-if="answerMode === 'video'" class="cam-panel">
          <div class="cam-title"><span class="cam-dot"></span>我的画面</div>
          <video v-show="camEnabled" ref="videoRef" autoplay muted playsinline></video>
          <div v-if="!camEnabled" class="cam-empty">
            <el-icon :size="18"><VideoCamera /></el-icon>
            <span>{{ camError || '摄像头未开启' }}</span>
          </div>
          <div v-else class="cam-status" :class="{ idle: !camActive }">
            {{ camActive ? '画面正常' : '画面静止，请靠近摄像头' }}
          </div>
        </aside>
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
          @input="onDraftTyped"
          @keydown="onAnswerKeydown"
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
import { useRoute, useRouter } from 'vue-router'
import WizardStepper from '@/components/wizard/WizardStepper.vue'
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
  VideoCamera,
} from '@element-plus/icons-vue'
import { listResumes } from '@/api/diagnostic'
import { listPositions } from '@/api/question'
import { listInterviewers } from '@/api/interviewer'
import {
  answerInterview,
  createInterview,
  finishInterview,
  getInterviewDetail,
  startInterview,
} from '@/api/interview'
import {
  TYPEWRITER_TICK_MS,
  createAiMessage,
  mapHistoryMessage,
  typewriterStep,
  typingTick,
} from '@/utils/typewriter'

const route = useRoute()
const router = useRouter()

// 结束面试请求进行中（防重复点击）
const ending = ref(false)

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

// 断线提示：connError 显示横幅，connAction 为“重试”回调
const connError = ref('')
const connAction = ref(null)

// 打字机定时器集合（onUnmounted 时统一清理）
let typeTimers = []

// 面试结束后延迟跳转面试记录页的定时器（onUnmounted 时清理，避免跳转前用户已离开）
let farewellTimer = null

// SSE 流控制：切换页面时中断所有进行中的流，
// 避免后台回调在组件卸载后继续创建定时器 / 语音播报，造成内存泄漏
let sseController = null
let isUnmounted = false

// ── 语音面试（Web Speech API）──
const voiceEnabled = ref(true)
const micSupported = typeof window !== 'undefined' && (
  'SpeechRecognition' in window || 'webkitSpeechRecognition' in window
)
const recording = ref(false)
let finalTranscript = ''
let recognition = null

// ── 回答方式（T7 视频面试降级方案）──
const answerModes = [
  { value: 'text', label: '文字', desc: '纯文字输入，适用所有浏览器' },
  { value: 'voice', label: '语音', desc: '语音输入自动转文字，回答更自然' },
  { value: 'video', label: '视频', desc: '摄像头 + 语音输入，画面活动监测（实验性）' },
]
const answerMode = ref(micSupported ? 'voice' : 'text')
const answerModeHint = computed(
  () => answerModes.find((m) => m.value === answerMode.value)?.desc || '',
)

// ── 摄像头（视频模式）──
const camEnabled = ref(false)   // 视频轨道是否已开启
const camError = ref('')        // 摄像头失败原因
const camActive = ref(true)     // 画面活动检测结果（默认视为正常）
const videoRef = ref(null)
let camStream = null
let camTracks = []
let activityTimer = null
let lastFrame = null

// 每 4s 截一帧到小 canvas，与上一帧比较像素差 → 画面是否有人活动（轻量方案，无需 face-api）
function startActivityCheck() {
  if (activityTimer) return
  lastFrame = null
  camActive.value = true
  activityTimer = setInterval(() => {
    const v = videoRef.value
    if (!v || v.readyState < 2) return
    const canvas = document.createElement('canvas')
    canvas.width = 96
    canvas.height = 72
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.drawImage(v, 0, 0, 96, 72)
    let data
    try {
      data = ctx.getImageData(0, 0, 96, 72).data
    } catch {
      return
    }
    if (lastFrame) {
      let diff = 0
      for (let i = 0; i < data.length; i += 32) {
        diff += Math.abs(data[i] - lastFrame[i])
      }
      camActive.value = diff > 700
    }
    lastFrame = data
  }, 4000)
}

function stopCamera() {
  if (activityTimer) {
    clearInterval(activityTimer)
    activityTimer = null
  }
  lastFrame = null
  camActive.value = true
  camTracks.forEach((t) => {
    try { t.stop() } catch { /* 忽略 */ }
  })
  camTracks = []
  if (videoRef.value) videoRef.value.srcObject = null
  camStream = null
  camEnabled.value = false
}

async function enableCamera() {
  if (camStream) return
  if (!navigator.mediaDevices?.getUserMedia) {
    camError.value = '当前浏览器不支持摄像头'
    fallbackVideoMode()
    return
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480 },
      audio: false,
    })
    camStream = stream
    camTracks = stream.getVideoTracks()
    camEnabled.value = true
    camError.value = ''
    await nextTick()
    if (videoRef.value) {
      videoRef.value.srcObject = stream
      videoRef.value.play().catch(() => {})
    }
    startActivityCheck()
  } catch {
    camError.value = '摄像头不可用或未授权'
    fallbackVideoMode()
  }
}

// 视频模式降级：摄像头失败 → 语音（语音不可用 → 文字），不阻塞面试主流程
function fallbackVideoMode() {
  stopCamera()
  const next = micSupported ? 'voice' : 'text'
  answerMode.value = next
  ElMessage.warning(`${camError.value}，已切换为${next === 'voice' ? '语音' : '文字'}回答`)
}

function toggleCamera() {
  if (camStream) stopCamera()
  else enableCamera()
}

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
  // 会话恢复模式：优先使用后端返回的面试官名称
  if (session.value?.interviewer_name) return session.value.interviewer_name
  const iv = interviewers.value.find((x) => x.id === selectedInterviewerId.value)
  return iv ? iv.name : ''
})

const difficultyLabel = computed(() => {
  const d = difficulties.find((x) => x.value === selectedDifficulty.value)
  return d ? d.label : ''
})

const sessionPositionLabel = computed(() => {
  // 会话恢复模式：优先使用后端返回的岗位信息（可能是自定义岗位，不在 preset 列表中）
  if (session.value?.position_name) return session.value.position_name
  if (session.value?.target_position) return session.value.target_position
  const p = positions.value.find((x) => x.id === selectedPositionId.value)
  return p ? positionOptionLabel(p) : (customPosition.value.trim() || '模拟面试')
})

function positionMeta(p) {
  const d = { junior: '初级', mid: '中级', senior: '高级' }[p.difficulty] || p.difficulty || ''
  const dir = { backend: '后端', frontend: '前端', algorithm: '算法', product: '产品', operations: '运营', data: '数据' }[p.direction] || ''
  return `${dir} ${d}`.trim()
}

function typeText(iv) {
  // 内置面试官按名称显示精确标签（后端按名称命中专属模式）
  const byName = {
    资深技术面试官: '技术面',
    'CTO 技术面': '架构面',
    'HR 综合面': '综合面',
    压力面: '压力面',
    转行质疑面试官: '转行面',
    '谈薪 HR': '谈薪面',
  }
  if (iv && typeof iv === 'object') {
    if (iv.name && byName[iv.name]) return byName[iv.name]
    return { all: '通用', normal: '常规面', switch: '转行面', salary: '谈薪面' }[iv.interview_type] || iv.interview_type || ''
  }
  return iv || ''
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
    // v1.2：面试类型跟随所选面试官（normal/switch/salary），不再硬编码
    // 面试官 interview_type 可能为 'all'（通用），归一为 normal 以通过后端校验
    const selectedIv = interviewers.value.find((x) => x.id === selectedInterviewerId.value)
    const rawType = selectedIv?.interview_type || 'normal'
    const interview_type = ['normal', 'switch', 'salary'].includes(rawType) ? rawType : 'normal'
    const payload = {
      mode: answerMode.value,
      interview_type,
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
    // 视频模式：会话就绪后开启摄像头（失败自动回退语音/文字）
    if (answerMode.value === 'video') {
      await enableCamera()
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message || '创建面试失败')
  } finally {
    creating.value = false
  }
}

async function beginChat() {
  chatLoading.value = true
  waitingAnswer.value = false
  connError.value = ''
  connAction.value = null
  if (sseController) sseController.abort()
  sseController = new AbortController()
  try {
    await startInterview(interviewId.value, {
      signal: sseController.signal,
      onEvent: (event, data) => {
        if (isUnmounted) return
        if (event === 'question') {
          pushAiMessage(data?.question)
        } else if (event === 'finished') {
          waitingAnswer.value = false
          scheduleGoHistory()
        }
      },
    })
  } catch (e) {
    // 组件已卸载或主动中断时不提示，避免误报断线
    if (isUnmounted || e?.name === 'AbortError') return
    // 保留会话，提示断线并允许重试（startInterview 幂等，可安全重发）
    connError.value = e.response?.data?.detail || e.message || '网络连接中断，面试尚未开始'
    connAction.value = () => {
      beginChat()
    }
    ElMessage.error(connError.value)
  } finally {
    chatLoading.value = false
  }
  scrollToBottom()
}

// ── 打字机效果：question 逐字展示，点击气泡可跳过 ──
// opts.unlock=false 用于面试结束语：只打字展示，不打字结束后恢复作答 / 自动开麦
function pushAiMessage(content, opts = {}) {
  if (!content) return
  const autoUnlock = opts.unlock !== false
  // push 后从响应式数组中取回 proxy 引用，否则修改 msg.shown 不会触发视图更新
  chatMessages.value.push(createAiMessage(content))
  const msg = chatMessages.value[chatMessages.value.length - 1]
  msg._autoUnlock = autoUnlock
  speakText(content)
  // 约 2.5 秒打完整段（步长按文本长度自适应）
  const step = typewriterStep(content.length)
  let pos = 0
  const timer = setInterval(() => {
    const tick = typingTick(pos, step, content.length)
    pos = tick.pos
    msg.shown = content.slice(0, pos)
    scrollToBottom()
    if (tick.done) {
      clearInterval(timer)
      msg._timer = null
      msg.typing = false
      msg.shown = content
      if (autoUnlock) {
        waitingAnswer.value = true
        // 语音/视频模式：问题已完整显示，自动开麦让用户直接回答
        maybeAutoStartMic()
      }
    }
  }, TYPEWRITER_TICK_MS)
  msg._timer = timer
  typeTimers.push(timer)
  scrollToBottom()
  return msg
}

function skipTyping(msg) {
  if (msg._timer) {
    clearInterval(msg._timer)
    msg._timer = null
  }
  msg.typing = false
  msg.shown = msg.full
  if (msg._autoUnlock !== false) {
    waitingAnswer.value = true
    maybeAutoStartMic()
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
  // 播报自然结束（未被提前停止）时也自动开麦
  u.onend = () => { maybeAutoStartMic() }
  u.onerror = () => { maybeAutoStartMic() }
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
    // 识别已停止（如用户已按 Enter 发送）后不再覆盖输入框，避免 stop() 的收尾结果清空内容
    if (!recording.value) return
    let interim = ''
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const res = e.results[i]
      if (res.isFinal) finalTranscript += res[0].transcript
      else interim += res[0].transcript
    }
    answerDraft.value = (finalTranscript + interim).trimStart()
  }
  r.onerror = (e) => {
    // 自动开麦后用户可能尚未开口：no-speech 属正常，保持录音并重启识别
    if (e?.error === 'no-speech' && recording.value && waitingAnswer.value) {
      try { r.start() } catch { recording.value = false }
      return
    }
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

function startRecording() {
  if (!micSupported) return false
  const r = getRecognition()
  if (!r) return false
  if (recording.value) return true
  finalTranscript = ''
  answerDraft.value = ''
  recording.value = true
  try {
    r.start()
    return true
  } catch {
    recording.value = false
    return false
  }
}

function toggleRecording() {
  if (!micSupported || !waitingAnswer.value) return
  if (recording.value) {
    stopRecording()
    return
  }
  if (!startRecording()) {
    ElMessage.warning('无法启动麦克风，请检查浏览器权限')
  }
}

// AI 回答后自动开麦（语音/视频模式）：问题已完整显示在屏幕上，直接开麦让用户开口回答。
// 若 AI 语音播报还在进行，先停止播报，避免其声音被识别进用户回答；
// 不再等待播报结束（之前按播报时长等待导致麦克风迟迟不打开）。
function maybeAutoStartMic() {
  if (isUnmounted) return
  if (!micSupported || !waitingAnswer.value) return
  if (answerMode.value === 'text') return
  if (recording.value) return
  if ('speechSynthesis' in window && (window.speechSynthesis.speaking || window.speechSynthesis.pending)) {
    stopSpeak()
  }
  startRecording()
}

// 用户手动编辑输入框时停止语音识别，避免识别结果覆盖手打内容
function onDraftTyped() {
  if (recording.value) stopRecording()
}

// Enter 发送：过滤中文输入法组词确认的 Enter，避免误发/发空
function onAnswerKeydown(e) {
  if (e.isComposing) return
  if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.altKey && !e.metaKey) {
    e.preventDefault()
    sendAnswer()
  }
}

async function sendAnswer() {
  // 先取内容再停识别：stop() 的收尾 onresult 会覆盖输入框，顺序反了会发空内容
  const content = answerDraft.value.trim()
  if (!content || !waitingAnswer.value) return
  stopRecording()
  chatMessages.value.push({ role: 'user', content })
  answerDraft.value = ''
  waitingAnswer.value = false
  chatLoading.value = true
  connError.value = ''
  connAction.value = null
  scrollToBottom()
  if (sseController) sseController.abort()
  sseController = new AbortController()
  try {
    await answerInterview(interviewId.value, content, {
      signal: sseController.signal,
      onEvent: (event, data) => {
        if (isUnmounted) return
        if (event === 'question') {
          pushAiMessage(data?.question)
        } else if (event === 'farewell') {
          // 面试结束语：打字机展示为 AI 气泡，但不解锁输入框、不自动开麦
          pushAiMessage(data?.message, { unlock: false })
        } else if (event === 'finished') {
          const detail = data || {}
          ElMessage.success(detail.message || '面试结束，报告正在生成')
          waitingAnswer.value = false
          scheduleGoHistory()
        }
      },
    })
  } catch (e) {
    // 组件已卸载或主动中断时不提示，避免误报断线
    if (isUnmounted || e?.name === 'AbortError') return
    // 移除未成功送达的回答（服务端未记录），恢复输入内容，由用户决定是否重发
    const last = chatMessages.value[chatMessages.value.length - 1]
    if (last && last.role === 'user' && last.content === content) {
      chatMessages.value.pop()
    }
    answerDraft.value = content
    connError.value = e.response?.data?.detail || e.message || '网络连接中断，回答可能未送达'
    connAction.value = () => {
      connError.value = ''
      connAction.value = null
      waitingAnswer.value = true
    }
    ElMessage.error(connError.value)
  } finally {
    chatLoading.value = false
  }
  scrollToBottom()
}

async function endEarly() {
  if (ending.value) return
  stopCamera()
  if (chatMessages.value.length === 0) {
    session.value = null
    return
  }
  ending.value = true
  try {
    const res = await finishInterview(interviewId.value)
    const farewell = res?.farewell
    if (farewell) pushAiMessage(farewell, { unlock: false })
    ElMessage.success('面试已结束，报告正在生成')
  } catch {
    ElMessage.warning('面试已结束')
  } finally {
    ending.value = false
  }
  scheduleGoHistory()
}

// 面试结束（自动到轮数 / 手动结束）：告别语展示数秒后自动跳转面试记录页。
// 定时器幂等：结束事件与手动结束可能先后触发，只允许排定一次跳转。
function scheduleGoHistory() {
  if (farewellTimer || isUnmounted) return
  farewellTimer = setTimeout(() => {
    farewellTimer = null
    if (isUnmounted) return
    stopSpeak()
    stopRecording()
    session.value = null
    router.push({ name: 'history' })
  }, 3500)
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
  // 先标记卸载并中断 SSE 流，阻断后续回调创建新的定时器 / 语音播报
  isUnmounted = true
  if (sseController) {
    sseController.abort()
    sseController = null
  }
  stopSpeak()
  if (farewellTimer) {
    clearTimeout(farewellTimer)
    farewellTimer = null
  }
  for (const t of typeTimers) clearInterval(t)
  typeTimers = []
  if (recognition) {
    try { recognition.abort() } catch { /* 忽略 */ }
  }
  stopCamera()
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
  // 会话中断恢复：从历史记录“继续面试”进入
  const rid = Number(route.query.interview_id)
  if (rid) {
    await resumeInterview(rid)
  } else {
    applyQueryParams()
  }
})

// ── 会话恢复：加载进行中的面试并重建聊天上下文 ──
async function resumeInterview(id) {
  try {
    const d = await getInterviewDetail(id)
    if (d.status === 'reported') {
      ElMessage.info('该面试已结束')
      if (d.report_id) {
        router.replace({ name: 'report', params: { id: d.report_id } })
      }
      return
    }
    if (!['created', 'asking', 'decide_next'].includes(d.status)) {
      ElMessage.info('该面试当前不可继续')
      return
    }
    session.value = d
    interviewId.value = d.id
    chatMessages.value = (d.messages || []).map(mapHistoryMessage)
    selectedPositionId.value = d.position_id
    customPosition.value = d.target_position || ''
    selectedDifficulty.value = d.difficulty || 'normal'
    maxRounds.value = d.max_rounds || 6
    selectedInterviewerId.value = d.interviewer_id
    waitingAnswer.value = true
    scrollToBottom()
    // 会话恢复：还原回答方式
    if (['text', 'voice', 'video'].includes(d.mode)) {
      answerMode.value = d.mode
    }
    // 会话恢复：原会话为视频模式且浏览器支持语音 → 恢复摄像头
    if (d.mode === 'video' && micSupported) {
      nextTick(() => enableCamera())
    }
    // 语音/视频模式：恢复后自动开麦，直接开口即可
    maybeAutoStartMic()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message || '恢复面试失败')
  }
}
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
  position: relative;
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
.chat-main {
  flex: 1;
  min-height: 0;
  display: flex;
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
  min-width: 0;
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

/* 打字机光标 */
.typing-caret {
  display: inline-block;
  width: 2px;
  height: 1em;
  margin-left: 2px;
  vertical-align: -0.15em;
  background: var(--app-cyan, #5ad0e6);
  animation: caret-blink 0.9s steps(1) infinite;
}
@keyframes caret-blink {
  0%, 55% { opacity: 1; }
  56%, 100% { opacity: 0; }
}
.msg.ai.typing {
  cursor: pointer;
  position: relative;
}
.msg.ai.typing:hover::after {
  content: '点击跳过';
  position: absolute;
  top: -8px;
  left: 44px;
  font-size: 11px;
  color: var(--app-text-muted);
  background: rgba(0, 0, 0, 0.6);
  padding: 2px 8px;
  border-radius: 6px;
  pointer-events: none;
}

/* 断线横幅 */
.conn-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  margin-bottom: 12px;
  border-radius: 10px;
  background: rgba(242, 193, 78, 0.12);
  border: 1px solid rgba(242, 193, 78, 0.4);
  color: var(--app-amber, #d97706);
  font-size: 13px;
}
.conn-text {
  flex: 1;
}
.conn-retry {
  border: none;
  background: rgba(242, 193, 78, 0.2);
  color: var(--app-amber, #d97706);
  padding: 4px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
}
.conn-retry:hover {
  background: rgba(242, 193, 78, 0.35);
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

/* 视频模式：右侧摄像头栏 */
.cam-panel {
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #000;
  border-left: 1px solid rgba(226, 232, 240, 0.8);
}
.cam-title {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  background: rgba(15, 23, 42, 0.92);
}
.cam-panel video {
  flex: 1;
  min-height: 0;
  display: block;
  width: 100%;
  object-fit: cover;
  transform: scaleX(-1); /* 镜像，符合视频会议习惯 */
}
.cam-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--app-text-muted);
  font-size: 12px;
  background: #f8fafc;
}
.cam-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 10px;
  font-size: 11px;
  color: #fff;
  background: rgba(16, 185, 129, 0.85);
}
.cam-status.idle { background: rgba(242, 193, 78, 0.9); color: #5b3a00; }
.cam-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
  animation: cam-blink 1.4s ease-in-out infinite;
}
@keyframes cam-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.25; }
}
.mode-group { margin-bottom: 4px; }
.mode-hint {
  margin-top: 4px;
  font-size: 12px;
  color: var(--app-text-muted);
}

/* ==================== 深色液态玻璃覆盖 ==================== */
.wizard {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-highlight), var(--app-shadow-sm);
}
.w-dot {
  background: rgba(255, 255, 255, 0.06);
  border: 2px solid var(--app-border);
}
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

.w-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-highlight), var(--app-shadow-md);
}
.w-ico {
  color: #071018;
  background: var(--app-brand-gradient);
  box-shadow: 0 6px 14px -4px rgba(90, 208, 230, 0.5);
}
.w-ico.grad {
  background: linear-gradient(135deg, #6b8bff, #8b6bff);
  box-shadow: 0 6px 14px -4px rgba(107, 139, 255, 0.5);
}
.w-ico.green {
  background: linear-gradient(135deg, #43d9a3, #2fb589);
  box-shadow: 0 6px 14px -4px rgba(67, 217, 163, 0.45);
}

.opt-company { color: var(--app-text); }
.opt-position { color: var(--app-text-secondary); }
.opt-meta { color: var(--app-text-muted); }

.iv-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1.5px solid var(--app-border);
}
.iv-card:hover {
  border-color: rgba(107, 139, 255, 0.5);
  box-shadow: var(--glass-highlight);
}
.iv-card.on {
  border-color: var(--app-cyan);
  background: var(--app-brand-soft);
  box-shadow: 0 0 0 4px rgba(90, 208, 230, 0.14);
}
.iv-avatar {
  color: #071018;
  background: var(--app-brand-gradient);
}
.iv-check { color: var(--app-cyan); }
.iv-tag {
  color: var(--app-text-secondary);
  background: rgba(255, 255, 255, 0.07);
}

.diff-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1.5px solid var(--app-border);
}
.diff-card:hover {
  border-color: rgba(67, 217, 163, 0.5);
}
.diff-card.on {
  border-color: var(--app-success);
  background: rgba(67, 217, 163, 0.1);
  box-shadow: 0 0 0 4px rgba(67, 217, 163, 0.1);
}
.start-summary {
  background: rgba(255, 255, 255, 0.04);
  border: 1px dashed rgba(255, 255, 255, 0.18);
}

/* 对话区玻璃化 */
.chat-shell {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-highlight), var(--app-shadow-md);
}
.tool-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--app-border);
}
.tool-btn:hover { border-color: rgba(90, 208, 230, 0.5); color: var(--app-text); }
.tool-btn.on { color: #071018; background: var(--app-brand-gradient); border-color: transparent; }
.mic-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--app-border);
}
.mic-btn:hover:not(:disabled) { border-color: rgba(90, 208, 230, 0.5); color: var(--app-text); }
.mic-btn.on {
  color: #fff;
  background: #ff6b7a;
  border-color: #ff6b7a;
}
@keyframes mic-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255, 107, 122, 0.5); }
  50% { box-shadow: 0 0 0 8px rgba(255, 107, 122, 0); }
}
.chat-body {
  background: rgba(5, 7, 14, 0.28);
}
.ai-avatar {
  color: #071018;
  background: var(--app-brand-gradient);
}
.ai-bubble {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--app-border);
  color: var(--app-text);
}
.user-bubble {
  background: var(--app-brand-gradient);
  color: #071018;
  font-weight: 500;
}
.chat-input {
  background: rgba(255, 255, 255, 0.03);
  border-top: 1px solid var(--app-border);
}
.send-btn {
  background: var(--app-brand-gradient);
  color: #071018;
}
.cam-panel {
  border-left: 1px solid var(--app-border);
  background: rgba(5, 7, 14, 0.55);
  box-shadow: var(--glass-highlight), var(--app-shadow-md);
}
.cam-title { color: var(--app-text); }
.cam-empty { background: rgba(5, 7, 14, 0.28); }
.cam-status { background: rgba(67, 217, 163, 0.4); color: #eafff6; }
.cam-status.idle { background: rgba(242, 193, 78, 0.35); color: #ffe9b3; }

/* 窄屏：视频栏收窄，避免挤压聊天区 */
@media (max-width: 680px) {
  .cam-panel { width: 168px; }
}
</style>