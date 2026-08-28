<template>
  <div class="landing">
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
  min-height: 100vh;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: #0f172a;
}

/* ---------- 导航 ---------- */
.nav {
  position: sticky;
  top: 0;
  z-index: 10;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid #f1f5f9;
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
  color: #0f172a;
  text-decoration: none;
  letter-spacing: -0.2px;
}
.logo-mark {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: #0f172a;
  color: #fff;
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
  color: #64748b;
  text-decoration: none;
  transition: color 0.2s ease;
}
.nav-link:hover {
  color: #0f172a;
}
.nav-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}
.nav-login {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  text-decoration: none;
}
.nav-signup {
  padding: 8px 18px;
  border-radius: 100px;
  background: #0f172a;
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  transition: transform 0.15s ease, box-shadow 0.2s ease;
}
.nav-signup:hover {
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.25);
}

/* ---------- Hero ---------- */
.hero {
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
  color: #0f172a;
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
  color: #64748b;
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
  background: #0f172a;
  color: #ffffff;
  font-size: 16px;
  font-weight: 600;
  text-decoration: none;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.28);
  transition: transform 0.15s ease, box-shadow 0.2s ease;
}
.cta-arrow {
  font-size: 18px;
  transition: transform 0.2s ease;
}
.cta-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.35);
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
