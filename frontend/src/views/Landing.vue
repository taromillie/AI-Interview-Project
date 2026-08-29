<template>
  <div class="landing">
    <!-- 液态极光背景 -->
    <div class="aurora" aria-hidden="true">
      <span class="blob blob-cyan"></span>
      <span class="blob blob-blue"></span>
      <span class="blob blob-amber"></span>
      <span class="grid-overlay"></span>
    </div>

    <!-- 顶部导航 -->
    <header class="nav">
      <div class="nav-inner">
        <a class="nav-logo" href="/">
          <span class="logo-mark">✦</span>
          AI Interview Coach
        </a>
        <div class="nav-actions">
          <a class="nav-login" href="/login">Login</a>
          <a class="nav-signup" href="/login?tab=register">Sign up</a>
        </div>
      </div>
    </header>

    <!-- Hero -->
    <main class="hero">
      <h1 class="hero-title">
        make your
        <span class="deco deco-dot-yellow"></span>
        interview
        <span class="deco deco-arrow">→</span>
        a
        <span class="deco deco-pill">
          <span class="pill-track"><span class="pill-knob"></span></span>
        </span>
        success
        <span class="deco deco-emoji">🎉</span>
      </h1>

      <p class="hero-sub">
        AI resume &amp; JD matching, realistic mock interviews, and auto-generated
        review reports — everything you need to ace your next interview.
      </p>

      <div class="hero-cta">
        <a class="cta-btn" href="/login">
          Try it for free <span class="cta-arrow">→</span>
        </a>
      </div>
    </main>
  </div>
</template>

<script setup>
</script>

<style scoped>
.landing {
  position: relative;
  min-height: 100vh;
  background: linear-gradient(180deg, #080b14 0%, #05070e 100%);
  display: flex;
  flex-direction: column;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: var(--app-text);
}

/* ---------- 液态极光背景 ---------- */
.aurora {
  position: fixed;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
  background:
    radial-gradient(1200px 800px at 15% -10%, rgba(107, 139, 255, 0.14), transparent 60%),
    radial-gradient(1000px 700px at 110% 10%, rgba(90, 208, 230, 0.12), transparent 55%),
    linear-gradient(180deg, #080b14 0%, #05070e 100%);
}
.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(70px);
  opacity: 0.5;
  will-change: transform;
}
.blob-cyan {
  width: 46vw;
  height: 46vw;
  left: -8vw;
  top: -6vw;
  background: radial-gradient(circle at 30% 30%, rgba(90, 208, 230, 0.6), transparent 70%);
  animation: app-blob 20s var(--ease-in-out) infinite;
}
.blob-blue {
  width: 42vw;
  height: 42vw;
  right: -10vw;
  top: 4vw;
  background: radial-gradient(circle at 60% 40%, rgba(107, 139, 255, 0.55), transparent 70%);
  animation: app-blob-2 24s var(--ease-in-out) infinite;
}
.blob-amber {
  width: 34vw;
  height: 34vw;
  left: 30vw;
  bottom: -14vw;
  background: radial-gradient(circle at 50% 50%, rgba(242, 193, 78, 0.28), transparent 70%);
  animation: app-blob 28s var(--ease-in-out) infinite reverse;
}
.grid-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 46px 46px;
  mask-image: radial-gradient(ellipse 80% 60% at 50% 0%, #000 40%, transparent 80%);
  -webkit-mask-image: radial-gradient(ellipse 80% 60% at 50% 0%, #000 40%, transparent 80%);
}

/* ---------- 导航 ---------- */
.nav {
  position: sticky;
  top: 0;
  z-index: 10;
  background: rgba(8, 11, 20, 0.72);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.nav-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 32px;
  height: 64px;
  display: flex;
  align-items: center;
  gap: 40px;
}
.nav-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: var(--app-text);
  text-decoration: none;
  letter-spacing: -0.2px;
}
.logo-mark {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: var(--app-brand-gradient);
  color: #071018;
  box-shadow: 0 1px 0 0 rgba(255, 255, 255, 0.4) inset, 0 6px 18px -6px rgba(90, 208, 230, 0.6);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}
.nav-links {
  display: flex;
  gap: 28px;
  margin-right: auto;
}
.nav-link {
  font-size: 14px;
  font-weight: 500;
  color: var(--app-text-muted);
  text-decoration: none;
  transition: color 0.2s ease;
}
.nav-link:hover {
  color: var(--app-text);
}
.nav-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}
.nav-login {
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text);
  text-decoration: none;
}
.nav-signup {
  padding: 8px 18px;
  border-radius: 100px;
  background-image: var(--app-brand-gradient);
  color: #071018;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  box-shadow: 0 1px 0 0 rgba(255, 255, 255, 0.4) inset, 0 6px 18px -6px rgba(107, 139, 255, 0.55);
  transition: transform 0.15s ease, box-shadow 0.2s ease, filter 0.2s ease;
}
.nav-signup:hover {
  filter: brightness(1.08);
  box-shadow: 0 1px 0 0 rgba(255, 255, 255, 0.5) inset, 0 10px 24px -6px rgba(107, 139, 255, 0.7);
}

/* ---------- Hero ---------- */
.hero {
  position: relative;
  z-index: 1;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 80px 24px 120px;
}
.hero-title {
  max-width: 900px;
  font-size: clamp(40px, 6vw, 72px);
  line-height: 1.22;
  font-weight: 800;
  letter-spacing: -1.5px;
  color: var(--app-text);
  margin: 0 0 32px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  column-gap: 14px;
}

/* 标题内装饰元素 */
.deco {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  vertical-align: middle;
}
.deco-dot-yellow {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #fbbf24;
  box-shadow: 0 2px 8px rgba(251, 191, 36, 0.4);
}
.deco-arrow {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #16a34a;
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  box-shadow: 0 2px 10px rgba(22, 163, 74, 0.35);
}
.deco-pill {
  width: 56px;
}
.pill-track {
  display: inline-block;
  width: 56px;
  height: 26px;
  border-radius: 100px;
  background: linear-gradient(120deg, #22d3ee, #60a5fa);
  position: relative;
  box-shadow: 0 2px 10px rgba(34, 211, 238, 0.35);
}
.pill-knob {
  position: absolute;
  right: 3px;
  top: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}
.deco-emoji {
  font-size: 36px;
  filter: drop-shadow(0 4px 10px rgba(0, 0, 0, 0.12));
}

.hero-sub {
  max-width: 620px;
  font-size: 17px;
  line-height: 1.7;
  color: var(--app-text-secondary);
  margin: 0 0 40px;
}
.hero-cta {
  display: flex;
  justify-content: center;
}
.cta-btn {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 16px 36px;
  border-radius: 100px;
  background-image: var(--app-brand-gradient);
  color: #071018;
  font-size: 16px;
  font-weight: 600;
  text-decoration: none;
  box-shadow: 0 1px 0 0 rgba(255, 255, 255, 0.4) inset, 0 10px 28px -8px rgba(107, 139, 255, 0.6);
  transition: transform 0.15s ease, box-shadow 0.2s ease, filter 0.2s ease;
}
.cta-arrow {
  font-size: 18px;
  transition: transform 0.2s ease;
}
.cta-btn:hover {
  transform: translateY(-2px);
  filter: brightness(1.08);
  box-shadow: 0 1px 0 0 rgba(255, 255, 255, 0.5) inset, 0 16px 36px -8px rgba(107, 139, 255, 0.7);
}
.cta-btn:hover .cta-arrow {
  transform: translateX(4px);
}

/* 响应式 */
@media (max-width: 768px) {
  .nav-links {
    display: none;
  }
  .nav-inner {
    padding: 0 20px;
  }
  .hero {
    padding: 60px 20px 100px;
  }
  .hero-title {
    line-height: 1.3;
  }
}
</style>
