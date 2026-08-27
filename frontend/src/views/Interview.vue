<template>
  <div class="interview-page">
    <!-- 会话设置 -->
    <el-card v-if="stage === 'setup'" class="setup-card">
      <template #header>开始一场模拟面试</template>
      <el-alert
        title="面试官将基于你的简历与岗位要求进行多轮动态追问（SSE 流式对话）。结束后自动生成复盘报告。"
        type="info"
        :closable="false"
        class="tip"
      />
      <el-form label-width="100px" class="setup-form">
        <el-form-item label="目标岗位">
          <el-select v-model="positionId" clearable placeholder="可选，留空使用通用题库" style="width: 100%">
            <el-option v-for="p in positions" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
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
          <el-button type="primary" :loading="starting" @click="startInterview">
            开始面试
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 对话界面 -->
    <el-card v-else class="chat-card">
      <template #header>
        <div class="chat-header">
          <span>模拟面试中（{{ maxRounds }} 轮）</span>
          <el-button size="small" type="danger" plain :disabled="busy || stage === 'ended'" @click="finishNow">
            结束面试
          </el-button>
        </div>
      </template>

      <div ref="chatBox" class="chat-box">
        <div
          v-for="(m, i) in messages"
          :key="i"
          class="msg-row"
          :class="m.role === 'user' ? 'msg-user' : 'msg-assistant'"
        >
          <el-avatar :size="32" class="msg-avatar">
            {{ m.role === 'user' ? '我' : 'AI' }}
          </el-avatar>
          <div class="bubble">
            <div v-if="m.role === 'assistant' && m.strategy" class="strategy-tag">
              <el-tag size="small" effect="plain">{{ strategyText(m.strategy) }}</el-tag>
            </div>
            <div class="bubble-text">
              {{ m.content }}<span v-if="m.typing" class="cursor">▌</span>
            </div>
          </div>
        </div>
        <div v-if="status" class="status-line">
          <el-icon class="is-loading"><Loading /></el-icon>
          {{ status }}
        </div>
      </div>

      <div class="input-row">
        <el-input
          v-model="input"
          type="textarea"
          :rows="2"
          :disabled="busy || stage === 'ended'"
          placeholder="输入你的回答，回车发送（Shift+Enter 换行）"
          @keydown.enter.exact.prevent="send"
        />
        <el-button
          type="primary"
          :disabled="busy || stage === 'ended' || !input.trim()"
          :loading="busy"
          @click="send"
        >
          发送
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { answerInterview, createInterview, finishInterview, listInterviews, startInterview as startInterviewApi } from '@/api/interview'
import { listResumes } from '@/api/diagnostic'
import { listPositions } from '@/api/question'

const router = useRouter()

const stage = ref('setup')
const positions = ref([])
const resumes = ref([])
const positionId = ref(null)
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
  none: '提问',
}
function strategyText(s) {
  return STRATEGY_TEXT[s] || s
}

async function scrollBottom() {
  await nextTick()
  chatBox.value?.scrollTo({ top: chatBox.value.scrollHeight, behavior: 'smooth' })
}

function pushAssistant(text, strategy) {
  const msg = { role: 'assistant', content: '', strategy: strategy || 'none', typing: true }
  messages.value.push(msg)
  const idx = messages.value.length - 1
  let i = 0
  const timer = setInterval(() => {
    i += 2
    msg.content = text.slice(0, i)
    if (i >= text.length) {
      clearInterval(timer)
      msg.typing = false
      scrollBottom()
    }
  }, 16)
  scrollBottom()
}

async function loadOptions() {
  try {
    const [p, r] = await Promise.all([listPositions(), listResumes()])
    positions.value = p.filter((x) => x.status === 'active')
    resumes.value = r
  } catch {
    /* 忽略，设置页允许留空 */
  }
}

async function startInterview() {
  starting.value = true
  try {
    const iv = await createInterview({
      position_id: positionId.value || null,
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
.setup-card {
  max-width: 640px;
  margin: 0 auto;
}
.tip {
  margin-bottom: 18px;
}
.setup-form {
  max-width: 520px;
}
.form-tip {
  margin-left: 12px;
  color: #909399;
  font-size: 12px;
}
.chat-card {
  height: calc(100vh - 140px);
  display: flex;
  flex-direction: column;
}
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.chat-box {
  flex: 1;
  overflow-y: auto;
  padding: 8px 4px;
}
.msg-row {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}
.msg-user {
  flex-direction: row-reverse;
}
.msg-avatar {
  background: #409eff;
  flex-shrink: 0;
}
.msg-user .msg-avatar {
  background: #67c23a;
}
.bubble {
  max-width: 72%;
  padding: 10px 14px;
  border-radius: 10px;
  background: #f4f4f5;
  line-height: 1.6;
}
.msg-user .bubble {
  background: #ecf5ff;
}
.strategy-tag {
  margin-bottom: 6px;
}
.bubble-text {
  white-space: pre-wrap;
  word-break: break-word;
}
.cursor {
  animation: blink 1s step-start infinite;
}
@keyframes blink {
  50% {
    opacity: 0;
  }
}
.status-line {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #909399;
  padding: 4px 8px;
}
.input-row {
  display: flex;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}
.input-row .el-input {
  flex: 1;
}
</style>
