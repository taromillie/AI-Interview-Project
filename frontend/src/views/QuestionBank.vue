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
            <el-button type="primary" plain @click="openAiDialog()">AI 生成</el-button>
            <el-button @click="importDialogVisible = true">批量导入</el-button>
            <el-button type="primary" @click="openCreateEmpty">新建题目</el-button>
          </div>
        </div>
      </template>

      <div v-if="routeKeyword" class="kw-hint">
        <span>正在按知识点筛选：</span>
        <el-tag type="warning" effect="plain" closable @close="clearKeywordFilter">
          {{ routeKeyword }}
        </el-tag>
      </div>

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
        <template #empty>
          <el-empty :image-size="70">
            <template #description>
              <span v-if="hasFilter">未找到与「{{ filterWord }}」匹配的题目</span>
              <span v-else>题库暂无题目，点击下方按钮创建第一道题</span>
            </template>
            <template v-if="hasFilter" #default>
              <el-button type="primary" @click="openCreateForKeyword">创建该知识点题目</el-button>
              <el-button type="primary" plain @click="openAiForKeyword">AI 生成该知识点题目</el-button>
              <el-button @click="clearAllFilters">清除筛选查看全部</el-button>
            </template>
            <template v-else #default>
              <el-button type="primary" @click="openCreateEmpty">新建题目</el-button>
            </template>
          </el-empty>
        </template>
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

    <!-- AI 生成题目 -->
    <el-dialog v-model="aiDialogVisible" title="AI 生成题目" width="720px" top="5vh">
      <el-form :model="aiForm" label-width="90px">
        <el-form-item label="知识点">
          <el-input
            v-model="aiForm.topic"
            placeholder="例如：MySQL 索引、JVM 内存模型、React 性能优化"
            @keyup.enter="doAiGenerate"
          />
        </el-form-item>
        <el-form-item label="所属岗位">
          <el-select v-model="aiForm.position_id" placeholder="选择岗位" style="width: 100%">
            <el-option v-for="p in positions" :key="p.id" :label="positionLabel(p)" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="题目数量">
          <el-radio-group v-model="aiForm.count">
            <el-radio :value="3">3 道</el-radio>
            <el-radio :value="5">5 道</el-radio>
          </el-radio-group>
          <el-button type="primary" style="margin-left: 16px" :loading="aiGenerating" @click="doAiGenerate">
            AI 生成
          </el-button>
        </el-form-item>
      </el-form>

      <template v-if="aiGenerating">
        <div class="ai-loading">
          <el-icon class="is-loading" :size="20"><Loading /></el-icon>
          <span>AI 正在出题，请稍候…</span>
        </div>
      </template>
      <template v-else-if="aiItems.length">
        <el-alert type="success" :closable="false" style="margin-bottom: 10px">
          <template #title>
            已生成 {{ aiItems.length }} 道题，可编辑题干/难度，勾选后保存为草稿
          </template>
        </el-alert>
        <div class="ai-items">
          <div v-for="(it, i) in aiItems" :key="i" class="ai-item">
            <div class="ai-item-head">
              <el-checkbox v-model="it.checked" />
              <span class="ai-item-no">#{{ i + 1 }}</span>
              <el-select v-model="it.difficulty" size="small" style="width: 92px">
                <el-option label="初级" value="junior" />
                <el-option label="中级" value="mid" />
                <el-option label="高级" value="senior" />
              </el-select>
              <el-button text size="small" type="primary" @click="it.showRp = !it.showRp">
                {{ it.showRp ? '收起要点' : '查看参考要点' }}
              </el-button>
            </div>
            <el-input v-model="it.question" type="textarea" :rows="2" />
            <div class="ai-item-tags">
              <el-tag v-for="t in it.tags" :key="t" size="small" type="info" effect="plain">{{ t }}</el-tag>
            </div>
            <ul v-if="it.showRp" class="rp-list">
              <li v-for="(rp, j) in it.reference_points" :key="j">{{ rp }}</li>
            </ul>
          </div>
        </div>
      </template>
      <el-empty
        v-else
        :image-size="60"
        description="填写知识点后点击「AI 生成」，生成后可编辑再保存"
      />

      <template #footer>
        <el-button @click="closeAiDialog">关闭</el-button>
        <el-button v-if="aiItems.length" type="primary" :loading="aiSaving" @click="saveAiItems">
          保存选中（{{ checkedCount }}）到题库
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { Collection, Loading } from '@element-plus/icons-vue'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  createAtom,
  generateAtoms,
  importAtoms,
  listAtoms,
  listPositions,
  publishAtom,
  saveGeneratedAtoms,
} from '@/api/question'

const DIFF_TEXT = { junior: '初级', mid: '中级', senior: '高级' }
const STATUS_TEXT = { draft: '草稿', published: '已发布', archived: '已归档' }
const STATUS_TYPE = { draft: 'info', published: 'success', archived: 'warning' }

const positions = ref([])
const atoms = ref([])
const positionId = ref(null)
const keyword = ref('')
const tag = ref('')
const route = useRoute()
const router = useRouter()

// 从复盘报告等页面跳转携带的"按知识点筛选"条件
const routeKeyword = computed(() => String(route.query.keyword || ''))

// 当前生效的筛选描述（用于空状态提示）；无任何筛选时为空
const filterWord = computed(() => {
  if (routeKeyword.value) return routeKeyword.value
  if (keyword.value.trim()) return keyword.value.trim()
  if (tag.value.trim()) return tag.value.trim()
  if (positionId.value) {
    const p = positions.value.find((x) => x.id === positionId.value)
    return p ? positionLabel(p) : String(positionId.value)
  }
  if (status.value) return STATUS_TEXT[status.value] || status.value
  return ''
})
const hasFilter = computed(() => Boolean(filterWord.value))

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

function clearKeywordFilter() {
  keyword.value = ''
  const q = { ...route.query }
  delete q.keyword
  router.replace({ query: q })
  loadAtoms()
}

// 空状态"创建该知识点题目"：预填题干模板/标签，并沿用当前岗位筛选
function openCreateForKeyword() {
  dialogVisible.value = true
  const kw = keyword.value.trim() || routeKeyword.value || tag.value.trim()
  form.question = kw ? `请结合你的项目经历，谈谈你对「${kw}」的理解与实践。` : ''
  form.tags = kw || ''
  form.reference = ''
  form.difficulty = 'mid'
  form.position_id = positionId.value
}

// 新建题目：清空表单（保留岗位筛选作为默认归属岗位）
function openCreateEmpty() {
  dialogVisible.value = true
  Object.assign(form, { position_id: null, question: '', difficulty: 'mid', tags: '', reference: '' })
  if (positionId.value) form.position_id = positionId.value
}

// 清空全部筛选（含 URL 上的 keyword），查看全部题目
function clearAllFilters() {
  positionId.value = null
  keyword.value = ''
  tag.value = ''
  status.value = null
  const q = { ...route.query }
  delete q.keyword
  router.replace({ query: q })
  loadAtoms()
}

// ── AI 生成题目 ──
const aiDialogVisible = ref(false)
const aiGenerating = ref(false)
const aiSaving = ref(false)
const aiItems = ref([])
const aiForm = reactive({ topic: '', position_id: null, count: 3 })

const checkedCount = computed(() => aiItems.value.filter((i) => i.checked).length)

// 打开 AI 生成弹窗：可预填知识点与岗位
function openAiDialog(topic = '') {
  const kw = topic || keyword.value.trim() || routeKeyword.value || tag.value.trim()
  aiForm.topic = kw
  aiForm.position_id = positionId.value
  aiItems.value = []
  aiDialogVisible.value = true
}

function openAiForKeyword() {
  openAiDialog(filterWord.value)
}

async function doAiGenerate() {
  if (!aiForm.topic.trim()) {
    ElMessage.warning('请填写知识点')
    return
  }
  if (!aiForm.position_id) {
    ElMessage.warning('请选择所属岗位')
    return
  }
  aiGenerating.value = true
  aiItems.value = []
  try {
    const res = await generateAtoms({
      topic: aiForm.topic.trim(),
      position_id: aiForm.position_id,
      count: aiForm.count,
    })
    aiItems.value = (res.items || []).map((it) => ({ ...it, checked: true, showRp: false }))
    if (!aiItems.value.length) ElMessage.warning('AI 未返回有效题目，请重试')
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '生成失败，请先到「模型配置」启用 LLM')
  } finally {
    aiGenerating.value = false
  }
}

async function saveAiItems() {
  const items = aiItems.value
    .filter((i) => i.checked)
    .map(({ checked, showRp, ...rest }) => rest)
  if (!items.length) {
    ElMessage.warning('请勾选要保存的题目')
    return
  }
  aiSaving.value = true
  try {
    const res = await saveGeneratedAtoms({ position_id: aiForm.position_id, items })
    ElMessage.success(`已保存 ${res.count} 道草稿题目，可在列表查看并发布`)
    aiDialogVisible.value = false
    aiItems.value = []
    await loadAtoms()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    aiSaving.value = false
  }
}

function closeAiDialog() {
  aiDialogVisible.value = false
  aiItems.value = []
}

onMounted(() => {
  loadPositions()
  if (routeKeyword.value) {
    // 来自复盘报告"按知识点筛选"的跳转：把关键词填入搜索框并作为初始筛选条件
    keyword.value = routeKeyword.value
    loadAtoms()
  } else {
    loadAtoms()
  }
})
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.kw-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding: 8px 14px;
  font-size: 13px;
  color: var(--el-text-color-regular);
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
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
.ai-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
  padding: 24px 0;
  color: var(--app-text-secondary);
}
.ai-items {
  max-height: 46vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.ai-item {
  padding: 10px 12px;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-md);
  background: rgba(255, 255, 255, 0.03);
}
.ai-item-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.ai-item-no {
  font-size: 12px;
  color: var(--app-text-secondary);
}
.ai-item-tags {
  margin-top: 6px;
}
.rp-list {
  margin: 8px 0 0;
  padding-left: 18px;
  font-size: 13px;
  color: var(--app-text-secondary);
}
.rp-list li {
  margin: 3px 0;
}
</style>
