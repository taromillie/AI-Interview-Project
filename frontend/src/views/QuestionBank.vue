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
          <div class="header-actions">
            <el-button @click="importDialogVisible = true">批量导入</el-button>
            <el-button type="primary" @click="dialogVisible = true">新建题目</el-button>
          </div>
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
        <el-input
          v-model="tag"
          clearable
          placeholder="按标签精确筛选"
          style="width: 160px"
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

    <!-- 批量导入 -->
    <el-dialog v-model="importDialogVisible" title="批量导入题目" width="640px" top="6vh">
      <el-alert type="info" :closable="false" style="margin-bottom: 14px">
        <template #title>
          支持 JSON 数组（含 question/tags/reference_points）或 Markdown（## 题目 + 要点列表）。
          重复题目自动跳过；导入后为私有草稿，可逐条发布。
        </template>
      </el-alert>
      <el-form :model="importForm" label-width="90px">
        <el-form-item label="所属岗位">
          <el-select v-model="importForm.position_id" placeholder="选择岗位" style="width: 100%">
            <el-option v-for="p in positions" :key="p.id" :label="positionLabel(p)" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="格式">
          <el-radio-group v-model="importForm.format">
            <el-radio value="auto">自动识别</el-radio>
            <el-radio value="json">JSON</el-radio>
            <el-radio value="markdown">Markdown</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="importForm.text"
            type="textarea"
            :rows="8"
            placeholder="粘贴题目内容，或点击下方选择 .json / .md 文件"
          />
        </el-form-item>
        <el-form-item label="文件">
          <input ref="fileInput" type="file" accept=".json,.md,.txt" style="display: none" @change="onImportFile" />
          <el-button @click="fileInput.click()">选择文件</el-button>
          <span v-if="importFileName" class="file-name">{{ importFileName }}</span>
          <el-button v-if="importFileName" text type="primary" @click="clearImportFile">清除</el-button>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="doImport">开始导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { Collection } from '@element-plus/icons-vue'
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createAtom, importAtoms, listAtoms, listPositions, publishAtom } from '@/api/question'

const DIFF_TEXT = { junior: '初级', mid: '中级', senior: '高级' }
const STATUS_TEXT = { draft: '草稿', published: '已发布', archived: '已归档' }
const STATUS_TYPE = { draft: 'info', published: 'success', archived: 'warning' }

const positions = ref([])
const atoms = ref([])
const positionId = ref(null)
const keyword = ref('')
const tag = ref('')

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

// ── 批量导入 ──
const importDialogVisible = ref(false)
const importing = ref(false)
const importForm = reactive({ position_id: null, format: 'auto', text: '' })
const importFileName = ref('')
const fileInput = ref(null)

function onImportFile(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  importFileName.value = file.name
  const reader = new FileReader()
  reader.onload = () => {
    importForm.text = String(reader.result || '')
  }
  reader.readAsText(file)
  e.target.value = ''
}

function clearImportFile() {
  importFileName.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

async function doImport() {
  if (!importForm.position_id) {
    ElMessage.warning('请选择所属岗位')
    return
  }
  if (!importForm.text.trim()) {
    ElMessage.warning('请粘贴内容或选择文件')
    return
  }
  importing.value = true
  try {
    const res = await importAtoms({
      position_id: importForm.position_id,
      format: importForm.format,
      text: importForm.text,
    })
    const base = `导入完成：新建 ${res.created} 条，跳过重复 ${res.skipped} 条`
    const failed = (res.errors || []).length
    if (failed) {
      ElMessage.warning(`${base}，失败 ${failed} 条`)
    } else {
      ElMessage.success(base)
    }
    importDialogVisible.value = false
    Object.assign(importForm, { position_id: null, format: 'auto', text: '' })
    clearImportFile()
    await loadAtoms()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '导入失败，请检查内容格式')
  } finally {
    importing.value = false
  }
}

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
    if (tag.value.trim()) params.tag = tag.value.trim()
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
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.filters {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 14px;
  flex-wrap: wrap;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-md);
  box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.08);
}
.tag {
  margin-right: 4px;
}
.header-actions {
  display: flex;
  gap: 8px;
}
.file-name {
  margin-left: 8px;
  font-size: 13px;
  color: var(--app-text-secondary);
}
</style>
