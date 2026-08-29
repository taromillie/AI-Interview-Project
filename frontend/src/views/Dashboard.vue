<template>
  <div class="dashboard">
    <!-- Hero：对话式入口 -->
    <section class="hero">
      <h1 class="hero-title">你的 AI 面试官</h1>
      <p class="hero-desc">告诉它你想面的岗位，直接开始一场真实感的模拟面试</p>

      <div class="hero-card">
        <p class="hero-card__prompt">告诉我你想面试的岗位</p>
        <p class="hero-card__hint">例如：字节 AI 产品经理终面 · CTO 面我 · 压力面 · 30 分钟</p>
        <form class="cta-form" @submit.prevent="startByTarget">
          <input
            v-model="target"
            class="cta-field"
            placeholder="输入岗位名称，或直接上传岗位描述…"
            @keyup.enter="startByTarget"
          />
          <button type="submit" class="cta-btn">
            <span>开始面试</span>
            <el-icon :size="15"><ArrowRight /></el-icon>
          </button>
        </form>
        <div class="chips">
          <button v-for="c in chips" :key="c.text" type="button" class="chip" @click="useChip(c)">
            {{ c.text }}
          </button>
        </div>
      </div>

      <div class="quick-row">
        <button class="quick" @click="go('/diagnosis')"><el-icon><Document /></el-icon>简历诊断</button>
        <button class="quick" @click="go('/jobs')"><el-icon><Grid /></el-icon>岗位广场</button>
        <button class="quick" @click="go('/career')"><el-icon><Compass /></el-icon>转行诊断</button>
        <button class="quick" @click="go('/salary')"><el-icon><Money /></el-icon>谈薪评估</button>
      </div>
    </section>

    <!-- 热门岗位 -->
    <section v-if="hotJobs.length" class="section">
      <div class="section-head">
        <p class="num-label">01 — 热门岗位</p>
        <button class="more" @click="go('/jobs')">查看全部 <el-icon><ArrowRight /></el-icon></button>
      </div>
      <div class="job-grid">
        <div v-for="j in hotJobs" :key="j.id" class="job-card" @click="startByJob(j)">
          <div class="job-name">{{ j.company || j.name }}</div>
          <div class="job-position">{{ j.name }}</div>
          <div class="job-meta">
            <span>{{ directionText(j.direction) }}</span>
            <span class="dot-sep">·</span>
            <span>{{ difficultyText(j.difficulty) }}</span>
          </div>
          <div class="job-skills">
            <span v-for="s in (j.skills || []).slice(0, 3)" :key="s" class="pill">{{ s }}</span>
          </div>
          <div class="job-go">去面试 <el-icon><ArrowRight /></el-icon></div>
        </div>
      </div>
    </section>

    <!-- 功能入口 -->
    <section class="section">
      <div class="section-head">
        <p class="num-label">02 — 更多功能</p>
      </div>
      <div class="cards">
        <button v-for="(c, i) in cards" :key="c.path" class="card" @click="go(c.path)">
          <span class="card-num">{{ String(i + 1).padStart(2, '0') }}</span>
          <span class="card-body">
            <span class="card-title">{{ c.title }}</span>
            <span class="card-desc">{{ c.desc }}</span>
          </span>
          <el-icon class="card-arrow"><ArrowRight /></el-icon>
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowRight,
  Compass,
  Document,
  Grid,
  Money,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { listPositions } from '@/api/question'

const router = useRouter()
const userStore = useUserStore()
const target = ref('')
const hotJobs = ref([])

const chips = [
  { text: '我想面字节的 AI 产品经理', target: '字节 AI 产品经理' },
  { text: '我想体验 HR 面', target: 'HR 面试' },
  { text: '根据我简历挑个岗位面', target: '' },
  { text: '来一场压力面试', target: '压力面' },
]

const cards = [
  { path: '/interview', title: '模拟面试', desc: '可选面试官与难度的 AI 面试' },
  { path: '/diagnosis', title: '简历 × JD 诊断', desc: '上传简历 + 粘贴 JD 定位差距' },
  { path: '/real-interview', title: '真实面试复盘', desc: '录入真实问答 AI 逐题批改' },
  { path: '/offer', title: 'Offer 对比', desc: '多 Offer 总包与 AI 建议' },
  { path: '/profile', title: '能力画像', desc: '多场面试聚合洞察短板' },
  { path: '/study-plan', title: '备战日历', desc: '依据能力缺口生成计划' },
  { path: '/career', title: '转行诊断', desc: '评估转行可行性与路径' },
  { path: '/salary', title: '谈薪评估', desc: '了解你的市场薪资水位' },
  { path: '/questions', title: '题库管理', desc: '知识原子维护与发布' },
  { path: '/providers', title: '模型配置', desc: '配置 LLM API Key' },
]

function go(path) {
  router.push(path)
}

function useChip(c) {
  if (c.target) {
    router.push({ name: 'interview', query: { target: c.target } })
  } else {
    go('/diagnosis')
  }
}

function startByTarget() {
  const kw = target.value.trim()
  if (!kw) {
    go('/jobs')
    return
  }
  router.push({ name: 'interview', query: { target: kw } })
}

function startByJob(j) {
  router.push({ name: 'interview', query: { position_id: j.id } })
}

function directionText(d) {
  return { backend: '后端', frontend: '前端', algorithm: '算法', product: '产品', operations: '运营', data: '数据' }[d] || d || '通用'
}
function difficultyText(d) {
  return { junior: '初级', mid: '中级', senior: '高级' }[d] || d || '通用'
}

const fallbackJobs = [
  { id: 1, name: 'Java 开发工程师', company: '云启科技', direction: 'backend', difficulty: 'mid', skills: ['Java', 'Spring Boot', 'MySQL'] },
  { id: 2, name: '前端开发工程师', company: '星图网络', direction: 'frontend', difficulty: 'mid', skills: ['Vue', 'React', 'TypeScript'] },
  { id: 3, name: '算法工程师', company: '智算引擎', direction: 'algorithm', difficulty: 'senior', skills: ['Python', 'PyTorch', '机器学习'] },
  { id: 4, name: '产品经理', company: '青禾科技', direction: 'product', difficulty: 'mid', skills: ['需求分析', 'Axure', '数据分析'] },
  { id: 5, name: 'Go 后端开发', company: '极光云', direction: 'backend', difficulty: 'senior', skills: ['Go', 'gRPC', 'Redis'] },
  { id: 6, name: '数据分析师', company: '数维科技', direction: 'data', difficulty: 'junior', skills: ['SQL', 'Python', 'Tableau'] },
]

onMounted(async () => {
  try {
    const list = await listPositions()
    const active = list.filter((x) => x.status === 'active')
    // 按岗位名去重取样，保证热门岗位展示不同岗位，而不是清一色同一岗位名
    const seen = new Set()
    const diverse = active.filter((x) => {
      if (seen.has(x.name)) return false
      seen.add(x.name)
      return true
    })
    hotJobs.value = diverse.length > 1 ? diverse.slice(0, 6) : fallbackJobs
  } catch {
    hotJobs.value = fallbackJobs
  }
})
</script>

<style scoped>
.dashboard {
  max-width: 1000px;
  margin: 0 auto;
}

/* ---------- Hero ---------- */
.hero {
  text-align: center;
  padding: 46px 0 34px;
}
.hero-title {
  font-size: clamp(30px, 5vw, 42px);
  font-weight: 800;
  letter-spacing: -0.03em;
  background: linear-gradient(120deg, #4f46e5 0%, #a855f7 55%, #ec4899 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
  line-height: 1.15;
}
.hero-desc {
  margin-top: 10px;
  font-size: 15px;
  color: var(--app-text-secondary);
}

/* 输入卡片 */
.hero-card {
  max-width: 640px;
  margin: 30px auto 0;
  background: var(--glass-bg-strong);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  border-radius: var(--app-radius-lg);
  padding: 26px 28px 22px;
  text-align: left;
  box-shadow: var(--app-shadow-md);
}
.hero-card__prompt {
  font-size: 16px;
  font-weight: 600;
  color: var(--app-text);
}
.hero-card__hint {
  margin-top: 5px;
  font-size: 12px;
  color: var(--app-text-muted);
}

.cta-form {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  margin-top: 16px;
  border: 1px solid var(--app-border-strong);
  border-radius: 14px;
  padding: 5px;
  background: rgba(255, 255, 255, 0.6);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.cta-form:focus-within {
  border-color: var(--app-brand);
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.18);
}
.cta-field {
  border: none;
  background: transparent;
  outline: none;
  padding: 10px 12px;
  font-size: 14px;
  color: var(--app-text);
  min-width: 0;
}
.cta-field::placeholder {
  color: #b0b0b0;
}
.cta-btn {
  border: none;
  background: var(--app-brand-gradient);
  color: #fff;
  border-radius: 10px;
  padding: 10px 20px;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  box-shadow: 0 6px 18px -4px rgba(99, 102, 241, 0.5);
  transition: box-shadow 0.2s ease, transform 160ms var(--ease-out);
}
@media (hover: hover) and (pointer: fine) {
  .cta-btn:hover {
    box-shadow: 0 10px 26px -4px rgba(99, 102, 241, 0.6);
    transform: translateY(-1px);
  }
}
.cta-btn:active {
  transform: scale(0.97);
}

/* 快捷选项 */
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}
.chip {
  border: 1px solid var(--app-border-strong);
  background: rgba(255, 255, 255, 0.5);
  color: var(--app-text-secondary);
  font-size: 12px;
  border-radius: 999px;
  padding: 6px 13px;
  cursor: pointer;
  transition: border-color 0.18s ease, color 0.18s ease, background-color 0.18s ease;
}
@media (hover: hover) and (pointer: fine) {
  .chip:hover {
    border-color: var(--app-brand);
    color: var(--app-brand);
    background: var(--app-brand-soft);
  }
}

.quick-row {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 22px;
}
.quick {
  border: 1px solid var(--app-border-strong);
  background: rgba(255, 255, 255, 0.5);
  color: var(--app-text-secondary);
  font-size: 13px;
  border-radius: 999px;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: color 0.18s ease, border-color 0.18s ease, background-color 0.18s ease;
}
@media (hover: hover) and (pointer: fine) {
  .quick:hover {
    border-color: var(--app-brand);
    color: var(--app-brand);
    background: var(--app-brand-soft);
  }
}

/* ---------- Section ---------- */
.section {
  margin-top: 34px;
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.num-label {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--app-text-muted);
  font-weight: 600;
}
.more {
  border: none;
  background: none;
  color: var(--app-text-secondary);
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: color 0.18s ease;
}
@media (hover: hover) and (pointer: fine) {
  .more:hover {
    color: var(--app-text);
  }
}

/* ---------- 岗位卡片 ---------- */
.job-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 14px;
}
.job-card {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  border-radius: var(--app-radius-md);
  padding: 18px;
  cursor: pointer;
  box-shadow: var(--app-shadow-sm);
  transition: border-color 0.2s ease, transform 0.2s var(--ease-out), box-shadow 0.2s ease;
}
@media (hover: hover) and (pointer: fine) {
  .job-card:hover {
    border-color: rgba(99, 102, 241, 0.5);
    transform: translateY(-3px);
    box-shadow: var(--app-shadow-md);
  }
}
.job-card:active {
  transform: scale(0.98);
}
.job-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--app-text);
}
.job-position {
  margin-top: 3px;
  font-size: 12px;
  color: var(--app-text-muted);
  font-weight: 500;
}
.job-meta {
  margin: 6px 0 10px;
  font-size: 12px;
  color: var(--app-text-muted);
  display: flex;
  align-items: center;
  gap: 6px;
}
.dot-sep {
  color: var(--app-border-strong);
}
.job-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  min-height: 22px;
}
.pill {
  background: var(--app-brand-soft);
  color: var(--app-brand);
  font-size: 11px;
  font-weight: 500;
  padding: 2px 9px;
  border-radius: 999px;
}
.job-go {
  margin-top: 14px;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--app-brand);
}

/* ---------- 功能列表 ---------- */
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 10px;
}
.card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  border-radius: var(--app-radius-md);
  padding: 14px 16px;
  cursor: pointer;
  text-align: left;
  box-shadow: var(--app-shadow-sm);
  transition: border-color 0.2s ease, transform 0.2s var(--ease-out), box-shadow 0.2s ease;
}
@media (hover: hover) and (pointer: fine) {
  .card:hover {
    border-color: rgba(99, 102, 241, 0.5);
    transform: translateY(-2px);
    box-shadow: var(--app-shadow-md);
  }
}
.card:active {
  transform: scale(0.985);
}
.card-num {
  font-size: 12px;
  font-weight: 600;
  color: var(--app-text-muted);
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}
.card-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text);
}
.card-desc {
  font-size: 12px;
  color: var(--app-text-muted);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.card-arrow {
  color: var(--app-border-strong);
  flex-shrink: 0;
  transition: transform 0.2s var(--ease-out), color 0.2s ease;
}
@media (hover: hover) and (pointer: fine) {
  .card:hover .card-arrow {
    color: var(--app-text);
    transform: translateX(3px);
  }
}
</style>
