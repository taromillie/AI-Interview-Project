<template>
  <div class="auth-page">
    <!-- 动态极光背景 -->
    <div class="aurora" aria-hidden="true">
      <span class="blob blob-1"></span>
      <span class="blob blob-2"></span>
      <span class="blob blob-3"></span>
      <span class="grid-overlay"></span>
    </div>

    <div class="auth-shell iv-glass-strong iv-rise">
      <!-- 左侧品牌展示 -->
      <aside class="brand-side">
        <a class="brand-logo" href="/">
          <span class="logo-mark">✦</span>
          AI Interview Coach
        </a>

        <div class="brand-orb-wrap">
          <span class="orb-ring"></span>
          <span class="orb-ring ring2"></span>
          <span class="orb"></span>
        </div>

        <h2 class="brand-title">把每一次开口<br />练到从容不迫</h2>
        <p class="brand-sub">拟真语音模拟、多维实时评测、秒级复盘报告，陪你稳稳拿下下一场面试。</p>

        <div class="brand-quote iv-glass">
          <p>“连续练了两周，真实面试时明显更稳、思路更清晰。”</p>
          <div class="quote-by">
            <span class="quote-avatar">L</span>
            <span>Leo · 前端工程师</span>
          </div>
        </div>
      </aside>

      <!-- 右侧表单 -->
      <section class="form-side">
        <div class="panel-head">
          <div class="panel-title">{{ tab === 'login' ? '欢迎回来' : '创建账号' }}</div>
          <div class="panel-sub">
            {{ tab === 'login' ? '登录后继续你的面试之旅' : '注册即可开启第一次模拟面试' }}
          </div>
        </div>

        <!-- Tab 切换 -->
        <div class="tab-switch">
          <div class="tab-pill" :class="{ right: tab === 'register' }"></div>
          <button type="button" class="tab-btn" :class="{ active: tab === 'login' }" @click="switchTab('login')">
            登录
          </button>
          <button type="button" class="tab-btn" :class="{ active: tab === 'register' }" @click="switchTab('register')">
            注册
          </button>
        </div>

        <!-- 登录表单 -->
        <el-form v-if="tab === 'login'" :model="loginForm" @submit.prevent="onLogin">
          <el-form-item>
            <el-input v-model="loginForm.username" size="large" placeholder="用户名" :prefix-icon="User" />
          </el-form-item>
          <el-form-item>
            <el-input
              v-model="loginForm.password"
              size="large"
              type="password"
              placeholder="密码"
              show-password
              :prefix-icon="Lock"
              @keydown.enter.prevent="onLogin"
            />
          </el-form-item>
          <button type="button" class="submit-btn" :class="{ loading }" :disabled="loading" @click="onLogin">
            <span v-if="loading" class="spinner"></span>
            {{ loading ? '登录中…' : '登 录' }}
          </button>
        </el-form>

        <!-- 注册表单 -->
        <el-form v-else :model="registerForm" @submit.prevent="onRegister">
          <el-form-item>
            <el-input v-model="registerForm.username" size="large" placeholder="用户名" :prefix-icon="User" />
          </el-form-item>
          <el-form-item>
            <el-input v-model="registerForm.email" size="large" placeholder="邮箱（可选）" :prefix-icon="Message" />
          </el-form-item>
          <el-form-item>
            <el-input
              v-model="registerForm.password"
              size="large"
              type="password"
              placeholder="密码（至少 6 位）"
              show-password
              :prefix-icon="Lock"
            />
          </el-form-item>
          <el-form-item>
            <el-input
              v-model="registerForm.confirmPassword"
              size="large"
              type="password"
              placeholder="确认密码"
              show-password
              :prefix-icon="Lock"
              @keydown.enter.prevent="onRegister"
            />
          </el-form-item>
          <button type="button" class="submit-btn" :class="{ loading }" :disabled="loading" @click="onRegister">
            <span v-if="loading" class="spinner"></span>
            {{ loading ? '注册中…' : '注册并登录' }}
          </button>
        </el-form>

        <p class="form-foot">
          继续即代表你同意我们的服务条款与隐私政策
        </p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, Message, User } from '@element-plus/icons-vue'
import http from '@/api/http'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const tab = ref(route.query.tab === 'register' ? 'register' : 'login')
const loading = ref(false)
const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', email: '', password: '', confirmPassword: '' })

function switchTab(name) {
  tab.value = name
  router.replace({ query: { tab: name } })
}

async function onLogin() {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const data = await http.post('/auth/login', loginForm)
    userStore.setToken(data.access_token)
    const me = await http.get('/auth/me')
    userStore.setProfile(me)
    ElMessage.success('欢迎回来，' + me.username)
    router.push({ name: 'dashboard' })
  } catch (e) {
    ElMessage.error(e.message || '登录失败')
  } finally {
    loading.value = false
  }
}

async function onRegister() {
  if (!registerForm.username || registerForm.password.length < 6) {
    ElMessage.warning('用户名必填，密码至少 6 位')
    return
  }
  if (registerForm.password !== registerForm.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  loading.value = true
  try {
    const payload = {
      username: registerForm.username,
      password: registerForm.password,
      email: registerForm.email || undefined,
    }
    const data = await http.post('/auth/register', payload)
    userStore.setToken(data.access_token)
    const me = await http.get('/auth/me')
    userStore.setProfile(me)
    ElMessage.success('注册成功，欢迎加入')
    router.push({ name: 'dashboard' })
  } catch (e) {
    ElMessage.error(e.message || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  overflow: hidden;
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

/* 极光背景 */
.aurora {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  background:
    radial-gradient(120% 80% at 80% -10%, oklch(0.2 0.05 250 / 0.6), transparent 60%),
    var(--iv-bg-deep);
}
.blob { position: absolute; border-radius: 50%; filter: blur(70px); opacity: 0.5; will-change: transform; }
.blob-1 { width: 40vw; height: 40vw; left: -6vw; top: -8vw; background: radial-gradient(circle, var(--iv-blue), transparent 70%); animation: blob 20s ease-in-out infinite; }
.blob-2 { width: 38vw; height: 38vw; right: -8vw; top: 4vw; background: radial-gradient(circle, var(--iv-cyan), transparent 70%); animation: blob2 24s ease-in-out infinite; }
.blob-3 { width: 30vw; height: 30vw; left: 34vw; bottom: -12vw; background: radial-gradient(circle, var(--iv-amber), transparent 72%); opacity: 0.3; animation: blob 28s ease-in-out infinite reverse; }
.grid-overlay {
  position: absolute; inset: 0;
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

/* 玻璃通用 */
.iv-glass {
  background: linear-gradient(135deg, oklch(1 0 0 / 0.12), oklch(1 0 0 / 0.04));
  backdrop-filter: blur(24px) saturate(150%);
  -webkit-backdrop-filter: blur(24px) saturate(150%);
  border: 1px solid oklch(1 0 0 / 0.14);
  box-shadow: 0 1px 0 0 oklch(1 0 0 / 0.2) inset;
}
.iv-glass-strong {
  background: linear-gradient(135deg, oklch(1 0 0 / 0.14), oklch(1 0 0 / 0.05));
  backdrop-filter: blur(40px) saturate(160%);
  -webkit-backdrop-filter: blur(40px) saturate(160%);
  border: 1px solid oklch(1 0 0 / 0.2);
  box-shadow:
    0 1px 0 0 oklch(1 0 0 / 0.28) inset,
    0 40px 90px -30px oklch(0 0 0 / 0.7);
}
.iv-rise { opacity: 0; animation: rise 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards; }
@keyframes rise {
  from { opacity: 0; transform: translateY(18px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 外壳分屏 */
.auth-shell {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 880px;
  border-radius: 28px;
  overflow: hidden;
  display: grid;
  grid-template-columns: 1fr 1fr;
}

/* 左侧品牌 */
.brand-side {
  position: relative;
  padding: 44px 40px;
  display: flex;
  flex-direction: column;
  background: linear-gradient(160deg, oklch(0.3 0.08 250 / 0.5), oklch(0.16 0.04 260 / 0.2));
  border-right: 1px solid oklch(1 0 0 / 0.1);
}
.brand-logo {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 15px;
  font-weight: 700;
  color: var(--iv-text);
  text-decoration: none;
}
.logo-mark {
  width: 28px; height: 28px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--iv-cyan), var(--iv-blue));
  color: oklch(0.14 0.02 260);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  box-shadow: 0 4px 14px -4px var(--iv-blue);
}
.brand-orb-wrap {
  position: relative;
  width: 110px;
  height: 110px;
  margin: 32px 0 26px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.orb {
  width: 78px; height: 78px;
  border-radius: 50%;
  background: conic-gradient(from 0deg, var(--iv-cyan), var(--iv-blue), var(--iv-amber), var(--iv-cyan));
  box-shadow: 0 0 40px -6px var(--iv-blue), 0 0 0 1px oklch(1 0 0 / 0.2) inset;
  animation: orbBreathe 3.5s ease-in-out infinite;
}
@keyframes orbBreathe {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.07); }
}
.orb-ring {
  position: absolute;
  inset: 16px;
  border-radius: 50%;
  border: 1px solid var(--iv-cyan);
  animation: ring 3s ease-out infinite;
}
.orb-ring.ring2 { animation-delay: 1.5s; }
@keyframes ring {
  0% { transform: scale(0.7); opacity: 0.7; }
  100% { transform: scale(1.5); opacity: 0; }
}
.brand-title {
  font-size: 24px;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: -0.3px;
  margin-bottom: 12px;
}
.brand-sub {
  font-size: 14px;
  line-height: 1.7;
  color: var(--iv-muted);
  margin-bottom: auto;
}
.brand-quote {
  border-radius: 16px;
  padding: 16px 18px;
  margin-top: 28px;
}
.brand-quote p {
  font-size: 13.5px;
  line-height: 1.6;
  color: var(--iv-text);
  margin-bottom: 12px;
}
.quote-by {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
  color: var(--iv-muted);
}
.quote-avatar {
  width: 26px; height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: oklch(0.14 0.02 260);
  background: linear-gradient(135deg, var(--iv-cyan), var(--iv-blue));
}

/* 右侧表单 */
.form-side {
  padding: 48px 44px;
  display: flex;
  flex-direction: column;
}
.panel-head { margin-bottom: 26px; }
.panel-title {
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.2px;
}
.panel-sub {
  margin-top: 7px;
  font-size: 13.5px;
  color: var(--iv-muted);
}

/* Tab 切换 */
.tab-switch {
  position: relative;
  display: flex;
  gap: 4px;
  background: oklch(1 0 0 / 0.06);
  border: 1px solid oklch(1 0 0 / 0.1);
  border-radius: 14px;
  padding: 4px;
  margin-bottom: 24px;
}
.tab-pill {
  position: absolute;
  left: 4px; top: 4px; bottom: 4px;
  width: calc(50% - 4px);
  background: linear-gradient(135deg, var(--iv-cyan), var(--iv-blue));
  border-radius: 11px;
  box-shadow: 0 4px 14px -4px var(--iv-blue);
  transition: transform 0.35s cubic-bezier(0.34, 1.4, 0.64, 1);
  z-index: 0;
}
.tab-pill.right { transform: translateX(100%); }
.tab-btn {
  position: relative;
  z-index: 1;
  flex: 1;
  height: 40px;
  border: none;
  border-radius: 11px;
  background: transparent;
  font-size: 14px;
  font-weight: 600;
  color: var(--iv-muted);
  cursor: pointer;
  transition: color 0.25s ease;
}
.tab-btn.active { color: oklch(0.14 0.02 260); }

/* Element Plus 输入框玻璃化 */
.form-side :deep(.el-form-item) { margin-bottom: 18px; }
.form-side :deep(.el-input__wrapper) {
  border-radius: 12px;
  padding: 4px 14px;
  background: oklch(1 0 0 / 0.06);
  box-shadow: 0 0 0 1px oklch(1 0 0 / 0.14) inset;
  transition: box-shadow 0.2s ease, background 0.2s ease;
}
.form-side :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px oklch(1 0 0 / 0.24) inset;
}
.form-side :deep(.el-input__wrapper.is-focus) {
  background: oklch(1 0 0 / 0.09);
  box-shadow:
    0 0 0 1.5px color-mix(in oklch, var(--iv-cyan) 55%, transparent) inset,
    0 0 0 4px color-mix(in oklch, var(--iv-cyan) 18%, transparent);
}
.form-side :deep(.el-input__inner) {
  color: var(--iv-text);
  height: 42px;
}
.form-side :deep(.el-input__inner::placeholder) { color: var(--iv-muted); }
.form-side :deep(.el-input__prefix),
.form-side :deep(.el-input__suffix) { color: var(--iv-muted); }

/* 提交按钮 */
.submit-btn {
  width: 100%;
  height: 48px;
  margin-top: 8px;
  border: none;
  border-radius: 14px;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 1px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: oklch(0.14 0.02 260);
  background: linear-gradient(135deg, var(--iv-cyan), var(--iv-blue));
  box-shadow:
    0 1px 0 0 oklch(1 0 0 / 0.45) inset,
    0 10px 28px -8px color-mix(in oklch, var(--iv-blue) 60%, transparent);
  transition: transform 0.15s ease, filter 0.2s ease, box-shadow 0.2s ease;
}
.submit-btn:hover:not(:disabled) { transform: translateY(-2px); filter: brightness(1.06); }
.submit-btn:active:not(:disabled) { transform: scale(0.98); }
.submit-btn:disabled { cursor: default; opacity: 0.85; }
.spinner {
  width: 16px; height: 16px;
  border-radius: 50%;
  border: 2px solid oklch(0.14 0.02 260 / 0.35);
  border-top-color: oklch(0.14 0.02 260);
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.form-foot {
  margin-top: 20px;
  text-align: center;
  font-size: 12px;
  color: var(--iv-muted);
}

/* 响应式 */
@media (max-width: 760px) {
  .auth-shell { grid-template-columns: 1fr; max-width: 440px; }
  .brand-side { display: none; }
  .form-side { padding: 40px 30px; }
}

@media (prefers-reduced-motion: reduce) {
  .blob, .orb, .orb-ring, .iv-rise { animation: none; }
  .iv-rise { opacity: 1; }
}
</style>
