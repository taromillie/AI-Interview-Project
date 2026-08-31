<template>
  <div class="job-market">
    <!-- 顶部：标题 + 数据状态栏 -->
    <div class="hero">
      <div class="hero-title">岗位广场</div>
      <div class="hero-desc">先选岗位方向，再挑心仪公司 —— 浏览真实招聘信息，一键开始模拟面试</div>
      <div class="meta-row">
        <span class="meta-item">
          <el-icon :size="13"><Clock /></el-icon>
          共 {{ directions.length }} 个方向 · {{ positions.length }} 个岗位 · 数据更新于 {{ updatedAgo }}
        </span>
        <div class="auto-sync">
          <el-select v-model="autoInterval" size="small" class="sync-select" @change="onAutoIntervalChange">
            <el-option label="自动更新 · 10 分钟" :value="10" />
            <el-option label="自动更新 · 30 分钟" :value="30" />
            <el-option label="自动更新 · 60 分钟" :value="60" />
            <el-option label="仅手动更新" :value="0" />
          </el-select>
          <span v-if="nextSyncText" class="meta-item">下次自动同步：{{ nextSyncText }}</span>
        </div>
        <button class="refresh-btn" :disabled="syncing" @click="handleSync">
          <el-icon :size="13" :class="{ spinning: syncing }"><Refresh /></el-icon>
          {{ syncing ? '同步中…' : '立即同步' }}
        </button>
      </div>
    </div>

    <!-- ============ 视图一：岗位方向卡 ============ -->
    <div v-if="view === 'grid'" class="direction-grid">
      <div
        v-for="d in directions"
        :key="d.key"
        class="direction-card"
        tabindex="0"
        role="button"
        @click="openDirection(d)"
        @keydown.enter="openDirection(d)"
        @keydown.space.prevent="openDirection(d)"
      >
        <div class="dir-head">
          <div class="dir-name">{{ d.name }}</div>
          <div class="dir-count">{{ d.count }} 家公司</div>
        </div>
        <div class="dir-salary" :class="{ off: !d.salary_min }">
          <template v-if="d.salary_min">{{ d.salary_min }}-{{ d.salary_max }}K</template>
          <template v-else>薪资面议</template>
          <span class="dir-salary-label">平均薪资</span>
        </div>
        <div class="dir-skills">
          <span v-for="s in (d.skills || []).slice(0, 4)" :key="s" class="skill-pill">{{ s }}</span>
          <span v-if="(d.skills || []).length > 4" class="skill-more">+{{ (d.skills || []).length - 4 }}</span>
        </div>
        <div class="dir-foot">
          <button class="dir-btn" @click.stop="startDirectionInterview(d)">
            <el-icon :size="14"><MagicStick /></el-icon>
            面试该方向
          </button>
          <button class="dir-btn ghost" @click.stop="openDirection(d)">
            查看岗位
            <el-icon :size="13"><ArrowRight /></el-icon>
          </button>
        </div>
      </div>
      <el-empty v-if="!loading && !directions.length" description="暂无岗位数据，点击右上角「立即同步」拉取最新招聘信息" :image-size="90" />
    </div>

    <!-- ============ 视图二：方向详情（岗位列表） ============ -->
    <div v-else-if="view === 'detail' && currentDirection" class="detail-view">
      <div class="detail-head">
        <button class="back-btn" @click="backToGrid">
          <el-icon :size="14"><ArrowLeft /></el-icon>
          全部方向
        </button>
        <div class="detail-title-wrap">
          <div class="detail-title">{{ currentDirection.name }}</div>
          <div class="detail-sub">
            {{ currentDirection.count }} 家公司
            <template v-if="currentDirection.salary_min">
              <span class="dot">·</span>
              平均 {{ currentDirection.salary_min }}-{{ currentDirection.salary_max }}K
            </template>
            <span class="dot">·</span>
            {{ filtered.length }} 个岗位
          </div>
        </div>
      </div>

      <div class="search-bar">
        <el-icon class="search-ico"><Search /></el-icon>
        <input
          v-model="keyword"
          class="search-input"
          :placeholder="'在 ' + currentDirection.name + ' 中搜索岗位、公司、技能…'"
          @keyup.enter="applyFilter"
        />
        <button v-if="keyword" class="search-clear" @click="keyword = ''">
          <el-icon><Close /></el-icon>
        </button>
      </div>
      <div class="filter-row">
        <div class="chip-group">
          <span class="chip-label">难度</span>
          <button
            v-for="d in difficultyOptions"
            :key="d.value"
            class="chip"
            :class="{ on: filterDifficulty === d.value }"
            @click="filterDifficulty = d.value"
          >
            {{ d.label }}
          </button>
        </div>
        <button class="refresh-btn" :class="{ on: onlyFavorite }" @click="onlyFavorite = !onlyFavorite">
          <el-icon :size="13"><StarFilled v-if="onlyFavorite" /><Star v-else /></el-icon>
          {{ onlyFavorite ? '仅看已收藏' : '全部岗位' }}
        </button>
      </div>

      <!-- 岗位卡片网格 -->
      <div v-if="filtered.length" class="job-grid">
        <div
          v-for="j in filtered"
          :key="j.id"
          class="job-card"
          tabindex="0"
          role="button"
          @click="openDetail(j)"
          @keydown.enter="openDetail(j)"
          @keydown.space.prevent="openDetail(j)"
        >
          <div class="job-head">
            <div class="job-name-row">
              <div class="job-name">{{ j.company || '未标注公司' }}</div>
              <button
                class="fav-btn"
                :class="{ on: isFav(j.id) }"
                @click.stop="toggleFavorite(j)"
                :title="isFav(j.id) ? '取消收藏' : '收藏岗位'"
              >
                <el-icon :size="15"><StarFilled v-if="isFav(j.id)" /><Star v-else /></el-icon>
              </button>
            </div>
            <div class="job-tags">
              <el-tag v-if="appMeta(j.id)" size="small" :type="appMeta(j.id).type" effect="dark">
                {{ appMeta(j.id).label }}
              </el-tag>
              <el-tag size="small" :type="difficultyType(j.difficulty)" effect="light">
                {{ difficultyText(j.difficulty) }}
              </el-tag>
            </div>
          </div>
          <div class="job-position">{{ j.name }}</div>
          <div class="job-meta">
            <span v-if="j.city" class="meta-chip"><el-icon :size="12"><Location /></el-icon>{{ j.city }}</span>
            <span class="meta-chip salary" :class="{ off: !salaryText(j) }">
              <el-icon :size="12"><Wallet /></el-icon>{{ salaryText(j) || '薪资面议' }}
            </span>
          </div>
          <div class="job-skills">
            <span v-for="s in (j.skills || []).slice(0, 5)" :key="s" class="skill-pill">{{ s }}</span>
            <span v-if="(j.skills || []).length > 5" class="skill-more">+{{ (j.skills || []).length - 5 }}</span>
          </div>
          <div class="job-foot">
            <button class="detail-btn" @click.stop="openDetail(j)">
              查看详情
              <el-icon :size="13"><ArrowRight /></el-icon>
            </button>
            <button class="interview-btn" @click.stop="startInterview(j)">
              <el-icon :size="15"><MagicStick /></el-icon>
              开始面试
            </button>
          </div>
        </div>
      </div>

      <el-empty
        v-else-if="!loading"
        description="该方向下没有匹配的岗位，换个关键词或筛选条件试试"
        :image-size="90"
      />
      <div v-if="loading" class="loading">加载中…</div>
    </div>

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
            <!-- 基本信息 -->
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

            <!-- 技能标签 -->
            <div v-if="detail.skills && detail.skills.length" class="section">
              <div class="section-title">技能要求</div>
              <div class="skill-tags">
                <span v-for="s in detail.skills" :key="s" class="skill-pill">{{ s }}</span>
              </div>
            </div>

            <!-- 福利标签 -->
            <div v-if="detail.welfare && detail.welfare.length" class="section">
              <div class="section-title">公司福利</div>
              <div class="welfare-tags">
                <span v-for="w in detail.welfare" :key="w" class="welfare-pill">
                  <el-icon :size="12"><Check /></el-icon>{{ w }}
                </span>
              </div>
            </div>

            <!-- 职位描述 -->
            <div class="section">
              <div class="section-title">职位描述 / 工作内容</div>
              <div class="jd-text">{{ detail.description || '暂无详细描述' }}</div>
            </div>
          </div>

          <div class="modal-foot">
            <div class="src-info">
              <span class="src-badge">{{ sourceText(detail.source) }}</span>
              <a v-if="detail.source_url" :href="detail.source_url" target="_blank" rel="noopener" class="src-link">
                查看招聘原文
                <el-icon :size="12"><Link /></el-icon>
              </a>
              <span v-else class="src-time">
                {{ detail.published_at ? '发布于 ' + fmtDate(detail.published_at) : '' }}
              </span>
            </div>
            <div class="modal-actions">
              <button class="fav-btn text-btn" @click="goPlan(detail)">
                <el-icon :size="15"><Notebook /></el-icon>
                加入备战计划
              </button>
              <button
                class="fav-btn text-btn"
                :class="{ on: isFav(detail.id) }"
                @click="toggleFavorite(detail)"
              >
                <el-icon :size="15"><StarFilled v-if="isFav(detail.id)" /><Star v-else /></el-icon>
                {{ isFav(detail.id) ? '已收藏' : '收藏' }}
              </button>
              <el-dropdown @command="(c) => setAppStatus(detail, c)">
                <button class="apply-btn" :class="appStatus(detail.id) ? 'st-' + appStatus(detail.id) : ''">
                  {{ appMeta(detail.id) ? appMeta(detail.id).label : '标记投递状态' }}
                  <el-icon :size="12"><ArrowDown /></el-icon>
                </button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item
                      v-for="(v, k) in APPLICATION_STATUS"
                      :key="k"
                      :command="k"
                      :disabled="k === appStatus(detail.id)"
                    >
                      {{ v.label }}
                    </el-dropdown-item>
                    <el-dropdown-item v-if="appStatus(detail.id)" divided command="__remove__">
                      移除跟踪
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <button class="interview-btn" @click="startInterview(detail)">
                <el-icon :size="15"><MagicStick /></el-icon>
                针对此岗位开始模拟面试
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowDown, ArrowLeft, ArrowRight, Check, Clock, Close, Link, Location, MagicStick, Notebook, Refresh, Search, Star, StarFilled, Wallet } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getJobTrackSummary, favoritePosition, unfavoritePosition, setApplication, removeApplication, APPLICATION_STATUS } from '@/api/jobTrack'
import { listDirections, syncPositions, getSyncConfig, updateSyncConfig } from '@/api/question'
import { formatDate, parseDate } from '@/utils/time'

const router = useRouter()
const directions = ref([])
const view = ref('grid') // grid=方向卡 | detail=方向详情
const currentDirection = ref(null)
const keyword = ref('')
const filterDifficulty = ref('')
const loading = ref(true)
const syncing = ref(false)
const detail = ref(null)
const autoInterval = ref(30)
const nextSyncText = ref('')
let pollTimer = null

// ── 收藏与投递跟踪 ──
const favoriteIds = ref(new Set())
const applicationMap = ref({})
const onlyFavorite = ref(false)

const difficultyOptions = [
  { value: '', label: '全部' },
  { value: 'junior', label: '初级' },
  { value: 'mid', label: '中级' },
  { value: 'senior', label: '高级' },
]

// 全部岗位（跨方向展平，用于全局统计）
const positions = computed(() => directions.value.flatMap((d) => d.positions || []))

// 当前视图下的岗位集合
const currentJobs = computed(() =>
  view.value === 'detail' ? currentDirection.value?.positions || [] : positions.value
)

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return currentJobs.value.filter((j) => {
    if (filterDifficulty.value && j.difficulty !== filterDifficulty.value) return false
    if (onlyFavorite.value && !favoriteIds.value.has(j.id)) return false
    if (kw) {
      const haystack = [j.name, j.company, j.city, j.direction, ...(j.skills || [])].join(' ').toLowerCase()
      if (!haystack.includes(kw)) return false
    }
    return true
  })
})

const updatedAgo = computed(() => {
  let latest = null
  for (const j of positions.value) {
    const t = parseDate(j.synced_at)
    if (t && (!latest || t.getTime() > latest.getTime())) latest = t
  }
  if (!latest) return '暂无'
  const diff = (Date.now() - latest.getTime()) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + ' 分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + ' 小时前'
  return Math.floor(diff / 86400) + ' 天前'
})

function directionText(d) {
  const map = { backend: '后端', frontend: '前端', algorithm: '算法', product: '产品', operations: '运营', data: '数据' }
  return map[d] || d || '通用'
}
function difficultyText(d) {
  return { junior: '初级', mid: '中级', senior: '高级' }[d] || d || '通用'
}
function difficultyType(d) {
  return { junior: 'success', mid: 'warning', senior: 'danger' }[d] || 'info'
}
function sourceText(s) {
  const map = { builtin: '示例数据', jobui: '职友集', zhaopin: '智联招聘', liepin: '猎聘' }
  return map[s] || s || '未知来源'
}
function salaryText(j) {
  if (!j) return ''
  if (j.salary_min && j.salary_max) return j.salary_min + '-' + j.salary_max + 'K'
  if (j.salary_min) return j.salary_min + 'K 以上'
  if (j.salary_max) return j.salary_max + 'K 以内'
  return ''
}
function fmtDate(v) {
  return formatDate(v)
}

function applyFilter() {
  // 筛选已由 filtered 计算属性实时生效，回车聚焦到结果区并给出反馈
  if (!filtered.value.length) {
    ElMessage.info(keyword.value.trim() ? '没有符合条件的岗位，试试更换关键词或调整筛选' : '当前没有可展示的岗位')
    return
  }
  const grid = document.querySelector('.job-grid')
  if (grid) grid.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// ── 视图切换 ──
function openDirection(d) {
  currentDirection.value = d
  keyword.value = ''
  filterDifficulty.value = ''
  onlyFavorite.value = false
  view.value = 'detail'
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function backToGrid() {
  view.value = 'grid'
  currentDirection.value = null
  keyword.value = ''
}

// ── 收藏与投递跟踪 ──
const isFav = (id) => favoriteIds.value.has(id)
const appStatus = (id) => (applicationMap.value[id] ? applicationMap.value[id].status : '')
// 安全取状态元信息：后端返回未知状态值时回退为 null，避免取 label 时抛错白屏
const appMeta = (id) => {
  const st = appStatus(id)
  return st && APPLICATION_STATUS[st] ? APPLICATION_STATUS[st] : null
}

// 岗位 → 备战计划：带 position_id 一键跳转（后端据此回填目标岗位与技能）
function goPlan(p) {
  detail.value = null
  router.push({ name: 'study-plan', query: { position_id: p.id } })
}

async function loadTrack() {
  try {
    const s = await getJobTrackSummary()
    favoriteIds.value = new Set(s.favorite_ids || [])
    applicationMap.value = s.applications || {}
  } catch {
    /* 忽略，未登录或接口暂不可用时静默 */
  }
}

async function toggleFavorite(j) {
  try {
    if (isFav(j.id)) {
      await unfavoritePosition(j.id)
      favoriteIds.value = new Set([...favoriteIds.value].filter((x) => x !== j.id))
      ElMessage.success('已取消收藏')
    } else {
      await favoritePosition(j.id)
      favoriteIds.value = new Set([...favoriteIds.value, j.id])
      ElMessage.success('已收藏')
    }
  } catch {
    ElMessage.warning('操作失败，请稍后再试')
  }
}

async function setAppStatus(j, status) {
  if (status === '__remove__') {
    try {
      await removeApplication(j.id)
      const next = { ...applicationMap.value }
      delete next[j.id]
      applicationMap.value = next
      ElMessage.success('已移除投递跟踪')
    } catch {
      ElMessage.warning('操作失败，请稍后再试')
    }
    return
  }
  try {
    await setApplication(j.id, status)
    applicationMap.value = { ...applicationMap.value, [j.id]: { status } }
    ElMessage.success(`已标记为「${APPLICATION_STATUS[status].label}」`)
  } catch {
    ElMessage.warning('操作失败，请稍后再试')
  }
}

// ── 自动同步配置 ──
function fmtNextSync(iso) {
  if (!iso) return ''
  const diff = new Date(iso).getTime() - Date.now()
  if (diff <= 0) return '即将开始'
  const m = Math.ceil(diff / 60000)
  if (m < 60) return m + ' 分钟后'
  const h = Math.floor(m / 60)
  const mm = m % 60
  return h + ' 小时' + (mm ? ' ' + mm + ' 分' : '') + ' 后'
}

async function loadSyncConfig() {
  try {
    const cfg = await getSyncConfig()
    autoInterval.value = cfg.auto_enabled ? cfg.interval_minutes : 0
    nextSyncText.value = cfg.auto_enabled ? fmtNextSync(cfg.next_sync_at) : ''
  } catch {
    /* 忽略，保持默认 */
  }
}

async function onAutoIntervalChange() {
  try {
    await updateSyncConfig({
      auto_enabled: autoInterval.value > 0,
      interval_minutes: autoInterval.value > 0 ? autoInterval.value : undefined,
    })
    ElMessage.success(
      autoInterval.value > 0 ? `已开启自动更新，每 ${autoInterval.value} 分钟同步一次` : '已切换为仅手动更新'
    )
    await loadSyncConfig()
    if (autoInterval.value > 0) startPolling()
    else stopPolling()
  } catch {
    ElMessage.warning('更新同步频率失败')
  }
}

// ── 数据加载与轮询 ──
async function loadData() {
  try {
    directions.value = await listDirections()
  } catch {
    /* 忽略 */
  }
}

function startPolling() {
  if (pollTimer) return
  // 用户选择「仅手动更新」时不轮询
  if (autoInterval.value <= 0) return
  pollTimer = setInterval(async () => {
    // 页面切到后台时不空跑请求
    if (document.visibilityState !== 'visible') return
    try {
      await Promise.all([loadData(), loadSyncConfig()])
    } catch {
      /* 静默失败，下轮重试 */
    }
  }, 60000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function openDetail(j) {
  detail.value = j
}

function startInterview(j) {
  detail.value = null
  router.push({ name: 'interview', query: { position_id: j.id } })
}

// 方向层「面试该方向」：以该方向代表岗位进入面试
function startDirectionInterview(d) {
  if (!d.first_position_id) {
    ElMessage.warning('该方向暂无岗位，无法开始面试')
    return
  }
  router.push({ name: 'interview', query: { position_id: d.first_position_id } })
}

async function handleSync() {
  if (syncing.value) return
  syncing.value = true
  try {
    const res = await syncPositions()
    await loadData()
    if (res && res.ok === false) {
      ElMessage.warning(res.reason || '已有同步任务进行中')
    } else {
      ElMessage.success('岗位数据已同步更新')
    }
    await loadSyncConfig()
  } catch {
    ElMessage.warning('同步失败，请稍后再试')
  } finally {
    syncing.value = false
  }
}

onMounted(async () => {
  await loadData()
  loading.value = false
  await loadSyncConfig()
  loadTrack()
  startPolling()
})

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})
</script>

<style scoped>
.job-market {
  max-width: 1100px;
  margin: 0 auto;
}

/* ── 顶部 Hero ── */
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
.meta-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  margin-top: 14px;
  flex-wrap: wrap;
}
.auto-sync {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}
.sync-select {
  width: 150px;
}
.sync-select :deep(.el-select__wrapper) {
  border-radius: 999px;
  box-shadow: 0 0 0 1px var(--app-border) inset;
  font-size: 12px;
}
.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--app-text-muted);
}
.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border: 1px solid var(--app-border);
  background: #fff;
  color: var(--app-text-secondary);
  font-size: 12px;
  padding: 5px 12px;
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
.refresh-btn.on {
  border-color: rgba(242, 193, 78, 0.6);
  color: #f2c14e;
}
.spinning {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── 视图一：方向卡网格 ── */
.direction-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 18px;
}
.direction-card {
  background: #fff;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-lg, 18px);
  padding: 22px 22px 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  cursor: pointer;
  transition: transform 0.24s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1)),
    box-shadow 0.28s ease, border-color 0.28s ease;
  box-shadow: var(--app-shadow-sm, 0 1px 3px rgba(20, 20, 20, 0.04));
}
.direction-card:hover {
  transform: translateY(-4px);
  border-color: rgba(26, 26, 26, 0.25);
  box-shadow: var(--app-shadow-md, 0 10px 24px rgba(20, 20, 20, 0.08));
}
.dir-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
}
.dir-name {
  font-size: 20px;
  font-weight: 800;
  color: var(--app-text);
  letter-spacing: 0.3px;
}
.dir-count {
  font-size: 12px;
  color: var(--app-text-muted);
  flex-shrink: 0;
}
.dir-salary {
  font-size: 26px;
  font-weight: 800;
  color: #ea580c;
  line-height: 1.1;
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.dir-salary.off {
  color: var(--app-text-muted);
  font-size: 18px;
}
.dir-salary-label {
  font-size: 12px;
  font-weight: 400;
  color: var(--app-text-muted);
}
.dir-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  min-height: 24px;
}
.skill-pill {
  background: #f4f4f2;
  color: var(--app-text-secondary);
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 999px;
}
.skill-more {
  font-size: 12px;
  color: var(--app-text-muted);
  align-self: center;
}
.dir-foot {
  margin-top: auto;
  display: flex;
  gap: 8px;
}
.dir-btn {
  flex: 1;
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
.dir-btn:hover {
  box-shadow: 0 6px 18px rgba(26, 26, 26, 0.25);
}
.dir-btn:active {
  transform: scale(0.97);
}
.dir-btn.ghost {
  flex: 1.1;
  background: #fff;
  border: 1px solid var(--app-border);
  color: var(--app-text-secondary);
  font-weight: 500;
  box-shadow: none;
}
.dir-btn.ghost:hover {
  border-color: #1a1a1a;
  color: #1a1a1a;
}

/* ── 视图二：方向详情 ── */
.detail-head {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 18px;
}
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 1px solid var(--app-border);
  background: #fff;
  color: var(--app-text-secondary);
  font-size: 13px;
  padding: 7px 14px;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.18s;
  flex-shrink: 0;
  margin-top: 2px;
}
.back-btn:hover {
  border-color: #1a1a1a;
  color: #1a1a1a;
}
.detail-title-wrap {
  min-width: 0;
}
.detail-title {
  font-size: 24px;
  font-weight: 800;
  color: var(--app-text);
}
.detail-sub {
  margin-top: 5px;
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
.search-bar {
  position: relative;
  max-width: 560px;
  margin: 0 auto;
  background: #fff;
  border: 1.5px solid var(--app-border);
  border-radius: 16px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  height: 50px;
  transition: border-color 0.2s, box-shadow 0.25s;
  box-shadow: var(--app-shadow-sm, 0 1px 3px rgba(20, 20, 20, 0.04));
}
.search-bar:focus-within {
  border-color: #1a1a1a;
  box-shadow: 0 0 0 4px rgba(26, 26, 26, 0.08), var(--app-shadow-sm, 0 1px 3px rgba(20, 20, 20, 0.04));
}
.search-ico {
  color: var(--app-text-muted);
  font-size: 18px;
  margin-right: 10px;
  flex-shrink: 0;
}
.search-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 15px;
  color: var(--app-text);
  background: transparent;
}
.search-input::placeholder {
  color: #b3b3b3;
}
.search-clear {
  border: none;
  background: #f4f4f2;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--app-text-secondary);
  cursor: pointer;
}
.filter-row {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
  margin: 14px 0 20px;
}
.chip-group {
  display: flex;
  align-items: center;
  gap: 6px;
}
.chip-label {
  font-size: 12px;
  color: var(--app-text-muted);
  margin-right: 2px;
}
.chip {
  border: none;
  background: #fff;
  color: var(--app-text-secondary);
  font-size: 13px;
  padding: 6px 14px;
  border-radius: 999px;
  cursor: pointer;
  border: 1px solid var(--app-border);
  transition: all 0.18s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.chip:hover {
  border-color: #1a1a1a;
  color: #1a1a1a;
}
.chip.on {
  background: #1a1a1a;
  border-color: #1a1a1a;
  color: #fff;
  font-weight: 600;
}

/* ── 岗位卡片网格 ── */
.job-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}
.job-card {
  background: #fff;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-lg, 16px);
  padding: 18px 18px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  cursor: pointer;
  transition: transform 0.22s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1)),
    box-shadow 0.25s ease, border-color 0.25s ease;
  box-shadow: var(--app-shadow-sm, 0 1px 3px rgba(20, 20, 20, 0.04));
}
.job-card:hover {
  transform: translateY(-4px);
  border-color: rgba(26, 26, 26, 0.25);
  box-shadow: var(--app-shadow-md, 0 10px 24px rgba(20, 20, 20, 0.08));
}
.job-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}
.job-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.job-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--app-text);
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.fav-btn {
  border: none;
  background: transparent;
  padding: 2px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--app-text-muted);
  transition: color 0.18s, transform 160ms var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
  flex-shrink: 0;
}
.fav-btn:hover {
  color: #f2c14e;
  transform: scale(1.12);
}
.fav-btn:active {
  transform: scale(0.92);
}
.fav-btn.on {
  color: #f2c14e;
}
.fav-btn.on:hover {
  color: #f8d56a;
}
.job-tags {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-shrink: 0;
}
.job-position {
  margin-top: 4px;
  font-size: 13px;
  color: var(--app-text-secondary);
  font-weight: 600;
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
.job-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  min-height: 22px;
}
.job-foot {
  margin-top: auto;
  display: flex;
  gap: 8px;
}
.detail-btn {
  flex: 1;
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
.interview-btn {
  flex: 1.4;
  height: 40px;
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
.loading {
  text-align: center;
  color: var(--app-text-muted);
  padding: 40px 0;
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
.welfare-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.welfare-pill {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  background: #f0fdf4;
  color: #16a34a;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 999px;
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
.src-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.src-badge {
  font-size: 11px;
  color: var(--app-text-secondary);
  background: #f4f4f2;
  padding: 3px 8px;
  border-radius: 6px;
}
.src-link {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  color: #1a1a1a;
  text-decoration: none;
}
.src-link:hover {
  text-decoration: underline;
}
.src-time {
  font-size: 12px;
  color: var(--app-text-muted);
}
.modal-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.modal-actions .interview-btn {
  flex: none;
  height: 42px;
  padding: 0 18px;
}
.text-btn {
  border: 1px solid var(--app-border);
  border-radius: 12px;
  height: 42px;
  padding: 0 14px;
  gap: 6px;
  color: var(--app-text-secondary);
  font-size: 13px;
}
.text-btn.on {
  border-color: rgba(242, 193, 78, 0.55);
  color: #f2c14e;
}
.apply-btn {
  border: 1px solid var(--app-border);
  background: rgba(255, 255, 255, 0.05);
  color: var(--app-text-secondary);
  font-size: 13px;
  height: 42px;
  padding: 0 14px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  transition: all 0.18s;
}
.apply-btn:hover {
  border-color: rgba(90, 208, 230, 0.5);
  color: var(--app-text);
}
.apply-btn.st-applied {
  color: var(--app-cyan);
  border-color: rgba(90, 208, 230, 0.45);
}
.apply-btn.st-interviewing {
  color: var(--app-amber);
  border-color: rgba(242, 193, 78, 0.45);
}
.apply-btn.st-offer {
  color: var(--app-success);
  border-color: rgba(67, 217, 163, 0.45);
}
.apply-btn.st-rejected {
  color: #f87171;
  border-color: rgba(248, 113, 113, 0.45);
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

@media (max-width: 640px) {
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .filter-row {
    gap: 12px;
  }
}

/* ==================== 深色液态玻璃覆盖 ==================== */
.search-bar {
  background: var(--glass-bg-strong);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-highlight), var(--app-shadow-sm);
}
.search-bar:focus-within {
  border-color: rgba(90, 208, 230, 0.6);
  box-shadow: 0 0 0 4px rgba(90, 208, 230, 0.14), var(--glass-highlight);
}
.search-input::placeholder {
  color: var(--app-text-muted);
}
.search-clear {
  background: rgba(255, 255, 255, 0.08);
  color: var(--app-text-secondary);
}
.chip {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--app-border);
}
.chip:hover {
  border-color: rgba(90, 208, 230, 0.5);
  color: var(--app-text);
}
.chip.on {
  background: var(--app-brand-gradient);
  border-color: transparent;
  color: #071018;
}
.refresh-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--app-border);
}
.refresh-btn:hover:not(:disabled) {
  border-color: rgba(90, 208, 230, 0.5);
  color: var(--app-text);
}

.direction-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-highlight);
}
.direction-card:hover {
  border-color: rgba(90, 208, 230, 0.4);
  box-shadow: var(--glass-highlight), var(--glass-shadow);
}
.dir-salary {
  color: var(--app-amber);
}
.dir-salary.off {
  color: var(--app-text-muted);
}
.dir-btn {
  background: var(--app-brand-gradient);
  color: #071018;
  box-shadow: 0 1px 0 0 rgba(255, 255, 255, 0.4) inset, 0 8px 22px -8px rgba(107, 139, 255, 0.6);
}
.dir-btn:hover {
  filter: brightness(1.08);
  box-shadow: 0 1px 0 0 rgba(255, 255, 255, 0.5) inset, 0 12px 30px -8px rgba(107, 139, 255, 0.7);
}
.dir-btn.ghost {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--app-border);
  color: var(--app-text-secondary);
  box-shadow: none;
}
.dir-btn.ghost:hover {
  border-color: rgba(90, 208, 230, 0.5);
  color: var(--app-text);
}
.back-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--app-border);
}
.back-btn:hover {
  border-color: rgba(90, 208, 230, 0.5);
  color: var(--app-text);
}

.job-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-highlight);
}
.job-card:hover {
  border-color: rgba(90, 208, 230, 0.4);
  box-shadow: var(--glass-highlight), var(--glass-shadow);
}
.meta-chip {
  color: var(--app-text);
  background: rgba(255, 255, 255, 0.07);
}
.meta-chip.salary {
  color: var(--app-amber);
  background: rgba(242, 193, 78, 0.12);
}
.meta-chip.salary.off {
  color: var(--app-text-muted);
  background: rgba(255, 255, 255, 0.05);
}
.skill-pill {
  background: rgba(255, 255, 255, 0.06);
  color: var(--app-text-secondary);
}
.detail-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--app-border);
  color: var(--app-text-secondary);
}
.detail-btn:hover {
  border-color: rgba(90, 208, 230, 0.5);
  color: var(--app-text);
}
.interview-btn {
  background: var(--app-brand-gradient);
  color: #071018;
  box-shadow: 0 1px 0 0 rgba(255, 255, 255, 0.4) inset, 0 8px 22px -8px rgba(107, 139, 255, 0.6);
}
.interview-btn:hover {
  filter: brightness(1.08);
  box-shadow: 0 1px 0 0 rgba(255, 255, 255, 0.5) inset, 0 12px 30px -8px rgba(107, 139, 255, 0.7);
}

/* 详情弹窗玻璃化 */
.modal-mask {
  background: rgba(5, 7, 14, 0.6);
  backdrop-filter: blur(6px);
}
.modal {
  background: rgba(18, 24, 42, 0.9);
  backdrop-filter: blur(32px) saturate(160%);
  -webkit-backdrop-filter: blur(32px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.16);
  box-shadow: var(--glass-shadow);
}
.modal-head {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
.modal-close {
  background: rgba(255, 255, 255, 0.08);
  color: var(--app-text-secondary);
}
.modal-close:hover {
  background: rgba(255, 255, 255, 0.16);
}
.info-item {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.jd-text {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.welfare-pill {
  background: rgba(67, 217, 163, 0.14);
  color: var(--app-success);
}
.modal-foot {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}
.src-badge {
  background: rgba(255, 255, 255, 0.07);
  color: var(--app-text-secondary);
}
.src-link {
  color: var(--app-cyan);
}
</style>
