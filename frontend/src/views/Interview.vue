<template>
  <div class="interview-page">
    <!-- 会话设置 -->
    <el-card v-if="stage === 'setup'" class="setup-card">
      <template #header>
        <div class="setup-head">
          <span class="setup-title">开始一场模拟面试</span>
          <span class="setup-sub">面试官将基于你的简历与岗位要求进行多轮动态追问，结束后自动生成复盘报告</span>
        </div>
      </template>
      <el-form label-width="90px" class="setup-form">
        <el-form-item label="目标岗位">
          <el-select
            v-model="positionSel"
            filterable
            allow-create
            default-first-option
            clearable
            placeholder="从题库 / 我的 JD 选择，或直接输入自定义岗位"
            style="width: 100%"
          >
            <el-option-group label="我的 JD">
              <el-option
                v-for="jd in jds"
                :key="`jd-${jd.id}`"
                :label="jd.title || `JD #${jd.id}`"
                :value="`jd:${jd.title || `JD #${jd.id}`}`"
              />
            </el-option-group>
            <el-option-group label="题库岗位">
              <el-option v-for="p in positions" :key="p.id" :label="p.name" :value="`pos:${p.id}`" />
            </el-option-group>
          </el-select>
          <div class="form-tip">也可输入任意岗位名（自定义）</div>
        </el-form-item>
        <el-form-item label="使用简历">
          <el-select v-model="resumeId" clearable placeholder="可选，留空则不绑定简历" style="width: 100%">
            <el-option
              v-for="r in resumes"
              :key="r.id"
              :label="`简历 #${r.id}（${r.skills.length} 项技能）`"
              :value="r.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="面试轮数">
          <el-input-number v-model="maxRounds" :min="3" :max="20" />
          <span class="form-tip">含开场提问，达到轮数后自动结束</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" round :loading="starting" class="start-btn" @click="startInterview">
            开始面试
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 对话界面 -->
    <div v-else class="chat-shell">
      <header class="chat-header">
        <div class="chat-title">
          <span class="live-dot"></span>
          <span class="chat-title-text">模拟面试中</span>
          <span class="chat-rounds">共 {{ maxRounds }} 轮</span>
        </div>
        <el-button size="small" type="danger" plain round :disabled="busy || stage === 'ended'" @click="finishNow">
          结束面试
        </el-button>
      </header>

      <div ref="chatBox" class="chat-box">
        <div
          v-for="(m, i) in messages"
          :key="i"
          class="msg-row"
          :class="m.role === 'user' ? 'msg-user' : 'msg-assistant'"
        >
          <div class="msg-avatar">{{ m.role === 'user' ? '我' : '面' }}</div>
          <div class="bubble">
            <span v-if="m.role === 'assistant' && m.strategy" class="strategy-tag" :class="`tag-${m.strategy}`">
              {{ strategyText(m.strategy) }}
            </span>
            <div class="bubble-text">{{ m.content }}</div>
          </div>
        </div>
        <div v-if="status" class="status-line">
          <span class="dots"><i></i><i></i><i></i></span>
          <span>{{ status }}</span>
        </div>
      </div>

      <div class="input-area">
        <el-input
          v-model="input"
          type="textarea"
          :rows="2"
          resize="none"
          :disabled="busy || stage === 'ended'"
          placeholder="输入你的回答，回车发送（Shift+Enter 换行）"
          @keydown.enter.exact.prevent="send"
        />
        <el-button
          type="primary"
          round
          class="send-btn"
          :disabled="busy || stage === 'ended' || !input.trim()"
          :loading="busy"
          @click="send"
        >
          <el-icon v-if="!busy"><Promotion /></el-icon>
          <span v-if="!busy">发送</span>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Promotion } from '@element-plus/icons-vue'
import { answerInterview, createInterview, finishInterview, listInterviews, startInterview as startInterviewApi } from '@/api/interview'
import { listJds, listResumes } from '@/api/diagnostic'
import { listPositions } from '@/api/question'

const router = useRouter()

const stage = ref('setup')
const positions = ref([])
const resumes = ref([])
const jds = ref([])
const positionSel = ref('')
const resumeId = ref(null)
const maxRounds = ref(6)
const starting = ref(false)
const busy = ref(false)
const interviewId = ref(null)
const messages = ref([])
const input = ref('')
const status = ref('')
const chatBox = ref(null)

const STRATEGY_TEXT = {
  opening: '开场',
  deep_dive: '深入追问',
  probe: '澄清追问',
  remedy: '拉回正题',
  switch_topic: '切换话题',
  project_probe: '项目追问',
  farewell: '结束语',
  none: '提问',
}
function strategyText(s) {
  return STRATEGY_TEXT[s] || s
}

async function scrollBottom() {
  await nextTick()
  const box = chatBox.value
  if (box) box.scrollTo({ top: box.scrollHeight, behavior: 'smooth' })
}

// 面试官消息：reactive 包装确保响应式立即生效，收到即完整显示，无需等待用户输入
function pushAssistant(text, strategy) {
  const msg = reactive({ role: 'assistant', content: text, strategy: strategy || 'none', typing: false })
  messages.value.push(msg)
  scrollBottom()
}

async function loadOptions() {
  try {
    const [p, r, j] = await Promise.all([listPositions(), listResumes(), listJds()])
    positions.value = p.filter((x) => x.status === 'active')
    resumes.value = r
    jds.value = j
  } catch {
    /* 忽略，设置页允许留空 */
  }
}

// 解析目标岗位选择值：pos:12 → 题库；jd:xx / 其他 → 自定义岗位文本
function parsePosition(sel) {
  if (!sel) return { position_id: null, target_position: null }
  if (sel.startsWith('pos:')) {
    const id = Number(sel.slice(4))
    return { position_id: Number.isInteger(id) ? id : null, target_position: null }
  }
  let name = sel
  if (sel.startsWith('jd:')) name = sel.slice(3)
  return { position_id: null, target_position: name.trim() }
}

async function startInterview() {
  starting.value = true
  try {
    const { position_id, target_position } = parsePosition(positionSel.value)
    const iv = await createInterview({
      position_id,
      target_position,
      resume_id: resumeId.value || null,
      mode: 'text',
      max_rounds: maxRounds.value,
    })
    interviewId.value = iv.id
    stage.value = 'talking'
    await startInterviewApi(iv.id, {
      onEvent: handleEvent,
    })
  } catch (e) {
    ElMessage.error(e.message || '创建面试失败')
  } finally {
    starting.value = false
  }
}

function handleEvent(event, data) {
  if (event === 'preparing') {
    status.value = '面试官已就绪，正在出题…'
  } else if (event === 'thinking') {
    status.value = '面试官正在思考…'
  } else if (event === 'question') {
    status.value = ''
    pushAssistant(data.question, data.strategy)
  } else if (event === 'farewell') {
    status.value = '正在生成复盘报告，请稍候…'
    pushAssistant(data.message, 'farewell')
  } else if (event === 'finished') {
    status.value = ''
    ElMessage.success(data.message || '面试结束，报告已生成')
    stage.value = 'ended'
    setTimeout(() => router.push({ name: 'report', params: { id: data.report_id } }), 800)
  } else if (event === 'error') {
    status.value = ''
    ElMessage.error(data.message || '面试出现异常')
  }
}

async function send() {
  const content = input.value.trim()
  if (!content || busy.value) return
  input.value = ''
  messages.value.push({ role: 'user', content })
  scrollBottom()
  busy.value = true
  try {
    await answerInterview(interviewId.value, content, { onEvent: handleEvent })
  } catch (e) {
    status.value = ''
    ElMessage.error(e.message || '发送失败')
  } finally {
    busy.value = false
  }
}

async function finishNow() {
  busy.value = true
  status.value = '面试官正在收尾并生成报告…'
  try {
    const r = await finishInterview(interviewId.value)
    if (r.farewell) pushAssistant(r.farewell, 'farewell')
    ElMessage.success(r.message || '面试已结束')
    stage.value = 'ended'
    router.push({ name: 'report', params: { id: r.report_id } })
  } catch (e) {
    ElMessage.error(e.message || '结束失败')
  } finally {
    busy.value = false
    status.value = ''
  }
}

onMounted(() => {
  loadOptions()
  // 若有进行中的面试直接进入对话（恢复最近一场）
  listInterviews()
    .then((list) => {
      const ongoing = list.find((i) => ['created', 'asking'].includes(i.status))
      if (ongoing) {
        interviewId.value = ongoing.id
        maxRounds.value = ongoing.max_rounds
        stage.value = 'talking'
        ElMessage.info('已恢复上一场未完成的面试')
      }
    })
    .catch(() => {})
})
</script>

<style scoped>
.interview-page {
  max-width: 880px;
  margin: 0 auto;
  height: calc(100vh - 140px);
  display: flex;
  flex-direction: column;
}

/* ---------- 设置页 ---------- */
.setup-card {
  margin: 12px 0;
  border: none;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06), 0 8px 30px rgba(15, 23, 42, 0.06);
}
.setup-card :deep(.el-card__header) {
  padding: 22px 24px 0;
  border: none;
}
.setup-head {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.setup-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: 0.2px;
}
.setup-sub {
  font-size: 13px;
  color: #64748b;
}
.setup-card :deep(.el-card__body) {
  padding: 20px 24px 28px;
}
.setup-form {
  max-width: 560px;
  margin-top: 8px;
}
.form-tip {
  margin-left: 12px;
  color: #94a3b8;
  font-size: 12px;
}
.start-btn {
  min-width: 140px;
  margin-top: 6px;
  font-weight: 600;
}

/* ---------- 对话页 ---------- */
.chat-shell {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06), 0 8px 30px rgba(15, 23, 42, 0.06);
  overflow: hidden;
}
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 22px;
  border-bottom: 1px solid #eef2f7;
  background: linear-gradient(180deg, #fbfcfe 0%, #fff 100%);
}
.chat-title {
  display: flex;
  align-items: center;
  gap: 10px;
}
.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #059669;
  box-shadow: 0 0 0 0 rgba(5, 150, 105, 0.5);
  animation: livePulse 1.8s infinite;
}
@keyframes livePulse {
  70% {
    box-shadow: 0 0 0 7px rgba(5, 150, 105, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(5, 150, 105, 0);
  }
}
.chat-title-text {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}
.chat-rounds {
  font-size: 12px;
  color: #94a3b8;
  background: #f1f5f9;
  padding: 2px 10px;
  border-radius: 999px;
}

.chat-box {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 22px 22px 8px;
  background: linear-gradient(180deg, #f8fafc 0%, #fdfefe 30%, #ffffff 100%);
  scroll-behavior: smooth;
}
.chat-box::-webkit-scrollbar {
  width: 6px;
}
.chat-box::-webkit-scrollbar-thumb {
  background: #dbe3ee;
  border-radius: 3px;
}

/* 消息 */
.msg-row {
  display: flex;
  gap: 10px;
  margin-bottom: 18px;
  animation: fadeSlide 0.3s ease both;
}
@keyframes fadeSlide {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.msg-user {
  flex-direction: row-reverse;
}
.msg-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  margin-top: 2px;
}
.msg-assistant .msg-avatar {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  box-shadow: 0 2px 6px rgba(99, 102, 241, 0.35);
}
.msg-user .msg-avatar {
  background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
  box-shadow: 0 2px 6px rgba(37, 99, 235, 0.35);
}

.bubble {
  max-width: 76%;
  padding: 12px 16px;
  border-radius: 14px;
  line-height: 1.7;
  font-size: 14px;
  color: #1e293b;
}
.msg-assistant .bubble {
  background: #fff;
  border: 1px solid #e4ecfc;
  border-top-left-radius: 4px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.msg-user .bubble {
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
  color: #fff;
  border-top-right-radius: 4px;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
}
.bubble-text {
  white-space: pre-wrap;
  word-break: break-word;
}

/* 追问策略标签 */
.strategy-tag {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 1px 8px;
  border-radius: 999px;
  margin-bottom: 8px;
  letter-spacing: 0.3px;
}
.tag-opening {
  color: #059669;
  background: #ecfdf5;
}
.tag-deep_dive,
.tag-project_probe {
  color: #7c3aed;
  background: #f3e8ff;
}
.tag-probe {
  color: #2563eb;
  background: #eff6ff;
}
.tag-remedy {
  color: #d97706;
  background: #fffbeb;
}
.tag-switch_topic {
  color: #0891b2;
  background: #ecfeff;
}
.tag-farewell {
  color: #b45309;
  background: #fef3c7;
}
.tag-none {
  color: #64748b;
  background: #f1f5f9;
}

/* 状态行：三点脉冲 */
.status-line {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #64748b;
  font-size: 13px;
  padding: 6px 4px 14px;
}
.dots {
  display: inline-flex;
  gap: 4px;
  padding: 6px 10px;
  background: #fff;
  border: 1px solid #e4ecfc;
  border-radius: 999px;
}
.dots i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #6366f1;
  animation: dotPulse 1.2s ease-in-out infinite;
}
.dots i:nth-child(2) {
  animation-delay: 0.15s;
}
.dots i:nth-child(3) {
  animation-delay: 0.3s;
}
@keyframes dotPulse {
  0%,
  60%,
  100% {
    transform: scale(0.6);
    opacity: 0.45;
  }
  30% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 输入区 */
.input-area {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  padding: 14px 22px 18px;
  border-top: 1px solid #eef2f7;
  background: #fff;
}
.input-area .el-input {
  flex: 1;
}
.input-area :deep(.el-textarea__inner) {
  border-radius: 12px;
  border-color: #e2e8f0;
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.6;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.input-area :deep(.el-textarea__inner:focus) {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}
.send-btn {
  min-width: 96px;
  height: 44px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
}
</style>
