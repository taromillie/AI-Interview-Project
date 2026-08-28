<template>
  <footer class="wizard-nav">
    <el-button v-if="showPrev" @click="$emit('prev')">{{ prevText }}</el-button>
    <span class="wizard-nav__spacer" />
    <el-button v-if="showNext" type="primary" :disabled="nextDisabled" @click="$emit('next')">{{ nextText }}</el-button>
  </footer>
</template>

<script setup>
defineProps({
  showPrev: { type: Boolean, default: true },
  showNext: { type: Boolean, default: true },
  nextDisabled: { type: Boolean, default: false },
  prevText: { type: String, default: '上一步' },
  nextText: { type: String, default: '下一步' },
})
defineEmits(['prev', 'next'])
</script>

<style scoped>
.wizard-nav { display: flex; align-items: center; gap: 12px; margin-top: 24px; }
.wizard-nav__spacer { flex: 1; }
</style>
