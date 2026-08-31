<template>
  <div class="profile">
    <div class="page-banner">
      <div class="banner-left">
        <div class="banner-icon">
          <el-icon :size="24"><TrendCharts /></el-icon>
        </div>
        <div>
          <div class="banner-title">能力画像</div>
          <div class="banner-desc">由你最近多场模拟面试的复盘报告聚合生成：四维度雷达图 + 技能评分 + 优势与提升建议 + 维度趋势。完成面试并生成报告后自动更新。</div>
        </div>
      </div>
    </div>

    <el-card>
      <template #header>
        <div class="header-row">
          <span>能力画像</span>
          <div class="header-right">
            <el-tag v-if="profile.report_count" type="success" size="small">
              已聚合 {{ profile.report_count }} 场面试
            </el-tag>
            <el-button size="small" :loading="loading" @click="load">刷新</el-button>
          </div>
        </div>
      </template>

      <template v-if="profile.report_count">
        <el-row :gutter="24">
          <el-col :span="12">
            <div class="chart-wrap">
              <svg :viewBox="`0 0 ${size} ${size}`" class="radar">
                <!-- 网格 -->
                <polygon
                  v-for="ring in 4"
                  :key="ring"
                  :points="gridPoints(ring / 4)"
                  fill="none"
                  stroke="#e4e7ed"
                  stroke-width="1"
                />
                <!-- 轴线 -->
                <line
                  v-for="(key, i) in dims"
                  :key="`axis-${key}`"
                  :x1="cx"
                  :y1="cy"
                  :x2="point(i, 1)[0]"
                  :y2="point(i, 1)[1]"
                  stroke="#e4e7ed"
                  stroke-width="1"
                />
                <!-- 数据多边形 -->
                <polygon :points="dataPoints" fill="rgba(64,158,255,0.25)" stroke="#409eff" stroke-width="2" />
                <!-- 数据点 -->
                <circle
                  v-for="(key, i) in dims"
                  :key="`dot-${key}`"
                  :cx="point(i, valueOf(key) / 100)[0]"
                  :cy="point(i, valueOf(key) / 100)[1]"
                  r="4"
                  fill="#fff"
                  stroke="#409eff"
                  stroke-width="2"
                />
                <!-- 标签 -->
                <text
                  v-for="(key, i) in dims"
                  :key="`label-${key}`"
                  :x="point(i, 1.28)[0]"
                  :y="point(i, 1.28)[1]"
                  text-anchor="middle"
                  font-size="13"
                  fill="#303133"
                  font-weight="600"
                >
                  {{ dimLabels[key] }}
                </text>
                <!-- 数值 -->
                <text
                  v-for="(key, i) in dims"
                  :key="`val-${key}`"
                  :x="point(i, valueOf(key) / 100)[0]"
                  :y="point(i, valueOf(key) / 100)[1] - 10"
                  text-anchor="middle"
                  font-size="12"
                  fill="#409eff"
                  font-weight="700"
                >
                  {{ Math.round(valueOf(key)) }}
                </text>
              </svg>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="section-title">维度说明</div>
            <div v-for="key in dims" :key="key" class="dim-row">
              <span class="dim-label">{{ dimLabels[key] }}</span>
              <el-progress
                :percentage="Math.round(valueOf(key))"
                :stroke-width="12"
                :color="dimColor(valueOf(key))"
                class="dim-bar"
              />
              <span class="dim-score">{{ Math.round(valueOf(key)) }}</span>
            </div>
          </el-col>
        </el-row>

        <el-divider content-position="left">优势与提升建议</el-divider>
        <el-row :gutter="24">
          <el-col :span="12">
            <div class="advice-block">
              <div class="advice-title ok">值得保持的优势</div>
              <div v-if="profile.strengths.length">
                <div v-for="(s, i) in profile.strengths" :key="i" class="advice-item ok">
                  <span class="advice-badge">＋</span>{{ s }}
                </div>
              </div>
              <el-empty v-else description="优势尚不明显，继续积累面试经验" :image-size="40" />
            </div>
          </el-col>
          <el-col :span="12">
            <div class="advice-block">
              <div class="advice-title warn">重点提升方向</div>
              <div v-if="profile.suggestions.length">
                <div v-for="(s, i) in profile.suggestions" :key="i" class="advice-item warn">
                  <span class="advice-badge">→</span>{{ s }}
                </div>
              </div>
              <el-empty v-else description="暂无明显短板，保持稳定发挥" :image-size="40" />
            </div>
          </el-col>
        </el-row>

        <el-divider content-position="left">技能评分（{{ Object.keys(profile.skill_scores).length }}）</el-divider>
        <div v-if="Object.keys(profile.skill_scores).length" class="skill-grid">
          <div v-for="(score, skill) in profile.skill_scores" :key="skill" class="skill-item">
            <span class="skill-name">{{ skill }}</span>
            <el-progress
              :percentage="Math.round(score)"
              :stroke-width="10"
              :color="dimColor(score)"
              class="skill-bar"
            />
            <span class="skill-score">{{ Math.round(score) }}</span>
          </div>
        </div>
        <el-empty v-else description="暂无技能评分（完成面试后自动生成）" :image-size="50" />

        <el-divider content-position="left">高频弱点（{{ profile.weak_points.length }}）</el-divider>
        <div v-if="profile.weak_points.length" class="weak-list">
          <el-tag
            v-for="(w, i) in profile.weak_points"
            :key="i"
            type="danger"
            effect="plain"
            class="weak-tag"
          >
            {{ w }}
          </el-tag>
        </div>
        <el-empty v-else description="暂无高频弱点" :image-size="50" />

        <el-divider content-position="left">维度趋势（最近 {{ (profile.trend || []).length }} 场）</el-divider>
        <div v-if="(profile.trend || []).length >= 2" class="trend-wrap">
          <svg :viewBox="`0 0 ${TW} ${TH}`" class="trend">
            <!-- 网格线 -->
            <line
              v-for="g in 4"
              :key="`grid-${g}`"
              :x1="PAD_L"
              :y1="ty(25 * g)"
              :x2="TW - PAD_R"
              :y2="ty(25 * g)"
              stroke="#eef2f7"
              stroke-width="1"
            />
            <text
              v-for="g in 4"
              :key="`label-${g}`"
              :x="PAD_L - 8"
              :y="ty(25 * g) + 4"
              text-anchor="end"
              font-size="11"
              fill="var(--app-text-muted)"
            >
              {{ 25 * g }}
            </text>
            <!-- 折线 -->
            <path
              v-for="key in dims"
              :key="`line-${key}`"
              :d="trendPath(key)"
              fill="none"
              :stroke="TREND_COLORS[key]"
              stroke-width="2.5"
              stroke-linejoin="round"
              stroke-linecap="round"
            />
            <!-- 点 -->
            <g v-for="(d, i) in profile.trend" :key="`dot-${i}`">
              <circle
                v-for="key in dims"
                :key="`${key}-${i}`"
                :cx="tx(i)"
                :cy="ty(d.dimensions?.[key] || 0)"
                r="3"
                fill="#fff"
                :stroke="TREND_COLORS[key]"
                stroke-width="2"
              />
              <text
                :x="tx(i)"
                :y="TH - 8"
                text-anchor="middle"
                font-size="11"
                fill="var(--app-text-muted)"
              >
                {{ shortDate(d.created_at) }}
              </text>
            </g>
          </svg>
          <div class="trend-legend">
            <span v-for="key in dims" :key="key" class="legend-item">
              <i class="legend-dot" :style="{ background: TREND_COLORS[key] }" />{{ dimLabels[key] }}
            </span>
          </div>
        </div>
        <el-empty
          v-else
          description="完成 2 场以上面试后，这里会展示各维度得分的变化趋势"
          :image-size="50"
        />
      </template>

      <el-empty
        v-else
        description="暂无面试报告。请先完成一场模拟面试并生成复盘报告，能力画像将自动聚合生成。"
        :image-size="90"
      >
        <el-button type="primary" @click="$router.push({ name: 'interview' })">去模拟面试</el-button>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup>
import { TrendCharts } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { getProfile } from '@/api/profile'
import { shortDate } from '@/utils/time'

const size = 420
const cx = size / 2
const cy = size / 2
const radius = 140

const dims = ['tech', 'expression', 'logic', 'project']
const dimLabels = { tech: '技术深度', expression: '表达清晰', logic: '逻辑思维', project: '项目颗粒度' }

const profile = ref({
  dimensions: {},
  skill_scores: {},
  weak_points: [],
  strengths: [],
  suggestions: [],
  trend: [],
  report_count: 0,
})
const loading = ref(false)

// 趋势图
const TW = 640
const TH = 240
const PAD_L = 44
const PAD_R = 18
const PAD_T = 16
const PAD_B = 30
// 趋势线配色：与深色主题匹配的高亮色；内联 :stroke 直接绑定，不依赖 DOM 顺序
const TREND_COLORS = { tech: '#22d3ee', expression: '#60a5fa', logic: '#34d399', project: '#fbbf24' }

function tx(i) {
  const n = (profile.value.trend || []).length
  if (n < 2) return PAD_L
  return PAD_L + (i * (TW - PAD_L - PAD_R)) / (n - 1)
}

function ty(v) {
  return PAD_T + ((100 - Number(v || 0)) * (TH - PAD_T - PAD_B)) / 100
}

function trendPath(key) {
  const data = profile.value.trend || []
  return data.map((d, i) => `${i ? 'L' : 'M'}${tx(i)},${ty(d.dimensions?.[key])}`).join(' ')
}



function point(i, ratio) {
  const angle = (i / dims.length) * Math.PI * 2 - Math.PI / 2
  return [cx + radius * ratio * Math.cos(angle), cy + radius * ratio * Math.sin(angle)]
}

function gridPoints(ratio) {
  return dims.map((_, i) => point(i, ratio).join(',')).join(' ')
}

function valueOf(key) {
  return Number(profile.value.dimensions?.[key] || 0)
}

const dataPoints = computed(() => dims.map((key, i) => point(i, valueOf(key) / 100).join(',')).join(' '))

function dimColor(v) {
  if (v >= 80) return '#67c23a'
  if (v >= 60) return '#e6a23c'
  return '#f56c6c'
}

async function load() {
  loading.value = true
  try {
    profile.value = await getProfile()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.chart-wrap {
  display: flex;
  justify-content: center;
  padding: 8px 0;
  overflow-x: auto;
}
.radar {
  max-width: 420px;
  width: 100%;
  filter: drop-shadow(0 8px 22px rgba(90, 208, 230, 0.12));
}
/* 雷达网格 / 轴线：暗色玻璃细线 */
.radar polygon,
.radar line {
  stroke: rgba(255, 255, 255, 0.12);
}
/* 数据多边形：青蓝液态玻璃填充 */
.radar polygon[fill^="rgba"] {
  fill: rgba(90, 208, 230, 0.24);
  stroke: var(--app-cyan);
  stroke-width: 2;
}
/* 数据点 */
.radar circle {
  fill: var(--app-cyan);
  stroke: #fff;
  stroke-width: 2;
}
/* 维度标签 */
.radar text[fill="#303133"] {
  fill: var(--app-text);
}
/* 数值 */
.radar text[fill="#409eff"] {
  fill: var(--app-cyan);
}
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text);
  margin: 8px 0 12px;
}
.section-title::before {
  content: '';
  width: 4px;
  height: 14px;
  border-radius: 2px;
  background: var(--app-brand-gradient);
}
.dim-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.dim-label {
  width: 72px;
  font-size: 13px;
  color: var(--app-text-secondary);
  flex-shrink: 0;
}
.dim-bar {
  flex: 1;
}
.dim-score {
  width: 28px;
  text-align: right;
  font-size: 13px;
  font-weight: 700;
  color: var(--app-cyan);
}
.skill-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 16px;
}
.skill-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.skill-name {
  width: 110px;
  font-size: 13px;
  color: var(--app-text-secondary);
  flex-shrink: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.skill-bar {
  flex: 1;
}
.skill-score {
  width: 30px;
  font-size: 13px;
  font-weight: 600;
  color: var(--app-text);
  text-align: right;
}
.weak-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.weak-tag {
  font-size: 13px;
}
.advice-block {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.07), rgba(255, 255, 255, 0.03));
  border: 1px solid var(--app-border);
  border-radius: 12px;
  padding: 14px 16px;
  min-height: 120px;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.1);
}
.advice-title {
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 10px;
}
.advice-title.ok {
  color: var(--app-success);
}
.advice-title.warn {
  color: var(--app-warning);
}
.advice-item {
  display: flex;
  gap: 8px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--app-text-secondary);
  padding: 4px 0;
}
.advice-item.ok .advice-badge {
  color: var(--app-success);
}
.advice-item.warn .advice-badge {
  color: var(--app-warning);
}
.advice-badge {
  flex-shrink: 0;
  font-weight: 800;
}
.trend-wrap {
  padding: 4px 0;
  overflow-x: auto;
}
.trend {
  width: 100%;
  max-width: 720px;
  display: block;
  margin: 0 auto;
}
/* 趋势网格线 */
.trend line {
  stroke: rgba(255, 255, 255, 0.1);
}
/* 趋势折线：颜色由 :stroke="TREND_COLORS[key]" 内联指定 */
.trend > path {
  stroke-width: 2.5;
}
/* 趋势数据点 */
.trend circle {
  fill: var(--app-cyan);
  stroke: #fff;
  stroke-width: 2;
}
.trend-legend {
  display: flex;
  justify-content: center;
  gap: 18px;
  margin-top: 8px;
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--app-text-secondary);
}
.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.25);
}
</style>
