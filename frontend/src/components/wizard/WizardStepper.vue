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
