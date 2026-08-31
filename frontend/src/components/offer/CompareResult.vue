<template>
  <div v-if="table.length" class="compare-result">
    <el-table :data="table" border size="small" class="cmp-table">
      <el-table-column prop="field" label="维度" width="130" />
      <el-table-column
        v-for="(_, i) in companies.length"
        :key="i"
        :label="companies[i] || `Offer ${i + 1}`"
      >
        <template #default="{ row }">
          <span
            :class="{
              best: isBest(row, i),
              total: row.field.includes('年化总包'),
            }"
          >
            {{ row.values[i] }}
          </span>
        </template>
      </el-table-column>
    </el-table>
    <div class="best-hint">绿色高亮 = 该维度最优</div>

    <template v-if="analysis">
      <div class="section-title">AI 综合建议</div>
      <div class="analysis-box">{{ analysis }}</div>
    </template>
    <template v-else>
      <div class="analysis-pending">
        <span class="pending-dot"></span>
        AI 正在分析，请稍候…
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  table: { type: Array, default: () => [] },
  analysis: { type: String, default: '' },
})

// 列公司名优先取自对比表的“公司”行快照（与后端列顺序天然一致），
// 历史回看时 Offer 可能已删除，仍能正确显示表头。
const companies = computed(() => {
  const row = props.table.find((r) => r.field === '公司')
  if (row?.values?.length) return row.values
  return []
})

function isBest(row, i) {
  const values = row.values.map((v) => Number(String(v).replace(/[^\d.]/g, '')) || 0)
  if (row.field.includes('生活平衡')) {
    return values[i] === Math.max(...values) && values[i] > 0
  }
  return values[i] === Math.max(...values) && values[i] > 0
}
</script>

<style scoped>
.cmp-table {
  width: 100%;
}
.best {
  color: #67c23a;
  font-weight: 700;
}
.total {
  font-weight: 700;
  color: #303133;
}
.best-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--app-text-muted);
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 20px 0 10px;
}
.analysis-box {
  background: #f0f7ff;
  border: 1px solid #d6e9ff;
  border-radius: 8px;
  padding: 14px 16px;
  font-size: 13px;
  color: #303133;
  line-height: 1.8;
  white-space: pre-wrap;
}

/* ==================== 深色液态玻璃覆盖 ==================== */
.best { color: var(--app-success); }
.total { color: var(--app-text); }
.section-title { color: var(--app-text); }
.analysis-box {
  background: var(--app-brand-soft);
  border: 1px solid rgba(90, 208, 230, 0.25);
  color: var(--app-text);
}
.analysis-pending {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 20px;
  padding: 14px 16px;
  border-radius: 8px;
  background: var(--app-brand-soft);
  border: 1px dashed rgba(90, 208, 230, 0.3);
  color: var(--app-text-secondary);
  font-size: 13px;
}
.pending-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--app-brand-gradient);
  animation: pending-blink 1s ease-in-out infinite;
}
@keyframes pending-blink {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}
</style>
