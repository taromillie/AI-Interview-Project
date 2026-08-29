<template>
  <div class="auth-page">
    <!-- 液态极光背景 -->
    <div class="aurora" aria-hidden="true">
      <span class="blob blob-cyan"></span>
      <span class="blob blob-blue"></span>
      <span class="blob blob-amber"></span>
      <span class="grid-overlay"></span>
    </div>

    <div class="auth-wrap">
      <!-- Logo -->
      <div class="auth-logo">
        <div class="logo-badge">
          <el-icon :size="18"><MagicStick /></el-icon>
        </div>
        <span class="logo-name">AI 模拟面试官</span>
      </div>

      <div class="panel-card">
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
          <el-button type="primary" size="large" class="submit-btn" :loading="loading" @click="onLogin">
            登 录
          </el-button>
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
            />
          </el-form-item>
          <el-button type="primary" size="large" class="submit-btn" :loading="loading" @click="onRegister">
            注册并登录
          </el-button>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, MagicStick, Message, User } from '@element-plus/icons-vue'
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
  background: linear-gradient(180deg, #080b14 0%, #05070e 100%);
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

.auth-wrap {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
}

/* Logo */
.auth-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 28px;
}
.logo-badge {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--app-brand-gradient);
  color: #071018;
  box-shadow: 0 1px 0 0 rgba(255, 255, 255, 0.4) inset, 0 6px 18px -6px rgba(90, 208, 230, 0.6);
}
.logo-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--app-text);
  letter-spacing: 0.3px;
}

/* 表单卡片 - 玻璃拟态 */
.panel-card {
  width: 100%;
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: 28px;
  padding: 40px 36px;
  box-shadow: var(--glass-highlight), var(--glass-shadow);
  animation: fadeUp 0.5s ease both;
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}

.panel-head {
  margin-bottom: 28px;
  text-align: center;
}
.panel-title {
  font-size: 24px;
  font-weight: 800;
  color: var(--app-text);
  letter-spacing: -0.2px;
}
.panel-sub {
  margin-top: 6px;
  font-size: 13px;
  color: var(--app-text-secondary);
}

/* Tab 切换 */
.tab-switch {
  position: relative;
  display: flex;
  gap: 4px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  padding: 4px;
  margin-bottom: 24px;
}
.tab-pill {
  position: absolute;
  left: 4px; top: 4px; bottom: 4px;
  width: calc(50% - 4px);
  background: var(--glass-bg-strong);
  border-radius: 11px;
  box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.2);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 0;
}
.tab-pill.right {
  transform: translateX(100%);
}
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
  color: var(--app-text-muted);
  cursor: pointer;
  transition: color 0.25s ease;
}
.tab-btn.active {
  color: var(--app-text);
}

/* 输入框 */
.panel-card :deep(.el-input__wrapper) {
  border-radius: 14px;
  padding: 2px 16px;
}

/* 提交按钮 - 青蓝渐变 */
.submit-btn {
  width: 100%;
  height: 48px;
  margin-top: 8px;
  border-radius: 14px;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 1px;
  background-image: var(--app-brand-gradient);
  border: none;
  color: #071018;
  box-shadow: 0 1px 0 0 rgba(255, 255, 255, 0.4) inset, 0 10px 28px -10px rgba(107, 139, 255, 0.6);
  transition: transform 0.15s ease, box-shadow 0.2s ease, filter 0.2s ease;
}
.submit-btn:active {
  transform: scale(0.97);
}
@media (hover: hover) and (pointer: fine) {
  .submit-btn:hover {
    filter: brightness(1.08);
    box-shadow: 0 1px 0 0 rgba(255, 255, 255, 0.5) inset, 0 16px 38px -10px rgba(107, 139, 255, 0.7);
  }
}
</style>
