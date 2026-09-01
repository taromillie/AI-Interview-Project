<template>
  <section class="w-card">
    <div class="w-head">
      <span class="w-ico grad"><el-icon :size="20"><User /></el-icon></span>
      <div>
        <div class="w-title">选择面试官</div>
        <div class="w-desc">不同角色的人设与提问风格会注入本次面试</div>
      </div>
    </div>

    <div v-if="!interviewers.length" class="loading-text">正在加载面试官角色…</div>
    <div v-else class="interviewer-grid">
      <button
        v-for="iv in interviewers"
        :key="iv.id"
        class="iv-card"
        :class="{ on: selectedInterviewerId === iv.id }"
        @click="$emit('update:selectedInterviewerId', iv.id)"
      >
        <div class="iv-top">
          <div class="iv-avatar">{{ iv.name.slice(0, 1) }}</div>
          <div class="iv-info">
            <div class="iv-name">{{ iv.name }}</div>
            <div class="iv-title">{{ iv.title || '面试官' }}</div>
          </div>
          <el-icon v-if="selectedInterviewerId === iv.id" class="iv-check"><Check /></el-icon>
        </div>
        <div class="iv-persona">{{ iv.persona || '专业、严谨，关注你的真实能力。' }}</div>
        <div class="iv-tags">
          <span class="iv-tag">{{ typeText(iv) }}</span>
          <span class="iv-tag">{{ biasText(iv.difficulty_bias) }}</span>
        </div>
      </button>
    </div>
  </section>
</template>

<script setup>
import { Check, User } from '@element-plus/icons-vue'

defineProps({
  interviewers: { type: Array, default: () => [] },
  selectedInterviewerId: { type: [Number, String], default: null },
})
defineEmits(['update:selectedInterviewerId'])

function typeText(iv) {
  // 内置面试官按名称显示精确标签（后端按名称命中专属模式）
  const byName = {
    资深技术面试官: '技术面',
    'CTO 技术面': '架构面',
    'HR 综合面': '综合面',
    压力面: '压力面',
    转行质疑面试官: '转行面',
    '谈薪 HR': '谈薪面',
  }
  if (iv && typeof iv === 'object') {
    if (iv.name && byName[iv.name]) return byName[iv.name]
    return { all: '通用', normal: '常规面', switch: '转行面', salary: '谈薪面' }[iv.interview_type] || iv.interview_type || ''
  }
  return iv || ''
}

function biasText(b) {
  return b === 1 ? '偏难' : b === -1 ? '偏易' : '难度中性'
}
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
  box-shadow: 0 6px 14px rgba(139, 92, 246, 0.28);
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
.interviewer-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
}
.iv-card {
  background: #fff;
  border: 1.5px solid #e4e9f2;
  border-radius: 14px;
  padding: 14px;
  text-align: left;
  cursor: pointer;
  transition: all 0.22s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.iv-card:hover {
  border-color: rgba(139, 92, 246, 0.5);
  box-shadow: var(--app-shadow-sm, 0 1px 3px rgba(20, 20, 20, 0.06));
}
.iv-card.on {
  border-color: #333333;
  background: rgba(26, 26, 26, 0.05);
  box-shadow: 0 0 0 4px rgba(26, 26, 26, 0.1);
}
.iv-top {
  display: flex;
  align-items: center;
  gap: 10px;
}
.iv-avatar {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #444444, #333333);
}
.iv-info {
  flex: 1;
  min-width: 0;
}
.iv-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--app-text);
}
.iv-title {
  font-size: 11px;
  color: var(--app-text-muted);
  margin-top: 1px;
}
.iv-check {
  color: #333333;
  font-size: 16px;
  flex-shrink: 0;
}
.iv-persona {
  margin-top: 10px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--app-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.iv-tags {
  display: flex;
  gap: 6px;
  margin-top: 10px;
}
.iv-tag {
  font-size: 11px;
  color: #333333;
  background: rgba(26, 26, 26, 0.1);
  border-radius: 999px;
  padding: 2px 10px;
}
.loading-text {
  text-align: center;
  color: var(--app-text-muted);
  padding: 30px 0;
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
  background: linear-gradient(135deg, #6b8bff, #8b6bff);
  box-shadow: 0 6px 14px -4px rgba(107, 139, 255, 0.5);
}
.iv-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1.5px solid var(--app-border);
}
.iv-card:hover {
  border-color: rgba(107, 139, 255, 0.5);
  box-shadow: var(--glass-highlight);
}
.iv-card.on {
  border-color: var(--app-cyan);
  background: var(--app-brand-soft);
  box-shadow: 0 0 0 4px rgba(90, 208, 230, 0.14);
}
.iv-avatar {
  color: #071018;
  background: var(--app-brand-gradient);
}
.iv-check { color: var(--app-cyan); }
.iv-tag {
  color: var(--app-cyan);
  background: var(--app-brand-soft);
}
</style>
