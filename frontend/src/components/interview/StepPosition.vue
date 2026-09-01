<template>
  <section class="w-card">
    <div class="w-head">
      <span class="w-ico"><el-icon :size="20"><Aim /></el-icon></span>
      <div>
        <div class="w-title">选择目标岗位</div>
        <div class="w-desc">面试问题将围绕该岗位的技能要求展开</div>
      </div>
    </div>

    <el-form label-position="top">
      <el-form-item label="岗位">
        <el-radio-group v-model="positionMode" class="mode-group">
          <el-radio-button value="preset">岗位库</el-radio-button>
          <el-radio-button value="custom">自定义</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-form-item v-if="positionMode === 'preset'">
        <el-select
          v-model="selectedPositionId"
          filterable
          placeholder="从岗位库选择（支持关键词搜索）"
          class="full"
        >
          <el-option v-for="p in positions" :key="p.id" :label="positionOptionLabel(p)" :value="p.id">
            <span class="opt-company">{{ p.company || '未知公司' }}</span>
            <span class="opt-position">{{ p.name }}</span>
            <span class="opt-meta">{{ positionMeta(p) }}</span>
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item v-else label="岗位名称">
        <el-input
          v-model="customPosition"
          placeholder="如：后端开发工程师、AI 产品经理…"
          maxlength="60"
          @keyup.enter="$emit('next')"
        />
      </el-form-item>

      <el-form-item label="使用简历（可选）">
        <el-select v-model="selectedResumeId" clearable placeholder="不选则使用最近一份简历" class="full">
          <el-option v-for="r in resumes" :key="r.id" :label="r.name || `简历 #${r.id}`" :value="r.id" />
        </el-select>
      </el-form-item>
    </el-form>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { Aim } from '@element-plus/icons-vue'

const props = defineProps({
  positions: { type: Array, default: () => [] },
  positionMode: { type: String, default: 'preset' },
  selectedPositionId: { type: [Number, String], default: null },
  customPosition: { type: String, default: '' },
  resumes: { type: Array, default: () => [] },
  selectedResumeId: { type: [Number, String], default: null },
})
const emit = defineEmits([
  'update:positionMode',
  'update:selectedPositionId',
  'update:customPosition',
  'update:selectedResumeId',
  'next',
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

function positionOptionLabel(p) {
  return p.company ? `${p.company} ${p.name}` : p.name
}

function positionMeta(p) {
  const d = { junior: '初级', mid: '中级', senior: '高级' }[p.difficulty] || p.difficulty || ''
  const dir = { backend: '后端', frontend: '前端', algorithm: '算法', product: '产品', operations: '运营', data: '数据' }[p.direction] || ''
  return `${dir} ${d}`.trim()
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
.full { width: 100%; }
.mode-group { margin-bottom: 4px; }
.opt-company { color: var(--app-text); font-weight: 600; font-size: 13px; }
.opt-position { margin-left: 8px; color: var(--app-text-muted); font-size: 12px; }
.opt-meta { float: right; color: var(--app-text-muted); font-size: 12px; }

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
.opt-company { color: var(--app-text); }
.opt-position { color: var(--app-text-secondary); }
.opt-meta { color: var(--app-text-muted); }
</style>
