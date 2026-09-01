<template>
  <section class="w-card">
    <div class="w-head">
      <span class="w-ico grad"><el-icon :size="20"><Setting /></el-icon></span>
      <div>
        <div class="w-title">设置面试参数</div>
        <div class="w-desc">回答方式与难度影响整体体验，可随时开始</div>
      </div>
    </div>

    <el-form label-position="top">
      <el-form-item label="难度">
        <div class="difficulty-grid">
          <button
            v-for="d in difficulties"
            :key="d.value"
            class="diff-card"
            :class="{ on: selectedDifficulty === d.value }"
            @click="$emit('update:selectedDifficulty', d.value)"
          >
            <div class="diff-name">{{ d.label }}</div>
            <div class="diff-desc">{{ d.desc }}</div>
          </button>
        </div>
      </el-form-item>

      <el-form-item label="面试轮数">
        <div class="rounds-form">
          <el-input-number v-model="maxRounds" :min="3" :max="8" :step="1" />
          <span class="rounds-note">AI 提问 {{ maxRounds }} 轮后自动生成评估报告</span>
        </div>
      </el-form-item>

      <el-form-item label="回答方式">
        <el-radio-group v-model="answerMode" class="mode-group">
          <el-radio-button value="text">文字</el-radio-button>
          <el-radio-button value="voice" :disabled="!micSupported">语音（AI 读题）</el-radio-button>
          <el-radio-button value="video" :disabled="!micSupported">语音+视频模式</el-radio-button>
        </el-radio-group>
        <div class="mode-hint">{{ answerModeHint }}</div>
      </el-form-item>
    </el-form>

    <div class="start-summary">
      <div class="sum-item">
        <span class="sum-label">岗位</span>
        <span class="sum-value">{{ positionLabel }}</span>
      </div>
      <div class="sum-item">
        <span class="sum-label">面试官</span>
        <span class="sum-value">{{ interviewerLabel }}</span>
      </div>
      <div class="sum-item">
        <span class="sum-label">难度</span>
        <span class="sum-value">{{ difficultyLabel }}</span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { Setting } from '@element-plus/icons-vue'

const props = defineProps({
  difficulties: { type: Array, default: () => [] },
  selectedDifficulty: { type: String, default: 'mid' },
  maxRounds: { type: Number, default: 5 },
  answerModes: { type: Array, default: () => [] },
  answerMode: { type: String, default: 'text' },
  micSupported: { type: Boolean, default: false },
  answerModeHint: { type: String, default: '' },
  positionLabel: { type: String, default: '' },
  interviewerLabel: { type: String, default: '' },
  difficultyLabel: { type: String, default: '' },
})
const emit = defineEmits(['update:selectedDifficulty', 'update:maxRounds', 'update:answerMode'])

const maxRounds = computed({
  get: () => props.maxRounds,
  set: (v) => emit('update:maxRounds', v),
})
const answerMode = computed({
  get: () => props.answerMode,
  set: (v) => emit('update:answerMode', v),
})
</script>

<style scoped>
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
  box-shadow: 0 6px 14px rgba(16, 185, 129, 0.28);
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
.difficulty-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  width: 100%;
}
.diff-card {
  background: #fff;
  border: 1.5px solid #e4e9f2;
  border-radius: 12px;
  padding: 10px 12px;
  text-align: left;
  cursor: pointer;
  transition: all 0.22s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.diff-card:hover {
  border-color: rgba(16, 185, 129, 0.5);
}
.diff-card.on {
  border-color: #333333;
  background: rgba(26, 26, 26, 0.05);
  box-shadow: 0 0 0 4px rgba(26, 26, 26, 0.1);
}
.diff-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--app-text);
}
.diff-desc {
  font-size: 11px;
  color: var(--app-text-muted);
  margin-top: 2px;
}
.rounds-form {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}
.rounds-note {
  font-size: 12px;
  color: var(--app-text-muted);
}
.mode-group { margin-bottom: 4px; }
.mode-hint {
  font-size: 12px;
  color: var(--app-text-muted);
  line-height: 1.6;
}
.start-summary {
  margin-top: 18px;
  border-radius: 12px;
  background: rgba(26, 26, 26, 0.05);
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.sum-item {
  display: flex;
  align-items: baseline;
  gap: 10px;
  font-size: 13px;
}
.sum-label {
  flex-shrink: 0;
  color: var(--app-text-muted);
}
.sum-value {
  color: var(--app-text);
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 深色液态玻璃覆盖（项目为强制深色主题，无需跟随系统配色） */
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
  background: linear-gradient(135deg, #34d399, #2dd4bf);
  box-shadow: 0 6px 14px -4px rgba(52, 211, 153, 0.5);
}
.diff-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1.5px solid var(--app-border);
}
.diff-card:hover {
  border-color: rgba(52, 211, 153, 0.5);
}
.diff-card.on {
  border-color: var(--app-emerald);
  background: var(--app-emerald-soft);
  box-shadow: 0 0 0 4px rgba(52, 211, 153, 0.14);
}
.start-summary {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
}
</style>
