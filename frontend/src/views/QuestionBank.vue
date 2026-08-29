<template>
  <div class="question-bank">
    <div class="page-banner">
      <div class="banner-left">
        <div class="banner-icon">
          <el-icon :size="24"><Collection /></el-icon>
        </div>
        <div>
          <div class="banner-title">题库管理</div>
          <div class="banner-desc">已发布 = 公共题库（全员可见，进入面试追问链路）；草稿 = 仅自己可见的私有题。发布需要管理员权限。</div>
        </div>
      </div>
    </div>
    <el-card>
      <template #header>
        <div class="header">
          <span>题库管理（知识原子）</span>
          <el-button type="primary" @click="dialogVisible = true">新建题目</el-button>
        </div>
      </template>

      <div class="filters">
        <el-select v-model="positionId" clearable placeholder="全部岗位" style="width: 200px" @change="loadAtoms">
          <el-option v-for="p in positions" :key="p.id" :label="positionLabel(p)" :value="p.id" />
        </el-select>
        <el-input
          v-model="keyword"
          clearable
          placeholder="搜索题目 / 标签关键词"
          style="width: 220px"
          class="keyword-input"
          @keyup.enter="loadAtoms"
          @clear="loadAtoms"
        />
        <el-button @click="loadAtoms">搜索</el-button>
        <el-select v-model="status" clearable placeholder="全部状态" style="width: 140px" @change="loadAtoms">
          <el-option label="草稿" value="draft" />
          <el-option label="已发布" value="published" />
          <el-option label="已归档" value="archived" />
        </el-select>
      </div>

      <el-table :data="atoms" v-loading="loading" size="small">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="question" label="题目" min-width="300" show-overflow-tooltip />
        <el-table-column prop="position_id" label="岗位ID" width="80" />
        <el-table-column label="难度" width="90">
          <template #default="{ row }">
            <el-tag size="small">{{ DIFF_TEXT[row.difficulty] || row.difficulty }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="标签" min-width="140">
          <template #default="{ row }">
            <el-tag v-for="t in row.tags || []" :key="t" size="small" type="info" effect="plain" class="tag">
              {{ t }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="STATUS_TYPE[row.status] || 'info'">
              {{ STATUS_TEXT[row.status] || row.status }}
            </el-tag>
            <el-tag
              v-if="row.status === 'published'"
              size="small"
              type="warning"
              effect="plain"
              class="tag"
            >
              公共
            </el-tag>
            <el-tag
              v-else-if="row.status === 'draft'"
              size="small"
              type="info"
              effect="plain"
              class="tag"
            >
              私有
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button v-if="row.status === 'draft'" size="small" type="success" plain @click="publish(row)">
              发布
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建题目 -->
    <el-dialog v-model="dialogVisible" title="新建题目" width="560px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="所属岗位">
          <el-select v-model="form.position_id" placeholder="选择岗位" style="width: 100%">
            <el-option v-for="p in positions" :key="p.id" :label="positionLabel(p)" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="题目">
          <el-input v-model="form.question" type="textarea" :rows="3" placeholder="例如：请讲讲你处理过的高并发问题" />
        </el-form-item>
        <el-form-item label="难度">
          <el-select v-model="form.difficulty" style="width: 140px">
            <el-option label="初级" value="junior" />
            <el-option label="中级" value="mid" />
            <el-option label="高级" value="senior" />
          </el-select>
        </el-form-item>
        <el-form-item label="技能标签">
          <el-input v-model="form.tags" placeholder="逗号分隔，如：Python, FastAPI" />
        </el-form-item>
        <el-form-item label="参考要点">
          <el-input v-model="form.reference" type="textarea" :rows="3" placeholder="逗号分隔的参考回答要点" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveAtom">保存（草稿）</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { Collection } from '@element-plus/icons-vue'
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createAtom, listAtoms, listPositions, publishAtom } from '@/api/question'

const DIFF_TEXT = { junior: '初级', mid: '中级', senior: '高级' }
const STATUS_TEXT = { draft: '草稿', published: '已发布', archived: '已归档' }
const STATUS_TYPE = { draft: 'info', published: 'success', archived: 'warning' }

const positions = ref([])
const atoms = ref([])
const positionId = ref(null)

function positionLabel(p) {
  return p.company ? `${p.company} ${p.name}` : p.name
}
const status = ref(null)
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)

const form = reactive({
  position_id: null,
  question: '',
  difficulty: 'mid',
  tags: '',
  reference: '',
})

async function loadPositions() {
  try {
    positions.value = await listPositions()
  } catch {
    /* 忽略 */
  }
}

async function loadAtoms() {
  loading.value = true
  try {
    const params = {}
    if (positionId.value) params.position_id = positionId.value
    if (status.value) params.status = status.value
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    atoms.value = await listAtoms(params)
  } finally {
    loading.value = false
  }
}

async function saveAtom() {
  if (!form.position_id) {
    ElMessage.warning('请选择所属岗位')
    return
  }
  if (!form.question.trim()) {
    ElMessage.warning('请填写题目')
    return
  }
  saving.value = true
  try {
    await createAtom({
      position_id: form.position_id,
      question: form.question.trim(),
      difficulty: form.difficulty,
      tags: form.tags
        .split(/[,，]/)
        .map((s) => s.trim())
        .filter(Boolean),
      reference_points: form.reference
        .split(/[,，]/)
        .map((s) => s.trim())
        .filter(Boolean),
    })
    ElMessage.success('已保存为草稿')
    dialogVisible.value = false
    Object.assign(form, { position_id: null, question: '', difficulty: 'mid', tags: '', reference: '' })
    await loadAtoms()
  } finally {
    saving.value = false
  }
}

async function publish(row) {
  try {
    await publishAtom(row.id)
    ElMessage.success('已发布')
    await loadAtoms()
  } catch {
    /* 无权限时后端已提示 */
  }
}

onMounted(() => {
  loadPositions()
  loadAtoms()
})
</script>

<style scoped>
/* 顶部 banner 图标：品牌渐变 */
.banner-left {
  display: flex;
  align-items: center;
  gap: 14px;
}
.banner-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: var(--app-brand-gradient);
  box-shadow: 0 8px 20px -6px rgba(99, 102, 241, 0.55);
  flex-shrink: 0;
}
.banner-title {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--app-text);
}
.banner-desc {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--app-text-secondary);
  max-width: 720px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 700;
  color: var(--app-text);
}
.filters {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  padding: 14px;
  border-radius: var(--app-radius-md);
  background: rgba(255, 255, 255, 0.45);
  border: 1px solid var(--glass-border);
}
.tag {
  margin-right: 4px;
}

/* 表格：透明化，透出毛玻璃 */
:deep(.el-table),
:deep(.el-table__inner-wrapper),
:deep(.el-table tr),
:deep(.el-table th.el-table__cell),
:deep(.el-table td.el-table__cell) {
  background-color: transparent;
}
:deep(.el-table) {
  --el-table-border-color: rgba(120, 110, 200, 0.14);
  --el-table-header-text-color: var(--app-text-secondary);
  --el-table-text-color: var(--app-text);
}
:deep(.el-table th.el-table__cell) {
  font-weight: 700;
}
:deep(.el-table__body tr:hover > td.el-table__cell) {
  background-color: rgba(99, 102, 241, 0.08) !important;
}

/* 弹窗：毛玻璃 */
:deep(.el-dialog) {
  background: var(--glass-bg-strong);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  border-radius: var(--app-radius-lg);
  box-shadow: var(--app-shadow-md);
}
:deep(.el-dialog__title) {
  font-weight: 700;
  color: var(--app-text);
}
</style>
