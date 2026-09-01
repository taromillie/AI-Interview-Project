<template>
  <div>
    <div class="page-head">
      <h1 class="page-title">模拟面试</h1>
      <p class="page-sub">选好岗位与面试官，开始一场贴近真实的 AI 面试</p>
    </div>

    <div class="w-body">
      <WizardStepper :steps="wizardSteps" :current-step="currentStep" :max-step="maxStep" @step="goStep" />

      <transition name="wizard" mode="out-in">
        <StepPosition
          v-if="currentStep === 1"
          key="step1"
          :positions="positions"
          v-model:position-mode="positionMode"
          v-model:selected-position-id="selectedPositionId"
          v-model:custom-position="customPosition"
          :resumes="resumes"
          v-model:selected-resume-id="selectedResumeId"
          @next="goNext"
        />
        <StepInterviewer
          v-else-if="currentStep === 2"
          key="step2"
          :interviewers="interviewers"
          v-model:selected-interviewer-id="selectedInterviewerId"
        />
        <StepSettings
          v-else
          key="step3"
          :difficulties="difficulties"
          v-model:selected-difficulty="selectedDifficulty"
          v-model:max-rounds="maxRounds"
          :answer-modes="answerModes"
          v-model:answer-mode="answerMode"
          :mic-supported="micSupported"
          :answer-mode-hint="answerModeHint"
          :position-label="positionLabel"
          :interviewer-label="interviewerLabel"
          :difficulty-label="difficultyLabel"
        />
      </transition>

      <div class="w-nav">
        <el-button v-if="currentStep > 1" @click="goPrev">返回</el-button>
        <div v-else class="nav-spacer" />
        <div class="nav-hint">
          <template v-if="currentStep === 1">{{ positionLabel || '请选择目标岗位' }}</template>
          <template v-else-if="currentStep === 2">{{ interviewerLabel }}</template>
          <template v-else>确认无误即可开始</template>
        </div>
        <el-button
          v-if="currentStep < maxStep"
          type="primary"
          :disabled="!canNext"
          @click="goNext"
        >下一步</el-button>
        <el-button
          v-else
          type="primary"
          :disabled="!canNext || creating"
          :loading="creating"
          @click="$emit('create')"
        >开始面试</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import WizardStepper from '@/components/wizard/WizardStepper.vue'
import StepPosition from './StepPosition.vue'
import StepInterviewer from './StepInterviewer.vue'
import StepSettings from './StepSettings.vue'

const props = defineProps({
  positions: { type: Array, default: () => [] },
  resumes: { type: Array, default: () => [] },
  interviewers: { type: Array, default: () => [] },
  positionMode: { type: String, default: 'preset' },
  selectedPositionId: { type: [Number, String], default: null },
  customPosition: { type: String, default: '' },
  selectedResumeId: { type: [Number, String], default: null },
  selectedInterviewerId: { type: [Number, String], default: null },
  selectedDifficulty: { type: String, default: 'mid' },
  maxRounds: { type: Number, default: 5 },
  answerMode: { type: String, default: 'text' },
  micSupported: { type: Boolean, default: false },
  creating: { type: Boolean, default: false },
})
const emit = defineEmits([
  'update:positionMode',
  'update:selectedPositionId',
  'update:customPosition',
  'update:selectedResumeId',
  'update:selectedInterviewerId',
  'update:selectedDifficulty',
  'update:maxRounds',
  'update:answerMode',
  'create',
])

const positionMode = computed({
  get: () => props.positionMode,
  set: (v) => emit('update:positionMode', v),
})
const selectedPositionId = computed({
  get: () => props.selectedPositionId,
  set: (v) => emit('update:selectedPositionId', v),
})
const customPosition = computed({
  get: () => props.customPosition,
  set: (v) => emit('update:customPosition', v),
})
const selectedResumeId = computed({
  get: () => props.selectedResumeId,
  set: (v) => emit('update:selectedResumeId', v),
})
const selectedInterviewerId = computed({
  get: () => props.selectedInterviewerId,
  set: (v) => emit('update:selectedInterviewerId', v),
})
const selectedDifficulty = computed({
  get: () => props.selectedDifficulty,
  set: (v) => emit('update:selectedDifficulty', v),
})
const maxRounds = computed({
  get: () => props.maxRounds,
  set: (v) => emit('update:maxRounds', v),
})
const answerMode = computed({
  get: () => props.answerMode,
  set: (v) => emit('update:answerMode', v),
})

const wizardSteps = [
  { id: 1, title: '目标岗位' },
  { id: 2, title: '面试官' },
  { id: 3, title: '难度' },
]
const currentStep = ref(1)
const maxStep = 3

const difficulties = [
  { value: 'easy', label: '简单', desc: '基础概念为主' },
  { value: 'mid', label: '中等', desc: '结合项目实践' },
  { value: 'hard', label: '困难', desc: '高压深入追问' },
]
const answerModes = [
  { value: 'text', label: '文字' },
  { value: 'voice', label: '语音（AI 读题）' },
  { value: 'video', label: '语音+视频模式' },
]

const positionLabel = computed(() => {
  if (positionMode.value === 'custom') return customPosition.value || '未设置'
  const p = props.positions.find((x) => x.id === selectedPositionId.value)
  return p ? (p.company ? `${p.company} ${p.name}` : p.name) : ''
})
const interviewerLabel = computed(() => {
  const iv = props.interviewers.find((x) => x.id === selectedInterviewerId.value)
  return iv ? iv.name : ''
})
const difficultyLabel = computed(
  () => difficulties.find((d) => d.value === selectedDifficulty.value)?.label || '',
)
const answerModeHint = computed(() => {
  if (answerMode.value === 'text') return '适合不方便开麦的环境，建议电脑端使用'
  if (answerMode.value === 'voice') return 'AI 朗读题目，你直接开口回答，浏览器会识别为文字'
  return '开启摄像头进行画面活动监测，模拟真实线上面试'
})
const canNext = computed(() => {
  if (currentStep.value === 1) return Boolean(positionLabel.value)
  if (currentStep.value === 2) return Boolean(interviewerLabel.value)
  return true
})

function goStep(n) {
  if (n <= currentStep.value) currentStep.value = n
}
function goNext() {
  if (currentStep.value < maxStep && canNext.value) currentStep.value += 1
}
function goPrev() {
  if (currentStep.value > 1) currentStep.value -= 1
}
</script>

<style scoped>
.page-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 18px;
  padding: 0 4px;
}
.page-title {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.01em;
  background: var(--app-text);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.page-sub {
  font-size: 13px;
  color: var(--app-text-muted);
}
.w-body {
  max-width: 760px;
  margin: 0 auto;
}
.w-nav {
  margin-top: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.nav-spacer {
  flex: 1;
}
.nav-hint {
  flex: 1;
  text-align: center;
  font-size: 13px;
  color: var(--app-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 0 8px;
}

.wizard-enter-active,
.wizard-leave-active {
  transition: opacity 0.25s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1)), transform 0.25s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.wizard-enter-from {
  opacity: 0;
  transform: translateX(14px);
}
.wizard-leave-to {
  opacity: 0;
  transform: translateX(-14px);
}

@media (max-width: 640px) {
  .page-head {
    flex-direction: column;
    gap: 4px;
  }
  .nav-hint {
    display: none;
  }
}
</style>
