import { computed, ref } from 'vue'

/**
 * 向导步骤状态机（多页向导复用，取代各页重复的 currentStep/maxStep/goNext/goPrev/goStep）。
 *
 * @param {number} initialStep 初始步骤（默认 1）
 * @param {number} totalSteps 总步骤数（默认 3）
 *
 * @returns {{
 *   currentStep: import('vue').Ref<number>,
 *   maxStep: import('vue').Ref<number>,
 *   isFirst: import('vue').ComputedRef<boolean>,
 *   isLast: import('vue').ComputedRef<boolean>,
 *   goNext: () => void,
 *   goPrev: () => void,
 *   goStep: (n: number) => void,
 * }}
 */
export function useWizard(initialStep = 1, totalSteps = 3) {
  const currentStep = ref(initialStep)
  const maxStep = ref(initialStep)

  const isFirst = computed(() => currentStep.value <= 1)
  const isLast = computed(() => currentStep.value >= totalSteps)

  function goNext() {
    if (currentStep.value < totalSteps) {
      currentStep.value += 1
      if (currentStep.value > maxStep.value) maxStep.value = currentStep.value
    }
  }

  function goPrev() {
    if (currentStep.value > 1) currentStep.value -= 1
  }

  /** 点击步骤条：只允许跳到已解锁步骤或下一步 */
  function goStep(n) {
    if (n < 1 || n > totalSteps) return
    if (n === currentStep.value) return
    if (n <= maxStep.value || n === currentStep.value + 1) {
      currentStep.value = n
      if (n > maxStep.value) maxStep.value = n
    }
  }

  return { currentStep, maxStep, isFirst, isLast, goNext, goPrev, goStep }
}
