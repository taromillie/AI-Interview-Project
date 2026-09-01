<template>
  <div class="chat-shell">
    <div class="chat-head">
      <div class="chat-meta">
        <div class="chat-title">{{ sessionPositionLabel }}</div>
        <div class="chat-sub">
          <span>{{ interviewerLabel || 'AI 面试官' }}</span>
          <span class="chat-dot">·</span>
          <span>{{ difficultyLabel }}</span>
          <span class="chat-dot">·</span>
          <span>第 {{ aiCount }}/{{ maxRounds }} 轮</span>
        </div>
      </div>
      <div class="chat-tools">
        <button
          class="tool-btn"
          :class="{ on: voiceEnabled }"
          :title="voiceEnabled ? '关闭语音播报' : '开启语音播报'"
          @click="$emit('toggle-voice')"
        >
          <el-icon :size="16"><Bell v-if="voiceEnabled" /><BellFilled v-else /></el-icon>
        </button>
        <button
          v-if="answerMode === 'video'"
          class="tool-btn"
          :class="{ on: camEnabled }"
          :title="camEnabled ? '关闭摄像头' : '开启摄像头'"
          @click="$emit('toggle-camera')"
        >
          <el-icon :size="16"><VideoCamera /></el-icon>
        </button>
        <el-button size="small" :loading="ending" @click="$emit('end-early')">结束面试</el-button>
      </div>
    </div>

    <div class="chat-main">
      <div ref="chatBody" class="chat-body">
        <div v-if="connError" class="conn-banner">
          <el-icon :size="14"><Warning /></el-icon>
          <span class="conn-text">{{ connError }}</span>
          <button v-if="connAction" class="conn-retry" @click="connAction()">重试</button>
        </div>
        <template v-for="(m, i) in messages" :key="i">
          <div
            v-if="m.role === 'ai'"
            class="msg ai"
            :class="{ typing: m.typing }"
            @click="m.typing && $emit('skip-typing', m)"
          >
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
      <CameraPanel
        v-if="answerMode === 'video'"
        :cam-enabled="camEnabled"
        :cam-error="camError"
        :cam-active="camActive"
        @video-el="$emit('video-el', $event)"
      />
    </div>

    <div class="chat-input">
      <button
        v-if="micSupported"
        class="mic-btn"
        :class="{ on: recording }"
        :disabled="!waitingAnswer"
        :title="recording ? '停止语音输入' : '语音输入回答'"
        @click="$emit('toggle-recording')"
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
        @input="$emit('draft-typed')"
        @keydown="$emit('answer-keydown', $event)"
      />
      <button
        class="send-btn"
        :disabled="!waitingAnswer || !answerDraft.trim()"
        @click="$emit('send-answer')"
      >
        <el-icon :size="18"><Promotion /></el-icon>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { Bell, BellFilled, Microphone, Promotion, VideoCamera, Warning } from '@element-plus/icons-vue'
import CameraPanel from './CameraPanel.vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  chatLoading: { type: Boolean, default: false },
  connError: { type: String, default: '' },
  connAction: { type: Function, default: null },
  sessionPositionLabel: { type: String, default: '' },
  interviewerLabel: { type: String, default: '' },
  difficultyLabel: { type: String, default: '' },
  maxRounds: { type: Number, default: 5 },
  voiceEnabled: { type: Boolean, default: true },
  answerMode: { type: String, default: 'text' },
  camEnabled: { type: Boolean, default: false },
  camError: { type: String, default: '' },
  camActive: { type: Boolean, default: true },
  micSupported: { type: Boolean, default: false },
  recording: { type: Boolean, default: false },
  waitingAnswer: { type: Boolean, default: false },
  answerDraft: { type: String, default: '' },
  ending: { type: Boolean, default: false },
})
const emit = defineEmits([
  'update:answerDraft',
  'toggle-voice',
  'toggle-camera',
  'toggle-recording',
  'end-early',
  'skip-typing',
  'draft-typed',
  'answer-keydown',
  'send-answer',
  'video-el',
])

const answerDraft = computed({
  get: () => props.answerDraft,
  set: (v) => emit('update:answerDraft', v),
})
const aiCount = computed(() => props.messages.filter((m) => m.role === 'ai').length)

const chatBody = ref(null)
function scrollToBottom() {
  nextTick(() => {
    if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
  })
}
// 打字机逐字更新 / 等待状态 / 录音状态变化时保持滚动到底部
watch(
  () => props.messages.map((m) => m.shown).join('|'),
  () => scrollToBottom(),
)
watch(
  () => [props.waitingAnswer, props.chatLoading, props.recording],
  () => scrollToBottom(),
)
</script>

<style scoped>
.chat-shell {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 64px);
  max-width: 860px;
  margin: 0 auto;
}
.chat-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 4px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.6);
}
.chat-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--app-text);
}
.chat-sub {
  margin-top: 3px;
  font-size: 12px;
  color: var(--app-text-muted);
  display: flex;
  align-items: center;
  gap: 4px;
}
.chat-dot {
  opacity: 0.5;
}
.chat-tools {
  display: flex;
  align-items: center;
  gap: 8px;
}
.tool-btn {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  border: 1px solid #e4e9f2;
  background: #fff;
  color: var(--app-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.tool-btn:hover {
  border-color: rgba(26, 26, 26, 0.4);
}
.tool-btn.on {
  color: #fff;
  background: linear-gradient(135deg, #1a1a1a, #1a1a1a);
  border-color: transparent;
}
.chat-main {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 16px;
  padding: 16px 4px;
}
.chat-body {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 4px 2px 12px;
}
.conn-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(245, 158, 11, 0.1);
  color: #b45309;
  font-size: 13px;
}
.conn-retry {
  border: none;
  background: none;
  color: inherit;
  font-weight: 600;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 6px;
}
.conn-retry:hover {
  background: rgba(245, 158, 11, 0.15);
}
.msg {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  max-width: 82%;
}
.msg.ai {
  align-self: flex-start;
}
.msg.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}
.msg-avatar {
  width: 34px;
  height: 34px;
  border-radius: 11px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
}
.ai-avatar {
  color: #fff;
  background: linear-gradient(135deg, #1a1a1a, #333333);
}
.msg.user .msg-avatar {
  color: #071018;
  background: linear-gradient(135deg, #5ad0e6, #79e2c8);
}
.msg-bubble {
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}
.ai-bubble {
  background: #f3f4f6;
  color: var(--app-text);
  border-top-left-radius: 4px;
  cursor: pointer;
}
.user-bubble {
  background: linear-gradient(135deg, #1a1a1a, #1a1a1a);
  color: #fff;
  border-top-right-radius: 4px;
}
.msg.typing .ai-bubble {
  cursor: pointer;
}
.typing-caret {
  display: inline-block;
  width: 2px;
  height: 14px;
  background: currentColor;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: caret-blink 0.8s steps(2) infinite;
}
@keyframes caret-blink {
  0%,
  50% {
    opacity: 1;
  }
  51%,
  100% {
    opacity: 0;
  }
}
.thinking {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-width: 56px;
}
.tdot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--app-text-muted);
  animation: tdot 1.2s infinite ease-in-out;
}
.tdot:nth-child(2) {
  animation-delay: 0.2s;
}
.tdot:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes tdot {
  0%,
  80%,
  100% {
    opacity: 0.25;
    transform: scale(0.9);
  }
  40% {
    opacity: 1;
    transform: scale(1.1);
  }
}
.chat-input {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 10px 0 18px;
}
.mic-btn {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  border: 1px solid #e4e9f2;
  background: #fff;
  color: var(--app-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.mic-btn:hover:not(:disabled) {
  border-color: rgba(26, 26, 26, 0.4);
}
.mic-btn.on {
  color: #fff;
  background: #ef4444;
  border-color: transparent;
  animation: mic-pulse 1.4s ease-in-out infinite;
}
.mic-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
@keyframes mic-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.45);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(239, 68, 68, 0);
  }
}
.chat-input :deep(.el-textarea__inner) {
  border-radius: 12px;
  background: #fff;
  box-shadow: var(--app-shadow-sm, 0 1px 3px rgba(20, 20, 20, 0.06));
  transition: border-color 0.2s;
}
.chat-input :deep(.el-textarea__inner:focus) {
  border-color: rgba(26, 26, 26, 0.5);
}
.send-btn {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  border: none;
  color: #fff;
  background: linear-gradient(135deg, #1a1a1a, #1a1a1a);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px -6px rgba(26, 26, 26, 0.6);
}
.send-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* 深色液态玻璃覆盖（项目为强制深色主题，无需跟随系统配色） */
.chat-head {
  border-bottom-color: var(--glass-border);
}
.tool-btn {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--app-border);
}
.tool-btn.on {
  color: #071018;
  background: var(--app-brand-gradient);
  border-color: transparent;
}
.ai-bubble {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
}
.user-bubble {
  color: #071018;
  background: linear-gradient(135deg, #5ad0e6, #79e2c8);
}
.ai-avatar {
  background: linear-gradient(135deg, #6b8bff, #8b6bff);
}
.mic-btn {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--app-border);
}
.chat-input :deep(.el-textarea__inner) {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--app-border);
  box-shadow: none;
}
.send-btn {
  color: #071018;
  background: var(--app-brand-gradient);
}
</style>
