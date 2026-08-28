<template>
  <section class="wizard-card" :class="`wizard-card--${size}`">
    <header v-if="title || $slots.header" class="wizard-card__header">
      <slot name="header"><h2>{{ title }}</h2></slot>
    </header>
    <div class="wizard-card__body"><slot /></div>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  size: { type: String, default: 'normal' },
})
</script>

<style scoped>
.wizard-card { border-radius: 16px; }
.wizard-card__header { display: flex; align-items: center; justify-content: space-between; }
.wizard-card__body { min-width: 0; }
</style>
