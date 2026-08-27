<template>
  <div class="question-bank">
    <el-card>
      <template #header>
        <div class="header">
          <span>题库管理（知识原子）</span>
          <el-button type="primary" @click="dialogVisible = true">新建题目</el-button>
        </div>
      </template>

      <div class="filters">
        <el-select v-model="positionId" clearable placeholder="全部岗位" style="width: 200px" @change="loadAtoms">
          <el-option v-for="p in positions" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-select v-model="status" clearable placeholder="全部状态" style="width: 140px" @change="loadAtoms">
          <el-option label="草稿" value="draft" />
          <el-option label="已发布" value="published" />
          <el-option label="已归档" value="archived" />
        </el-select>
        <el-alert
          title="仅「已发布」题目会进入模拟面试的追问链路（发布需要管理员权限）。"
          type="info"
          :closable="false"
          class="tip"
        />
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
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="STATUS_TYPE[row.status] || 'info'">
              {{ STATUS_TEXT[row.status] || row.status }}
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
            <el-option v-for="p in positions" :key="p.id" :label="p.name" :value="p.id" />
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
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createAtom, listAtoms, listPositions, publishAtom } from '@/api/question'

const DIFF_TEXT = { junior: '初级', mid: '中级', senior: '高级' }
const STATUS_TEXT = { draft: '草稿', published: '已发布', archived: '已归档' }
const STATUS_TYPE = { draft: 'info', published: 'success', archived: 'warning' }

const positions = ref([])
const atoms = ref([])
const positionId = ref(null)
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
}
.filters {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.tip {
  flex: 1;
  min-width: 280px;
}
.tag {
  margin-right: 4px;
}
</style>
