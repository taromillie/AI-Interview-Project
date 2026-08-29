<template>
  <div class="landing">
    <!-- 动态极光背景 -->
    <div class="aurora" aria-hidden="true">
      <span class="blob blob-1"></span>
      <span class="blob blob-2"></span>
      <span class="blob blob-3"></span>
      <span class="grid-overlay"></span>
    </div>

    <!-- 顶部玻璃导航 -->
    <header class="nav" :class="{ scrolled }">
      <div class="nav-inner">
        <a class="nav-logo" href="/">
          <span class="logo-mark">✦</span>
          AI Interview Coach
        </a>
        <nav class="nav-links">
          <a class="nav-link" href="#features">核心能力</a>
          <a class="nav-link" href="#flow">使用流程</a>
          <a class="nav-link" href="#roles">适配岗位</a>
        </nav>
        <div class="nav-actions">
          <a class="nav-login" href="/login">登录</a>
          <a class="nav-signup" href="/login?tab=register">
            免费开始 <span aria-hidden="true">→</span>
          </a>
        </div>
      </div>
    </header>

    <main class="main">
      <!-- Hero -->
      <section class="hero">
        <div class="hero-copy iv-rise" style="animation-delay: 0.05s">
          <div class="badge">
            <span class="badge-dot"></span>
            AI 驱动 · 实时模拟面试
          </div>
          <h1 class="hero-title">
            把每一次开口<br />
            <span class="grad">练到从容不迫</span>
          </h1>
          <p class="hero-sub">
            简历与岗位智能匹配、拟真语音模拟面试、自动生成复盘报告 ——
            一站式帮你打磨表达、补齐短板，稳稳拿下下一场面试。
          </p>
          <div class="hero-cta">
            <a class="iv-btn" href="/login?tab=register">
              免费开始模拟 <span aria-hidden="true">→</span>
            </a>
            <a class="iv-btn-ghost" href="/login">已有账号，登录</a>
          </div>
          <div class="hero-stats">
            <div class="stat">
              <div class="stat-num">120+</div>
              <div class="stat-label">岗位题库</div>
            </div>
            <div class="stat-sep"></div>
            <div class="stat">
              <div class="stat-num">实时</div>
              <div class="stat-label">语音评测</div>
            </div>
            <div class="stat-sep"></div>
            <div class="stat">
              <div class="stat-num">秒级</div>
              <div class="stat-label">复盘报告</div>
            </div>
          </div>
        </div>

        <!-- Hero 产品预览玻璃卡 -->
        <div class="hero-preview iv-rise" style="animation-delay: 0.18s">
          <div class="preview-card iv-glass-strong iv-sheen">
            <div class="preview-head">
              <div class="rec">
                <span class="rec-dot"></span> REC
              </div>
              <div class="timer">{{ clock }}</div>
            </div>

            <div class="orb-wrap">
              <span class="orb-ring"></span>
              <span class="orb-ring ring2"></span>
              <span class="orb"></span>
            </div>
            <div class="orb-caption">AI 面试官正在提问</div>

            <div class="question-glass iv-glass">
              请用一个具体项目，说明你是如何定位并解决线上性能瓶颈的。
            </div>

            <div class="wave" aria-hidden="true">
              <span v-for="(h, i) in bars" :key="i" :style="{ height: h + '%', animationDelay: i * 0.06 + 's' }"></span>
            </div>

            <div class="metrics">
              <div class="metric" v-for="m in metrics" :key="m.label">
                <div class="metric-top">
                  <span>{{ m.label }}</span><span>{{ m.value }}</span>
                </div>
                <div class="metric-bar"><span :style="{ width: m.value + '%' }"></span></div>
              </div>
            </div>
          </div>
          <div class="float-badge fb-1 iv-glass">语气自然 · 92</div>
          <div class="float-badge fb-2 iv-glass">逻辑清晰 · 88</div>
        </div>
      </section>

      <!-- 核心能力 -->
      <section id="features" class="section">
        <div class="section-head">
          <div class="kicker">核心能力</div>
          <h2 class="section-title">面试准备，需要的都在这里</h2>
          <p class="section-sub">从简历诊断到实战复盘，覆盖求职全链路的智能工具。</p>
        </div>
        <div class="feature-grid">
          <div
            v-for="(f, i) in features"
            :key="f.title"
            class="feature-card iv-glass iv-rise"
            :style="{ animationDelay: 0.06 * i + 's' }"
          >
            <div class="feature-icon">{{ f.icon }}</div>
            <h3 class="feature-title">{{ f.title }}</h3>
            <p class="feature-desc">{{ f.desc }}</p>
          </div>
        </div>
      </section>

      <!-- 使用流程 -->
      <section id="flow" class="section">
        <div class="section-head">
          <div class="kicker">使用流程</div>
          <h2 class="section-title">三步开启一场高质量模拟</h2>
        </div>
        <div class="flow-grid">
          <div
            v-for="(s, i) in steps"
            :key="s.title"
            class="flow-card iv-glass iv-rise"
            :style="{ animationDelay: 0.08 * i + 's' }"
          >
            <div class="flow-index">0{{ i + 1 }}</div>
            <h3 class="flow-title">{{ s.title }}</h3>
            <p class="flow-desc">{{ s.desc }}</p>
          </div>
        </div>
      </section>

      <!-- 适配岗位 -->
      <section id="roles" class="section">
        <div class="section-head">
          <div class="kicker">适配岗位</div>
          <h2 class="section-title">覆盖主流技术与产品岗位</h2>
        </div>
        <div class="roles">
          <span v-for="r in roles" :key="r" class="role-chip iv-glass">{{ r }}</span>
        </div>
      </section>

      <!-- CTA -->
      <section class="cta-section">
        <div class="cta-card iv-glass-strong iv-sheen">
          <h2 class="cta-title">准备好，把面试练成你的主场</h2>
          <p class="cta-sub">免费开始你的第一场 AI 模拟面试，几分钟即可拿到专属复盘报告。</p>
          <a class="iv-btn cta-btn" href="/login?tab=register">
            立即免费体验 <span aria-hidden="true">→</span>
          </a>
        </div>
      </section>
    </main>

    <!-- 页脚 -->
    <footer class="footer">
      <div class="footer-inner">
        <a class="nav-logo" href="/">
          <span class="logo-mark">✦</span>
          AI Interview Coach
        </a>
        <p class="footer-copy">© {{ year }} AI Interview Coach · 让每一次面试都有备而来</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const scrolled = ref(false)
const seconds = ref(154)
const year = new Date().getFullYear()

const bars = ref(Array.from({ length: 28 }, () => 30 + Math.random() * 70))
const metrics = [
  { label: '内容匹配度', value: 90 },
  { label: '表达流畅度', value: 84 },
  { label: '逻辑结构', value: 88 },
]
const features = [
  { icon: '📄', title: '简历智能诊断', desc: '解析简历与目标 JD 的匹配度，定位缺口并给出可执行的优化建议。' },
  { icon: '🎙️', title: '拟真语音面试', desc: 'AI 面试官逐题追问，模拟真实压力场景，支持语音作答与实时转写。' },
  { icon: '📊', title: '自动复盘报告', desc: '从内容、逻辑到表达多维评分，秒级生成结构化复盘与提升清单。' },
  { icon: '🧭', title: '职业方向诊断', desc: '结合能力画像与市场行情，给出转型路径与目标岗位建议。' },
  { icon: '💰', title: '薪资谈判模拟', desc: '基于真实行情数据模拟薪资谈判，帮你争取更合理的 offer。' },
  { icon: '📚', title: '个性化学习计划', desc: '针对薄弱环节生成专属提升计划与配套题库，训练更高效。' },
]
const steps = [
  { title: '导入简历与目标岗位', desc: '上传简历、选择目标 JD，系统即刻完成匹配分析。' },
  { title: '进入拟真模拟面试', desc: 'AI 面试官按岗位逐题追问，你用语音自然作答。' },
  { title: '查看复盘并针对提升', desc: '获取多维评分与改进建议，按学习计划持续训练。' },
]
const roles = [
  '前端工程师', '后端工程师', '算法工程师', '数据分析', '产品经理',
  '测试工程师', '运维 / SRE', '客户端开发', 'AI 应用工程师', '项目管理',
]

const clock = computed(() => {
  const m = String(Math.floor(seconds.value / 60)).padStart(2, '0')
  const s = String(seconds.value % 60).padStart(2, '0')
  return `${m}:${s}`
})

let timer, waveTimer
function onScroll() {
  scrolled.value = window.scrollY > 12
}
onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
  timer = setInterval(() => { seconds.value += 1 }, 1000)
  waveTimer = setInterval(() => {
    bars.value = bars.value.map(() => 30 + Math.random() * 70)
  }, 550)
})
onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
  clearInterval(timer)
  clearInterval(waveTimer)
})
</script>

<style scoped>
.landing {
  position: relative;
  min-height: 100vh;
  overflow-x: hidden;
  color: var(--iv-text);
  background: var(--iv-bg-deep);
  font-family: 'Sora', -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  --iv-bg: oklch(0.16 0.03 255);
  --iv-bg-deep: oklch(0.11 0.025 260);
  --iv-cyan: oklch(0.82 0.14 195);
  --iv-blue: oklch(0.68 0.15 250);
  --iv-amber: oklch(0.82 0.14 65);
  --iv-text: oklch(0.97 0.01 240);
  --iv-muted: oklch(0.72 0.03 250);
}

/* ---------- 极光背景 ---------- */
.aurora {
  position: fixed;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  background:
    radial-gradient(120% 80% at 80% -10%, oklch(0.2 0.05 250 / 0.6), transparent 60%),
    var(--iv-bg-deep);
}
.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(70px);
  opacity: 0.55;
  will-change: transform;
}
.blob-1 {
  width: 44vw; height: 44vw;
  left: -6vw; top: -8vw;
  background: radial-gradient(circle, var(--iv-blue), transparent 70%);
  animation: blob 20s ease-in-out infinite;
}
.blob-2 {
  width: 40vw; height: 40vw;
  right: -8vw; top: 6vw;
  background: radial-gradient(circle, var(--iv-cyan), transparent 70%);
  animation: blob2 24s ease-in-out infinite;
}
.blob-3 {
  width: 34vw; height: 34vw;
  left: 30vw; bottom: -12vw;
  background: radial-gradient(circle, var(--iv-amber), transparent 72%);
  opacity: 0.32;
  animation: blob 28s ease-in-out infinite reverse;
}
.grid-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(oklch(1 0 0 / 0.03) 1px, transparent 1px),
    linear-gradient(90deg, oklch(1 0 0 / 0.03) 1px, transparent 1px);
  background-size: 54px 54px;
  mask-image: radial-gradient(120% 90% at 50% 0%, black, transparent 75%);
}
@keyframes blob {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(6%, -8%) scale(1.12); }
  66% { transform: translate(-7%, 5%) scale(0.94); }
}
@keyframes blob2 {
  0%, 100% { transform: translate(0, 0) scale(1.05); }
  40% { transform: translate(-8%, 6%) scale(0.9); }
  70% { transform: translate(5%, 9%) scale(1.15); }
}

/* ---------- 玻璃通用 ---------- */
.iv-glass {
  background: linear-gradient(135deg, oklch(1 0 0 / 0.14), oklch(1 0 0 / 0.04));
  backdrop-filter: blur(28px) saturate(150%);
  -webkit-backdrop-filter: blur(28px) saturate(150%);
  border: 1px solid oklch(1 0 0 / 0.16);
  box-shadow:
    0 1px 0 0 oklch(1 0 0 / 0.22) inset,
    0 20px 60px -20px oklch(0 0 0 / 0.55);
}
.iv-glass-strong {
  background: linear-gradient(135deg, oklch(1 0 0 / 0.2), oklch(1 0 0 / 0.06));
  backdrop-filter: blur(36px) saturate(160%);
  -webkit-backdrop-filter: blur(36px) saturate(160%);
  border: 1px solid oklch(1 0 0 / 0.22);
  box-shadow:
    0 1px 0 0 oklch(1 0 0 / 0.3) inset,
    0 24px 70px -20px oklch(0 0 0 / 0.6);
}
.iv-sheen { position: relative; overflow: hidden; isolation: isolate; }
.iv-sheen::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(115deg, transparent 30%, oklch(1 0 0 / 0.28) 48%, transparent 62%);
  transform: translateX(-120%);
  animation: sheen 6s ease-in-out infinite;
  pointer-events: none;
  z-index: 1;
}
@keyframes sheen {
  0%, 55% { transform: translateX(-120%); }
  75%, 100% { transform: translateX(120%); }
}

.iv-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 14px 28px;
  border-radius: 999px;
  font-weight: 600;
  font-size: 15px;
  text-decoration: none;
  color: oklch(0.14 0.02 260);
  background: linear-gradient(135deg, var(--iv-cyan), var(--iv-blue));
  box-shadow:
    0 1px 0 0 oklch(1 0 0 / 0.45) inset,
    0 10px 30px -8px color-mix(in oklch, var(--iv-blue) 60%, transparent);
  transition: transform 0.25s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1)), filter 0.25s ease, box-shadow 0.25s ease;
}
.iv-btn:hover { transform: translateY(-2px); filter: brightness(1.06); }
.iv-btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 14px 24px;
  border-radius: 999px;
  font-weight: 500;
  font-size: 15px;
  text-decoration: none;
  color: var(--iv-text);
  border: 1px solid oklch(1 0 0 / 0.18);
  background: oklch(1 0 0 / 0.06);
  backdrop-filter: blur(16px);
  transition: background 0.25s ease, border-color 0.25s ease, transform 0.25s ease;
}
.iv-btn-ghost:hover {
  background: oklch(1 0 0 / 0.12);
  border-color: oklch(1 0 0 / 0.32);
  transform: translateY(-1px);
}

.iv-rise { opacity: 0; animation: rise 0.7s cubic-bezier(0.22, 1, 0.36, 1) forwards; }
@keyframes rise {
  from { opacity: 0; transform: translateY(18px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ---------- 导航 ---------- */
.nav {
  position: sticky;
  top: 0;
  z-index: 20;
  padding: 14px 24px;
  transition: background 0.3s ease, backdrop-filter 0.3s ease, border-color 0.3s ease;
  border-bottom: 1px solid transparent;
}
.nav.scrolled {
  background: oklch(0.13 0.02 260 / 0.6);
  backdrop-filter: blur(20px) saturate(150%);
  border-bottom: 1px solid oklch(1 0 0 / 0.08);
}
.nav-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 32px;
}
.nav-logo {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 16px;
  font-weight: 700;
  color: var(--iv-text);
  text-decoration: none;
  letter-spacing: 0.2px;
}
.logo-mark {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  background: linear-gradient(135deg, var(--iv-cyan), var(--iv-blue));
  color: oklch(0.14 0.02 260);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  box-shadow: 0 4px 14px -4px var(--iv-blue);
}
.nav-links {
  display: flex;
  gap: 26px;
  margin-right: auto;
  margin-left: 8px;
}
.nav-link {
  font-size: 14px;
  font-weight: 500;
  color: var(--iv-muted);
  text-decoration: none;
  transition: color 0.2s ease;
}
.nav-link:hover { color: var(--iv-text); }
.nav-actions { display: flex; align-items: center; gap: 18px; }
.nav-login {
  font-size: 14px;
  font-weight: 600;
  color: var(--iv-text);
  text-decoration: none;
}
.nav-signup {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--iv-cyan), var(--iv-blue));
  color: oklch(0.14 0.02 260);
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  transition: transform 0.2s ease, filter 0.2s ease;
}
.nav-signup:hover { transform: translateY(-1px); filter: brightness(1.06); }

.main { position: relative; z-index: 1; }

/* ---------- Hero ---------- */
.hero {
  max-width: 1200px;
  margin: 0 auto;
  padding: 70px 24px 90px;
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 56px;
  align-items: center;
}
.badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 500;
  color: var(--iv-text);
  background: oklch(1 0 0 / 0.06);
  border: 1px solid oklch(1 0 0 / 0.14);
  backdrop-filter: blur(12px);
}
.badge-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--iv-cyan);
  box-shadow: 0 0 10px var(--iv-cyan);
  animation: breathe 2s ease-in-out infinite;
}
@keyframes breathe {
  0%, 100% { opacity: 0.6; transform: scale(0.9); }
  50% { opacity: 1; transform: scale(1.1); }
}
.hero-title {
  margin: 22px 0 18px;
  font-size: clamp(38px, 5vw, 62px);
  line-height: 1.14;
  font-weight: 800;
  letter-spacing: -1px;
}
.grad {
  background: linear-gradient(120deg, var(--iv-cyan), var(--iv-blue) 60%, var(--iv-amber));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.hero-sub {
  max-width: 520px;
  font-size: 16px;
  line-height: 1.75;
  color: var(--iv-muted);
  margin-bottom: 30px;
}
.hero-cta { display: flex; flex-wrap: wrap; gap: 14px; margin-bottom: 36px; }
.hero-stats { display: flex; align-items: center; gap: 22px; }
.stat-num {
  font-size: 24px;
  font-weight: 800;
  background: linear-gradient(120deg, var(--iv-cyan), var(--iv-blue));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.stat-label { font-size: 12px; color: var(--iv-muted); margin-top: 2px; }
.stat-sep { width: 1px; height: 30px; background: oklch(1 0 0 / 0.12); }

/* ---------- Hero 预览卡 ---------- */
.hero-preview { position: relative; }
.preview-card {
  border-radius: 24px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.preview-head {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.rec {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1px;
  color: oklch(0.8 0.15 25);
}
.rec-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: oklch(0.65 0.2 25);
  box-shadow: 0 0 10px oklch(0.65 0.2 25);
  animation: breathe 1.4s ease-in-out infinite;
}
.timer {
  font-family: var(--font-mono, ui-monospace, monospace);
  font-size: 14px;
  color: var(--iv-text);
  letter-spacing: 1px;
}
.orb-wrap {
  position: relative;
  width: 116px;
  height: 116px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 14px 0 10px;
}
.orb {
  width: 82px;
  height: 82px;
  border-radius: 50%;
  background: conic-gradient(from 0deg, var(--iv-cyan), var(--iv-blue), var(--iv-amber), var(--iv-cyan));
  box-shadow: 0 0 40px -6px var(--iv-blue), 0 0 0 1px oklch(1 0 0 / 0.2) inset;
  animation: orbBreathe 3.5s ease-in-out infinite;
  filter: blur(0.3px);
}
@keyframes orbBreathe {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.07); }
}
.orb-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1px solid var(--iv-cyan);
  animation: ring 3s ease-out infinite;
}
.orb-ring.ring2 { animation-delay: 1.5s; }
@keyframes ring {
  0% { transform: scale(0.7); opacity: 0.7; }
  100% { transform: scale(1.4); opacity: 0; }
}
.orb-caption { font-size: 12px; color: var(--iv-muted); margin-bottom: 14px; }
.question-glass {
  width: 100%;
  border-radius: 14px;
  padding: 14px 16px;
  font-size: 13.5px;
  line-height: 1.6;
  color: var(--iv-text);
}
.wave {
  width: 100%;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  margin: 16px 0;
}
.wave span {
  width: 3px;
  border-radius: 2px;
  background: linear-gradient(var(--iv-cyan), var(--iv-blue));
  transition: height 0.5s ease;
}
.metrics { width: 100%; display: flex; flex-direction: column; gap: 10px; }
.metric-top {
  display: flex;
  justify-content: space-between;
  font-size: 11.5px;
  color: var(--iv-muted);
  margin-bottom: 5px;
}
.metric-bar {
  height: 6px;
  border-radius: 3px;
  background: oklch(1 0 0 / 0.08);
  overflow: hidden;
}
.metric-bar span {
  display: block;
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, var(--iv-cyan), var(--iv-blue));
  box-shadow: 0 0 10px -2px var(--iv-cyan);
  transition: width 0.8s var(--ease-out, ease);
}
.float-badge {
  position: absolute;
  padding: 9px 14px;
  border-radius: 12px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--iv-text);
}
.fb-1 { top: 30px; right: -18px; animation: float 5s ease-in-out infinite; }
.fb-2 { bottom: 40px; left: -22px; animation: float 6s ease-in-out infinite reverse; }
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

/* ---------- 通用区块 ---------- */
.section { max-width: 1200px; margin: 0 auto; padding: 60px 24px; }
.section-head { text-align: center; margin-bottom: 44px; }
.kicker {
  display: inline-block;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--iv-cyan);
  margin-bottom: 12px;
}
.section-title {
  font-size: clamp(26px, 3.4vw, 38px);
  font-weight: 800;
  letter-spacing: -0.5px;
  margin-bottom: 12px;
}
.section-sub { color: var(--iv-muted); font-size: 15px; }

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
.feature-card {
  border-radius: 18px;
  padding: 26px;
  transition: transform 0.3s var(--ease-out, ease), border-color 0.3s ease;
}
.feature-card:hover { transform: translateY(-6px); border-color: oklch(1 0 0 / 0.28); }
.feature-icon {
  width: 50px;
  height: 50px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-bottom: 16px;
  background: oklch(1 0 0 / 0.06);
  border: 1px solid oklch(1 0 0 / 0.12);
}
.feature-title { font-size: 17px; font-weight: 700; margin-bottom: 8px; }
.feature-desc { font-size: 14px; line-height: 1.7; color: var(--iv-muted); }

.flow-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
.flow-card {
  border-radius: 18px;
  padding: 28px;
  position: relative;
}
.flow-index {
  font-size: 40px;
  font-weight: 800;
  line-height: 1;
  margin-bottom: 14px;
  background: linear-gradient(135deg, var(--iv-cyan), var(--iv-blue));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  opacity: 0.9;
}
.flow-title { font-size: 17px; font-weight: 700; margin-bottom: 8px; }
.flow-desc { font-size: 14px; line-height: 1.7; color: var(--iv-muted); }

.roles {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
}
.role-chip {
  padding: 10px 20px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 500;
  color: var(--iv-text);
  transition: transform 0.2s ease, border-color 0.2s ease;
}
.role-chip:hover { transform: translateY(-2px); border-color: var(--iv-cyan); }

/* ---------- CTA ---------- */
.cta-section { max-width: 1000px; margin: 0 auto; padding: 40px 24px 90px; }
.cta-card {
  border-radius: 28px;
  padding: 56px 40px;
  text-align: center;
}
.cta-title {
  font-size: clamp(26px, 3.6vw, 40px);
  font-weight: 800;
  letter-spacing: -0.5px;
  margin-bottom: 14px;
}
.cta-sub { color: var(--iv-muted); font-size: 15px; margin-bottom: 30px; }
.cta-btn { font-size: 16px; padding: 15px 34px; }

/* ---------- 页脚 ---------- */
.footer {
  position: relative;
  z-index: 1;
  border-top: 1px solid oklch(1 0 0 / 0.08);
  padding: 30px 24px;
}
.footer-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.footer-copy { font-size: 13px; color: var(--iv-muted); }

/* ---------- 响应式 ---------- */
@media (max-width: 900px) {
  .hero { grid-template-columns: 1fr; gap: 40px; text-align: center; }
  .hero-copy { display: flex; flex-direction: column; align-items: center; }
  .hero-cta, .hero-stats { justify-content: center; }
  .feature-grid, .flow-grid { grid-template-columns: 1fr; }
  .nav-links { display: none; }
}
@media (max-width: 560px) {
  .nav-inner { gap: 12px; }
  .nav-signup { padding: 8px 14px; }
  .float-badge { display: none; }
  .footer-inner { flex-direction: column; text-align: center; }
}

@media (prefers-reduced-motion: reduce) {
  .iv-sheen::after, .blob, .orb, .orb-ring, .badge-dot, .rec-dot, .float-badge, .iv-rise {
    animation: none;
  }
  .iv-rise { opacity: 1; }
}
</style>
