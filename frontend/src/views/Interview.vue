<template>
  <div class="interview-page">
    <InterviewWizard
      v-if="!session"
      :positions="positions"
      :resumes="resumes"
      :interviewers="interviewers"
      v-model:position-mode="positionMode"
      v-model:selected-position-id="selectedPositionId"
      v-model:custom-position="customPosition"
      v-model:selected-resume-id="selectedResumeId"
      v-model:selected-interviewer-id="selectedInterviewerId"
      v-model:selected-difficulty="selectedDifficulty"
      v-model:max-rounds="maxRounds"
      v-model:answer-mode="answerMode"
      :mic-supported="micSupported"
      :creating="creating"
      @create="createSession"
    />
    <ChatPanel
      v-else
      :messages="chatMessages"
      :chat-loading="chatLoading"
      :conn-error="connError"
      :conn-action="connAction"
      :session-position-label="sessionPositionLabel"
      :interviewer-label="interviewerLabel"
      :difficulty-label="difficultyLabel"
      :max-rounds="maxRounds"
      :voice-enabled="voiceEnabled"
      :answer-mode="answerMode"
      :cam-enabled="camEnabled"
      :cam-error="camError"
      :cam-active="camActive"
      :mic-supported="micSupported"
      :recording="recording"
      :waiting-answer="waitingAnswer"
      v-model:answer-draft="answerDraft"
      :ending="ending"
      @toggle-voice="toggleVoice"
      @toggle-camera="toggleCamera"
      @toggle-recording="toggleRecording"
      @end-early="endEarly"
      @skip-typing="skipTyping"
      @draft-typed="onDraftTyped"
      @answer-keydown="onAnswerKeydown"
      @send-answer="sendAnswer"
      @video-el="onVideoEl"
    />
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
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
import { useCamera } from '@/composables/useCamera'
import { useVoice } from '@/composables/useVoice'
import InterviewWizard from '@/components/interview/InterviewWizard.vue'
import ChatPanel from '@/components/interview/ChatPanel.vue'

const route = useRoute()
const router = useRouter()

// 结束面试请求进行中（防重复点击）
const ending = ref(false)

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

// ── 回答方式（T7 视频面试降级方案）──
const answerModes = [
  { value: 'text', label: '文字', desc: '纯文字输入，适用所有浏览器' },
  { value: 'voice', label: '语音', desc: '语音输入自动转文字，回答更自然' },
  { value: 'video', label: '视频', desc: '摄像头 + 语音输入，画面活动监测（实验性）' },
]

// ── 会话状态 ──
const session = ref(null)
const creating = ref(false)
const chatMessages = ref([])
const chatLoading = ref(false)
const waitingAnswer = ref(false)
const answerDraft = ref('')
const interviewId = ref(null)

// 断线提示：connError 显示横幅，connAction 为"重试"回调
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

// 当前未送达回答的幂等键 { id, content }：
// 断线重发同一回答时复用 id，服务端据此去重，避免回答被重复记录、轮数被重复推进
let pendingAnswerId = null

// ── 语音 + 摄像头（composables）──
const { voiceEnabled, micSupported, recording, speakText, stopRecording, toggleRecording, toggleVoice, maybeAutoStartMic, dispose: disposeVoice } = useVoice({
  getWaitingAnswer: () => waitingAnswer.value,
  getAnswerMode: () => answerMode.value,
  getIsUnmounted: () => isUnmounted,
  setAnswerDraft: (t) => { answerDraft.value = t },
})

const answerMode = ref(micSupported ? 'voice' : 'text')
const { camEnabled, camError, camActive, videoRef, stopCamera, enableCamera, toggleCamera } = useCamera({
  getMicSupported: () => micSupported,
  setAnswerMode: (m) => { answerMode.value = m },
})

function onVideoEl(el) {
  videoRef.value = el
}

// ── 派生（会话区）──
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
  return p ? (p.company ? `${p.company} ${p.name}` : p.name) : (customPosition.value.trim() || '模拟面试')
})

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
  } catch {
    /* 拦截器已统一提示 */
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
}

// 用户手动编辑输入框时停止语音识别，避免识别结果覆盖手打内容
function onDraftTyped() {
  if (recording.value) stopRecording()
}

// Enter 发送：过滤中文输入法组词确认的 Enter，避免误发/发空
function onAnswerKeydown(e) {
  if (!e || e.isComposing) return
  if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.altKey && !e.metaKey) {
    e.preventDefault()
    sendAnswer()
  }
}

function genRequestId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID()
  return `req-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

// 单次发送回答：收到 question / finished 即视为送达成功
function doSendAnswer(content, requestId) {
  if (sseController) sseController.abort()
  sseController = new AbortController()
  return answerInterview(interviewId.value, content, {
    requestId,
    signal: sseController.signal,
    onEvent: (event, data) => {
      if (isUnmounted) return
      if (event === 'question') {
        pendingAnswerId = null // 送达成功，幂等键作废
        pushAiMessage(data?.question)
      } else if (event === 'farewell') {
        // 面试结束语：打字机展示为 AI 气泡，但不解锁输入框、不自动开麦
        pushAiMessage(data?.message, { unlock: false })
      } else if (event === 'finished') {
        pendingAnswerId = null
        const detail = data || {}
        ElMessage.success(detail.message || '面试结束，报告正在生成')
        waitingAnswer.value = false
        scheduleGoHistory()
      }
    },
  })
}

async function sendAnswerWithRetry(content, requestId, retriesLeft) {
  try {
    await doSendAnswer(content, requestId)
    connError.value = ''
    connAction.value = null
  } catch (e) {
    // 组件已卸载或主动中断时不提示，避免误报断线
    if (isUnmounted || e?.name === 'AbortError') return
    // 服务端明确报错（error 事件）不自动重试，直接交给用户处理
    if (retriesLeft > 0 && e?.name !== 'SSEError') {
      connError.value = '网络不稳定，正在重试发送回答…'
      await new Promise((r) => setTimeout(r, 1200))
      return sendAnswerWithRetry(content, requestId, retriesLeft - 1)
    }
    // 多次失败：移除未送达的回答，恢复输入内容；保留幂等键，用户重发时复用
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
  // 同一回答断线重发复用同一幂等键；换内容则重新生成
  if (!pendingAnswerId || pendingAnswerId.content !== content) {
    pendingAnswerId = { id: genRequestId(), content }
  }
  await sendAnswerWithRetry(content, pendingAnswerId.id, 2)
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
    disposeVoice()
    session.value = null
    router.push({ name: 'history' })
  }, 3500)
}

// 从岗位广场 / 诊断结果 / 面试历史跳转时带入岗位与难度
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
  const d = route.query.difficulty
  if (d && ['easy', 'normal', 'hard'].includes(d)) {
    selectedDifficulty.value = d
  }
}

onUnmounted(() => {
  // 先标记卸载并中断 SSE 流，阻断后续回调创建新的定时器 / 语音播报
  isUnmounted = true
  pendingAnswerId = null // 离开页面后旧幂等键作废，避免跨会话复用
  if (sseController) {
    sseController.abort()
    sseController = null
  }
  disposeVoice()
  if (farewellTimer) {
    clearTimeout(farewellTimer)
    farewellTimer = null
  }
  for (const t of typeTimers) clearInterval(t)
  typeTimers = []
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
  // 会话中断恢复：从历史记录"继续面试"进入
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
  } catch {
    /* 拦截器已统一提示 */
  }
}
</script>

<style scoped>
.interview-page {
  max-width: 1080px;
  margin: 0 auto;
  padding: 24px 20px 40px;
}

@media (max-width: 900px) {
  .interview-page {
    padding: 16px 12px 32px;
  }
}
</style>
