<template>
  <div class="resume-match">
    <!-- 顶部 Hero -->
    <div class="hero">
      <div class="hero-title">岗位匹配</div>
      <div class="hero-desc">根据你的简历技能，从岗位库中智能推荐最适合你的岗位</div>
    </div>

    <!-- 简历选择 + 过滤 -->
    <div class="panel">
      <div class="panel-head">
        <span class="panel-title">选择简历</span>
        <button class="refresh-btn" :disabled="loadingResumes" @click="loadResumes">
          <el-icon :size="13" :class="{ spinning: loadingResumes }"><Refresh /></el-icon>
          {{ loadingResumes ? '加载中…' : '刷新' }}
        </button>
      </div>

      <div v-if="resumes.length" class="resume-list">
        <button
          v-for="r in resumes"
          :key="r.id"
          class="resume-item"
          :class="{ on: selectedId === r.id }"
          @click="selectResume(r)"
        >
          <span class="resume-name">{{ r.name }}</span>
          <span class="resume-skills">{{ (r.skills || []).slice(0, 4).join(' / ') || '暂无技能标签' }}</span>
        </button>
      </div>
      <div v-else-if="!loadingResumes" class="empty-hint">
        还没有简历，先到
        <router-link class="link" to="/diagnosis">简历诊断</router-link>
        上传一份简历，再回来匹配岗位
      </div>

      <div class="filter-row">
        <div class="filter-group">
          <span class="filter-label">方向</span>
          <el-select v-model="filters.direction" clearable placeholder="不限" class="filter-select">
            <el-option v-for="d in directionOptions" :key="d.value" :label="d.label" :value="d.value" />
          </el-select>
        </div>
        <div class="filter-group">
          <span class="filter-label">难度</span>
          <el-select v-model="filters.difficulty" clearable placeholder="不限" class="filter-select">
            <el-option v-for="d in difficultyOptions" :key="d.value" :label="d.label" :value="d.value" />
          </el-select>
        </div>
        <div class="filter-group">
          <span class="filter-label">城市</span>
          <el-input v-model="filters.city" clearable placeholder="如：北京" class="filter-input" />
        </div>
        <div class="filter-group">
          <span class="filter-label">数量</span>
          <el-select v-model="filters.limit" class="filter-select limit">
            <el-option v-for="n in [5, 10, 20]" :key="n" :label="`Top ${n}`" :value="n" />
          </el-select>
        </div>
        <button class="match-btn" :disabled="!selectedId || matching" @click="runMatch">
          <el-icon v-if="!matching" :size="15"><MagicStick /></el-icon>
          <span v-else class="spinner" />
          {{ matching ? '匹配中…' : '智能匹配岗位' }}
        </button>
      </div>
    </div>

    <!-- 结果区 -->
    <template v-if="displayList.length">
      <div class="result-head">
        <span class="result-title">
          {{ isHistory ? '最近一次推荐' : '推荐结果' }}
          <span class="result-count">共 {{ displayList.length }} 个岗位</span>
        </span>
        <span v-if="matchedAtText" class="result-time">{{ matchedAtText }}</span>
      </div>

      <div class="match-list">
        <div v-for="(item, i) in displayList" :key="item.position_id + '-' + i" class="match-card">
          <!-- 排名 + 匹配分 -->
          <div class="score-col">
            <span class="rank">#{{ i + 1 }}</span>
            <el-progress
              type="dashboard"
              :percentage="Math.round(item.match_score)"
              :width="74"
              :stroke-width="8"
              :color="scoreColor(item.match_score)"
            >
              <template #default="{ percentage }">
                <div class="score-num">{{ percentage }}</div>
                <div class="score-cap">匹配度</div>
              </template>
            </el-progress>
          </div>

          <!-- 岗位信息 -->
          <div class="info-col">
            <div class="job-head">
              <div class="job-name">{{ item.company || '未标注公司' }}</div>
              <div class="job-tags">
                <el-tag size="small" effect="plain">{{ directionText(item.direction) }}</el-tag>
                <el-tag size="small" :type="difficultyType(item.difficulty)" effect="light">
                  {{ difficultyText(item.difficulty) }}
                </el-tag>
              </div>
            </div>
            <div class="job-position">{{ item.name }}</div>
            <div class="job-meta">
              <span v-if="item.city" class="meta-chip"><el-icon :size="12"><Location /></el-icon>{{ item.city }}</span>
              <span class="meta-chip salary" :class="{ off: !salaryText(item) }">
                <el-icon :size="12"><Wallet /></el-icon>{{ salaryText(item) || '薪资面议' }}
              </span>
            </div>

            <div class="skills-block">
              <span v-for="s in item.matched_skills || []" :key="'m' + s" class="skill-pill hit">
                <el-icon :size="11"><Check /></el-icon>{{ s }}
              </span>
              <span v-for="s in item.missing_skills || []" :key="'x' + s" class="skill-pill miss">{{ s }}</span>
            </div>
            <div class="reason">
              <el-icon :size="13"><InfoFilled /></el-icon>
              {{ item.reason }}
            </div>
            <div v-if="item.dimension_breakdown" class="dimension">
              技能 {{ fmtDim(item.dimension_breakdown.skill_score) }} 分 · 方向 {{ fmtDim(item.dimension_breakdown.direction_score) }} 分 · 经验 {{ fmtDim(item.dimension_breakdown.exp_score) }} 分
            </div>
          </div>

          <!-- 操作 -->
          <div class="actions-col">
            <button class="interview-btn" @click="startInterview(item)">
              <el-icon :size="15"><MagicStick /></el-icon>
              开始面试
            </button>
            <button class="detail-btn" @click="openDetail(item)">
              查看岗位
              <el-icon :size="13"><ArrowRight /></el-icon>
            </button>
          </div>
        </div>
      </div>
    </template>

    <el-empty
      v-else-if="ran && !matching"
      description="没有匹配到合适岗位，换个简历或筛选条件试试"
      :image-size="90"
    />

    <!-- 岗位详情弹窗 -->
    <Transition name="fade">
      <div v-if="detail" class="modal-mask" @click.self="detail = null">
        <div class="modal">
          <div class="modal-head">
            <div>
              <div class="modal-name">{{ detail.company || detail.name }}</div>
              <div class="modal-sub">
                <span>{{ detail.name }}</span>
                <span v-if="detail.city" class="dot">·</span>
                <span v-if="detail.city">{{ detail.city }}</span>
                <span class="dot">·</span>
                <span>{{ salaryText(detail) || '薪资面议' }}</span>
              </div>
            </div>
            <button class="modal-close" @click="detail = null">
              <el-icon><Close /></el-icon>
            </button>
          </div>

          <div class="modal-body">
            <div class="info-grid">
              <div class="info-item">
                <div class="info-label">薪资范围</div>
                <div class="info-value">{{ salaryText(detail) || '面议' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">工作地点</div>
                <div class="info-value">{{ detail.city || '不限' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">岗位方向</div>
                <div class="info-value">{{ directionText(detail.direction) }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">经验要求</div>
                <div class="info-value">{{ difficultyText(detail.difficulty) }}</div>
              </div>
            </div>

            <div v-if="detail.skills && detail.skills.length" class="section">
              <div class="section-title">技能要求</div>
              <div class="skill-tags">
                <span v-for="s in detail.skills" :key="s" class="skill-pill">{{ s }}</span>
              </div>
            </div>

            <div class="section">
              <div class="section-title">职位描述 / 工作内容</div>
              <div class="jd-text">{{ detail.description || '暂无详细描述' }}</div>
            </div>
          </div>

          <div class="modal-foot">
            <div class="match-info">
              综合匹配度 <b :style="{ color: scoreColor(detail.match_score) }">{{ detail.match_score }} 分</b>
            </div>
            <button class="interview-btn" @click="startInterview(detail)">
              <el-icon :size="15"><MagicStick /></el-icon>
              针对此岗位开始模拟面试
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowRight,
  Check,
  Close,
  InfoFilled,
  Location,
  MagicStick,
  Refresh,
  Wallet,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { listResumes } from '@/api/diagnostic'
import { listResumeMatches, matchPositions } from '@/api/match'
import { formatDateTime } from '@/utils/time'

const router = useRouter()

const resumes = ref([])
const selectedId = ref(null)
const loadingResumes = ref(false)
const matching = ref(false)
const ran = ref(false)
const filters = ref({ direction: '', city: '', difficulty: '', limit: 10 })
const results = ref([])
const matchedAt = ref('')
const history = ref([])
const isHistory = ref(false)
const detail = ref(null)

const directionOptions = [
  { value: 'backend', label: '后端' },
  { value: 'frontend', label: '前端' },
  { value: 'algorithm', label: '算法' },
  { value: 'product', label: '产品' },
  { value: 'operations', label: '运营' },
  { value: 'data', label: '数据' },
]
const difficultyOptions = [
  { value: 'junior', label: '初级' },
  { value: 'mid', label: '中级' },
  { value: 'senior', label: '高级' },
]

const displayList = computed(() => (results.value.length ? results.value : history.value))

const matchedAtText = computed(() => {
  if (isHistory.value && history.value.length) return '匹配于 ' + formatDateTime(history.value[0].created_at)
  if (!isHistory.value && matchedAt.value) return '匹配于 ' + formatDateTime(matchedAt.value)
  return ''
})

function directionText(d) {
  return { backend: '后端', frontend: '前端', algorithm: '算法', product: '产品', operations: '运营', data: '数据' }[d] || d || '通用'
}
function difficultyText(d) {
  return { junior: '初级', mid: '中级', senior: '高级' }[d] || d || '通用'
}
function difficultyType(d) {
  return { junior: 'success', mid: 'warning', senior: 'danger' }[d] || 'info'
}
function salaryText(j) {
  if (!j) return ''
  if (j.salary_min && j.salary_max) return j.salary_min + '-' + j.salary_max + 'K'
  if (j.salary_min) return j.salary_min + 'K 以上'
  if (j.salary_max) return j.salary_max + 'K 以内'
  return ''
}
function scoreColor(score) {
  if (score >= 80) return '#16a34a'
  if (score >= 60) return '#ea580c'
  return '#d1d5db'
}
function fmtDim(v) {
  return Number(v || 0).toFixed(0)
}

async function loadResumes() {
  loadingResumes.value = true
  try {
    resumes.value = await listResumes()
  } catch {
    /* http 拦截器已提示 */
  } finally {
    loadingResumes.value = false
  }
}

async function selectResume(r) {
  selectedId.value = r.id
  results.value = []
  ran.value = false
  // 展示该简历最近一次的推荐结果
  try {
    const list = await listResumeMatches(r.id)
    history.value = list || []
    isHistory.value = list && list.length > 0
  } catch {
    history.value = []
    isHistory.value = false
  }
}

async function runMatch() {
  if (!selectedId.value) {
    ElMessage.warning('请先选择一份简历')
    return
  }
  matching.value = true
  try {
    const res = await matchPositions(selectedId.value, {
      limit: filters.value.limit,
      direction: filters.value.direction || undefined,
      city: filters.value.city || undefined,
      difficulty: filters.value.difficulty || undefined,
    })
    results.value = res.results || []
    matchedAt.value = res.matched_at || ''
    isHistory.value = false
    ran.value = true
    if (!results.value.length) ElMessage.info('没有匹配到合适岗位，试试放宽筛选条件')
  } catch {
    /* http 拦截器已提示 */
  } finally {
    matching.value = false
  }
}

function startInterview(item) {
  detail.value = null
  router.push({ name: 'interview', query: { position_id: item.position_id } })
}

function openDetail(item) {
  detail.value = item
}

// 初始加载简历列表
loadResumes()
</script>

<style scoped>
.resume-match {
  max-width: 1000px;
  margin: 0 auto;
}

/* ── Hero ── */
.hero {
  text-align: center;
  padding: 10px 0 22px;
}
.hero-title {
  font-size: 30px;
  font-weight: 800;
  color: var(--app-text);
  letter-spacing: 0.5px;
}
.hero-desc {
  margin-top: 8px;
  color: var(--app-text-secondary);
  font-size: 14px;
}

/* ── 简历选择面板 ── */
.panel {
  background: #fff;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-lg, 16px);
  padding: 18px 20px 20px;
  box-shadow: var(--app-shadow-sm, 0 1px 3px rgba(20, 20, 20, 0.04));
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.panel-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--app-text);
}
.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border: 1px solid var(--app-border);
  background: #fff;
  color: var(--app-text-secondary);
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.18s;
}
.refresh-btn:hover:not(:disabled) {
  border-color: #1a1a1a;
  color: #1a1a1a;
}
.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.spinning {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.resume-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.resume-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 3px;
  min-width: 170px;
  padding: 10px 14px;
  border: 1.5px solid var(--app-border);
  border-radius: 12px;
  background: #fafaf9;
  cursor: pointer;
  text-align: left;
  transition: all 0.18s;
}
.resume-item:hover {
  border-color: var(--app-border-strong);
}
.resume-item.on {
  border-color: #1a1a1a;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(26, 26, 26, 0.06);
}
.resume-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text);
}
.resume-skills {
  font-size: 12px;
  color: var(--app-text-muted);
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.empty-hint {
  font-size: 13px;
  color: var(--app-text-secondary);
  padding: 8px 0;
}
.link {
  color: #1a1a1a;
  font-weight: 600;
}

.filter-row {
  display: flex;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed var(--app-border);
}
.filter-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.filter-label {
  font-size: 12px;
  color: var(--app-text-muted);
}
.filter-select {
  width: 130px;
}
.filter-select :deep(.el-select__wrapper) {
  border-radius: 10px;
  box-shadow: 0 0 0 1px var(--app-border) inset;
}
.filter-select.limit {
  width: 100px;
}
.filter-input :deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 0 0 1px var(--app-border) inset;
}
.match-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 40px;
  padding: 0 22px;
  border: none;
  border-radius: 12px;
  background: #1a1a1a;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-left: auto;
  transition: transform 160ms var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1)), box-shadow 0.2s;
  box-shadow: 0 4px 12px rgba(26, 26, 26, 0.25);
}
.match-btn:hover:not(:disabled) {
  box-shadow: 0 6px 18px rgba(26, 26, 26, 0.25);
}
.match-btn:active:not(:disabled) {
  transform: scale(0.97);
}
.match-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.spinner {
  width: 15px;
  height: 15px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* ── 结果区 ── */
.result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 26px 0 14px;
}
.result-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--app-text);
}
.result-count {
  font-size: 12px;
  font-weight: 500;
  color: var(--app-text-muted);
  margin-left: 8px;
}
.result-time {
  font-size: 12px;
  color: var(--app-text-muted);
}

.match-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.match-card {
  display: flex;
  gap: 18px;
  background: #fff;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-lg, 16px);
  padding: 18px 20px;
  transition: transform 0.22s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1)), box-shadow 0.25s ease, border-color 0.25s ease;
  box-shadow: var(--app-shadow-sm, 0 1px 3px rgba(20, 20, 20, 0.04));
}
.match-card:hover {
  border-color: rgba(26, 26, 26, 0.25);
  box-shadow: var(--app-shadow-md, 0 10px 24px rgba(20, 20, 20, 0.08));
}

.score-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  width: 84px;
}
.rank {
  font-size: 12px;
  font-weight: 700;
  color: var(--app-text-muted);
  font-variant-numeric: tabular-nums;
}
.score-num {
  font-size: 20px;
  font-weight: 800;
  color: var(--app-text);
  line-height: 1;
}
.score-cap {
  font-size: 10px;
  color: var(--app-text-muted);
}

.info-col {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.job-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}
.job-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--app-text);
  line-height: 1.35;
}
.job-tags {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}
.job-position {
  font-size: 13px;
  font-weight: 600;
  color: var(--app-text-secondary);
}
.job-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  color: #1a1a1a;
  background: #f0f0ee;
  padding: 3px 9px;
  border-radius: 8px;
}
.meta-chip.salary {
  color: #ea580c;
  background: #fff7ed;
}
.meta-chip.salary.off {
  color: var(--app-text-muted);
  background: #f4f4f2;
}

.skills-block {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.skill-pill {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  background: #f4f4f2;
  color: var(--app-text-secondary);
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 999px;
}
.skill-pill.hit {
  background: #f0fdf4;
  color: #16a34a;
}
.skill-pill.miss {
  color: var(--app-text-muted);
  text-decoration: line-through;
}
.reason {
  display: flex;
  align-items: flex-start;
  gap: 5px;
  font-size: 12.5px;
  line-height: 1.65;
  color: var(--app-text-secondary);
  background: #fafaf9;
  border: 1px solid #f4f4f2;
  border-radius: 10px;
  padding: 8px 12px;
}
.reason .el-icon {
  margin-top: 3px;
  flex-shrink: 0;
  color: var(--app-text-muted);
}
.dimension {
  font-size: 11px;
  color: var(--app-text-muted);
  font-variant-numeric: tabular-nums;
}

.actions-col {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
  flex-shrink: 0;
  width: 130px;
}
.interview-btn {
  height: 42px;
  border: none;
  border-radius: 12px;
  background: #1a1a1a;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  cursor: pointer;
  transition: transform 160ms var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1)), box-shadow 0.2s;
  box-shadow: 0 4px 12px rgba(26, 26, 26, 0.25);
}
.interview-btn:hover {
  box-shadow: 0 6px 18px rgba(26, 26, 26, 0.25);
}
.interview-btn:active {
  transform: scale(0.97);
}
.detail-btn {
  height: 40px;
  border: 1px solid var(--app-border);
  border-radius: 12px;
  background: #fff;
  color: var(--app-text-secondary);
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  cursor: pointer;
  transition: all 0.18s;
}
.detail-btn:hover {
  border-color: #1a1a1a;
  color: #1a1a1a;
}

/* ── 详情弹窗 ── */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(20, 20, 20, 0.4);
  backdrop-filter: blur(3px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.modal {
  width: 640px;
  max-width: 100%;
  max-height: 86vh;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 24px 64px rgba(20, 20, 20, 0.2);
  overflow: hidden;
}
.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 22px 24px 16px;
  border-bottom: 1px solid #f4f4f2;
}
.modal-name {
  font-size: 20px;
  font-weight: 800;
  color: var(--app-text);
}
.modal-sub {
  margin-top: 6px;
  font-size: 13px;
  color: var(--app-text-secondary);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}
.dot {
  color: var(--app-border-strong);
}
.modal-close {
  border: none;
  background: #f4f4f2;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--app-text-secondary);
  cursor: pointer;
  flex-shrink: 0;
}
.modal-close:hover {
  background: var(--app-border);
}
.modal-body {
  padding: 18px 24px;
  overflow-y: auto;
}
.info-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}
.info-item {
  background: #fafaf9;
  border: 1px solid #f4f4f2;
  border-radius: 12px;
  padding: 10px 12px;
}
.info-label {
  font-size: 11px;
  color: var(--app-text-muted);
}
.info-value {
  margin-top: 4px;
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text);
}
.section {
  margin-top: 18px;
}
.section-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--app-text);
  margin-bottom: 8px;
}
.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.jd-text {
  font-size: 13px;
  line-height: 1.8;
  color: var(--app-text-secondary);
  background: #fafaf9;
  border: 1px solid #f4f4f2;
  border-radius: 12px;
  padding: 12px 14px;
  white-space: pre-wrap;
}
.modal-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 14px 24px 18px;
  border-top: 1px solid #f4f4f2;
}
.match-info {
  font-size: 13px;
  color: var(--app-text-secondary);
}
.match-info b {
  font-size: 16px;
}
.modal-foot .interview-btn {
  height: 42px;
  padding: 0 18px;
}

/* 弹窗过渡 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-active .modal,
.fade-leave-active .modal {
  transition: transform 0.22s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
.fade-enter-from .modal,
.fade-leave-to .modal {
  transform: translateY(16px) scale(0.98);
}

@media (max-width: 720px) {
  .match-card {
    flex-direction: column;
    gap: 14px;
  }
  .score-col {
    flex-direction: row;
    width: auto;
    align-items: center;
  }
  .actions-col {
    width: 100%;
    flex-direction: row;
  }
  .actions-col .interview-btn,
  .actions-col .detail-btn {
    flex: 1;
  }
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
