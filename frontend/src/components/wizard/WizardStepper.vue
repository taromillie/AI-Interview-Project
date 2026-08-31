<template>
  <nav class="wizard" :aria-label="ariaLabel">
    <template v-for="(step, index) in steps" :key="step.id">
      <button
        type="button"
        class="w-step"
        :class="{ active: currentStep === step.id, done: maxStep > step.id }"
        :disabled="step.id > maxStep && step.id !== currentStep + 1"
        @click="$emit('step', step.id)"
      >
        <span class="w-dot">
          <el-icon v-if="maxStep > step.id" :size="14"><Check /></el-icon>
          <template v-else>{{ step.id }}</template>
        </span>
        <span class="w-label">{{ step.title }}</span>
      </button>
      <span v-if="index < steps.length - 1" class="w-line" :class="{ done: maxStep > step.id }"></span>
    </template>
  </nav>
</template>

<script setup>
defineProps({
  steps: { type: Array, required: true },
  currentStep: { type: Number, required: true },
  maxStep: { type: Number, required: true },
  ariaLabel: { type: String, default: '流程步骤' },
})
defineEmits(['step'])
</script>

<!--
  默认样式（非 scoped）：作为兜底，保证组件可独立复用。
  使用方若自带同名 scoped 样式，其特异性更高，会自然覆盖，互不干扰。
-->
<style>
.wizard {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 18px;
  padding: 16px 26px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
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
  transition: transform 160ms cubic-bezier(0.22, 1, 0.36, 1);
}
.w-step:active {
  transform: scale(0.96);
}
.w-step:disabled {
  cursor: default;
  opacity: 0.55;
}
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
  background: rgba(255, 255, 255, 0.06);
  border: 2px solid rgba(255, 255, 255, 0.12);
  transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}
.w-step.active .w-dot {
  color: #062a3a;
  background: var(--app-cyan);
  border-color: transparent;
  box-shadow: 0 0 0 5px rgba(90, 208, 230, 0.14), 0 6px 16px rgba(90, 208, 230, 0.28);
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
  color: var(--app-text);
}
.w-step.done .w-label {
  color: var(--app-text);
}
.w-line {
  width: 52px;
  height: 3px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.12);
  margin: 0 12px;
  transition: background 0.3s ease;
}
.w-line.done {
  background: linear-gradient(90deg, #10b981, #34d399);
}
</style>
