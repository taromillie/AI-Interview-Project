<template>
  <div class="dashboard">
    <!-- Hero：大标题 + 居中大输入框 -->
    <section class="hero">
      <div class="hero-title">你好，{{ userStore.username }}</div>
      <div class="hero-desc">告诉我你想面试的岗位，直接开始一场模拟面试</div>
      <div class="big-input">
        <el-icon class="big-ico"><Search /></el-icon>
        <input
          v-model="target"
          class="big-field"
          placeholder="如：后端开发工程师、AI 产品经理…"
          @keyup.enter="startByTarget"
        />
        <button class="big-btn" @click="startByTarget">
          <el-icon :size="17"><MagicStick /></el-icon>
          <span>开始面试</span>
        </button>
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
        <div class="section-title">热门岗位</div>
        <button class="more" @click="go('/jobs')">查看全部 <el-icon><ArrowRight /></el-icon></button>
      </div>
      <div class="job-grid">
        <div v-for="j in hotJobs" :key="j.id" class="job-card" @click="startByJob(j)">
          <div class="job-name">{{ j.name }}</div>
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
        <div class="section-title">更多功能</div>
      </div>
      <div class="cards">
        <button v-for="c in cards" :key="c.path" class="card" @click="go(c.path)">
          <div class="card-ico" :style="{ background: c.bg }">
            <el-icon :size="18"><component :is="c.icon" /></el-icon>
          </div>
          <div class="card-body">
            <div class="card-title">{{ c.title }}</div>
            <div class="card-desc">{{ c.desc }}</div>
          </div>
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
  Calendar,
  Collection,
  Compass,
  Document,
  EditPen,
  Grid,
  MagicStick,
  Microphone,
  Money,
  Search,
  Setting,
  TrendCharts,
  Trophy,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { listPositions } from '@/api/question'

const router = useRouter()
const userStore = useUserStore()
const target = ref('')
const hotJobs = ref([])

const cards = [
  { path: '/interview', title: '模拟面试', desc: '可选面试官与难度的 AI 面试', icon: 'Microphone', bg: 'linear-gradient(135deg,#2563eb,#4f46e5)' },
  { path: '/diagnosis', title: '简历 × JD 诊断', desc: '上传简历 + 粘贴 JD 定位差距', icon: 'Document', bg: 'linear-gradient(135deg,#0ea5e9,#3b82f6)' },
  { path: '/offer', title: 'Offer 对比', desc: '多 Offer 总包与 AI 建议', icon: 'Trophy', bg: 'linear-gradient(135deg,#10b981,#22c55e)' },
  { path: '/profile', title: '能力画像', desc: '多场面试聚合洞察短板', icon: 'TrendCharts', bg: 'linear-gradient(135deg,#06b6d4,#3b82f6)' },
  { path: '/study-plan', title: '备战日历', desc: '依据能力缺口生成计划', icon: 'Calendar', bg: 'linear-gradient(135deg,#8b5cf6,#d946ef)' },
  { path: '/real-interview', title: '真实面试复盘', desc: '录入真实问答 AI 逐题批改', icon: 'EditPen', bg: 'linear-gradient(135deg,#ec4899,#a855f7)' },
  { path: '/questions', title: '题库管理', desc: '知识原子维护与发布', icon: 'Collection', bg: 'linear-gradient(135deg,#64748b,#94a3b8)' },
  { path: '/providers', title: '模型配置', desc: '配置 LLM API Key', icon: 'Setting', bg: 'linear-gradient(135deg,#6d28d9,#7c3aed)' },
]

function go(path) {
  router.push(path)
}

function startByTarget() {
  const kw = target.value.trim()
  if (!kw) {
    router.push('/jobs')
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

onMounted(async () => {
  try {
    const list = await listPositions()
    hotJobs.value = list.filter((x) => x.status === 'active').slice(0, 6)
  } catch {
    /* 忽略 */
  }
})
</script>

<style scoped>
.dashboard {
  max-width: 960px;
  margin: 0 auto;
}

/* ---------- Hero ---------- */
.hero {
  text-align: center;
  padding: 46px 0 30px;
}
.hero-title {
  font-size: 32px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 0.3px;
}
.hero-desc {
  margin-top: 10px;
  font-size: 15px;
  color: #64748b;
}
.big-input {
  max-width: 600px;
  margin: 26px auto 0;
  height: 58px;
  background: #fff;
  border: 1.5px solid #e2e8f0;
  border-radius: 999px;
  display: flex;
  align-items: center;
  padding: 0 8px 0 20px;
  box-shadow: var(--app-shadow-sm, 0 1px 3px rgba(15, 23, 42, 0.06));
  transition: border-color 0.2s, box-shadow 0.25s;
}
.big-input:focus-within {
  border-color: #2563eb;
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12), var(--app-shadow-md, 0 8px 20px rgba(15, 23, 42, 0.08));
}
.big-ico {
  color: #94a3b8;
  font-size: 19px;
  margin-right: 10px;
  flex-shrink: 0;
}
.big-field {
  flex: 1;
  border: none;
  outline: none;
  font-size: 15px;
  color: #0f172a;
  background: transparent;
  min-width: 0;
}
.big-field::placeholder {
  color: #b0b9c9;
}
.big-btn {
  border: none;
  height: 44px;
  padding: 0 22px;
  border-radius: 999px;
  background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  flex-shrink: 0;
  transition: transform 160ms var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1)), box-shadow 0.2s;
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3);
}
.big-btn:hover {
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4);
}
.big-btn:active {
  transform: scale(0.96);
}
.quick-row {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}
.quick {
  border: 1px solid #e2e8f0;
  background: #fff;
  color: #475569;
  font-size: 13px;
  border-radius: 999px;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: all 0.18s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.quick:hover {
  border-color: #2563eb;
  color: #2563eb;
  background: rgba(37, 99, 235, 0.04);
}

/* ---------- 通用 section ---------- */
.section {
  margin-top: 26px;
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.section-title {
  font-size: 17px;
  font-weight: 700;
  color: #0f172a;
}
.more {
  border: none;
  background: none;
  color: #2563eb;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  font-weight: 600;
}
.more:hover {
  opacity: 0.75;
}

/* ---------- 岗位卡片 ---------- */
.job-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px;
}
.job-card {
  background: #fff;
  border: 1px solid #eef1f6;
  border-radius: var(--app-radius-lg, 16px);
  padding: 18px;
  cursor: pointer;
  box-shadow: var(--app-shadow-sm, 0 1px 3px rgba(15, 23, 42, 0.06));
  transition: transform 0.22s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1)), box-shadow 0.25s, border-color 0.25s;
}
.job-card:hover {
  transform: translateY(-3px);
  border-color: rgba(37, 99, 235, 0.35);
  box-shadow: var(--app-shadow-md, 0 10px 24px rgba(15, 23, 42, 0.1));
}
.job-name {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}
.job-meta {
  margin: 6px 0 10px;
  font-size: 12px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 6px;
}
.dot-sep {
  color: #cbd5e1;
}
.job-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  min-height: 22px;
}
.pill {
  background: #f1f5f9;
  color: #475569;
  font-size: 11px;
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
  color: #2563eb;
}

/* ---------- 功能卡片 ---------- */
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}
.card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  border: 1px solid #eef1f6;
  border-radius: var(--app-radius-md, 14px);
  padding: 14px 16px;
  cursor: pointer;
  text-align: left;
  transition: transform 0.2s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1)), box-shadow 0.25s, border-color 0.25s;
}
.card:hover {
  transform: translateY(-2px);
  border-color: rgba(37, 99, 235, 0.3);
  box-shadow: var(--app-shadow-md, 0 10px 24px rgba(15, 23, 42, 0.08));
}
.card-ico {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.card-body {
  flex: 1;
  min-width: 0;
}
.card-title {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}
.card-desc {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.card-arrow {
  color: #cbd5e1;
  flex-shrink: 0;
  transition: transform 0.2s, color 0.2s;
}
.card:hover .card-arrow {
  color: #2563eb;
  transform: translateX(3px);
}
</style>
