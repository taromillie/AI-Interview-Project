<template>
  <div class="auth-page">
    <!-- 左侧品牌区 -->
    <div class="auth-hero">
      <div class="hero-glow hero-glow-1"></div>
      <div class="hero-glow hero-glow-2"></div>
      <div class="hero-grid"></div>

      <div class="hero-content">
        <div class="hero-logo">
          <div class="logo-badge">
            <el-icon :size="20"><MagicStick /></el-icon>
          </div>
          <div>
            <div class="logo-name">AI 模拟面试官</div>
            <div class="logo-sub">AI Interview Coach</div>
          </div>
        </div>

        <h1 class="hero-title">让每一次模拟，<br />都逼近真实面试</h1>
        <p class="hero-desc">
          简历与 JD 智能匹配、面试官多轮动态追问、面试后自动复盘，
          从准备到入职一站式护航。
        </p>

        <ul class="hero-feats">
          <li v-for="f in features" :key="f" class="feat">
            <span class="feat-check"><el-icon :size="13"><Check /></el-icon></span>
            {{ f }}
          </li>
        </ul>
      </div>

      <div class="hero-footer">© 2026 AI 模拟面试官 · 你的专属面试教练</div>
    </div>

    <!-- 右侧表单区 -->
    <div class="auth-panel">
      <div class="panel-inner">
        <div class="panel-head">
          <div class="panel-title">{{ tab === 'login' ? '欢迎回来' : '创建你的账号' }}</div>
          <div class="panel-sub">
            {{ tab === 'login' ? '登录后继续你的面试之旅' : '注册即可开始第一次模拟面试' }}
          </div>
        </div>

        <div class="tab-switch">
          <div class="tab-pill" :class="{ right: tab === 'register' }"></div>
          <button type="button" class="tab-btn" :class="{ active: tab === 'login' }" @click="tab = 'login'">
            登录
          </button>
          <button type="button" class="tab-btn" :class="{ active: tab === 'register' }" @click="tab = 'register'">
            注册
          </button>
        </div>

        <!-- 登录 -->
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

        <!-- 注册 -->
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
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Check, Lock, Message, User } from '@element-plus/icons-vue'
import http from '@/api/http'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const tab = ref('login')
const loading = ref(false)
const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', email: '', password: '', confirmPassword: '' })

const features = ['简历 × JD 智能匹配诊断', 'AI 面试官多轮动态追问', '转行诊断 · 谈薪评估 · 能力画像', '每场面试结束自动生成复盘报告']

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
  min-height: 100vh;
  display: flex;
}

/* ---------- 左侧品牌区 ---------- */
.auth-hero {
  position: relative;
  flex: 1.15;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 44px 56px 32px;
  overflow: hidden;
  background: linear-gradient(160deg, #0b1220 0%, #101c33 55%, #1e1b4b 100%);
  color: #fff;
}
.hero-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.55;
  pointer-events: none;
}
.hero-glow-1 {
  width: 420px;
  height: 420px;
  background: #2563eb;
  top: -120px;
  right: -80px;
}
.hero-glow-2 {
  width: 380px;
  height: 380px;
  background: #7c3aed;
  bottom: -140px;
  left: -60px;
  opacity: 0.4;
}
.hero-grid {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(rgba(255, 255, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.045) 1px, transparent 1px);
  background-size: 42px 42px;
  mask-image: radial-gradient(ellipse at 30% 40%, #000 20%, transparent 75%);
  pointer-events: none;
}
.hero-content {
  position: relative;
  z-index: 1;
  max-width: 520px;
  margin: auto 0;
  animation: fadeUp 0.7s ease both;
}
@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.hero-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 40px;
}
.logo-badge {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.45);
}
.logo-name {
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.logo-sub {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.55);
  letter-spacing: 1px;
  margin-top: 1px;
}
.hero-title {
  font-size: 40px;
  line-height: 1.28;
  font-weight: 800;
  letter-spacing: 0.5px;
  margin-bottom: 18px;
}
.hero-desc {
  font-size: 14px;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.72);
  max-width: 420px;
  margin-bottom: 30px;
}
.hero-feats {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.feat {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
}
.feat-check {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(5, 150, 105, 0.25);
  border: 1px solid rgba(5, 150, 105, 0.6);
  color: #34d399;
  flex-shrink: 0;
}
.hero-footer {
  position: relative;
  z-index: 1;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

/* ---------- 右侧表单区 ---------- */
.auth-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 48px;
  background: #f8fafc;
}
.panel-inner {
  width: 100%;
  max-width: 400px;
  animation: fadeUp 0.7s 0.1s ease both;
}
.panel-head {
  margin-bottom: 24px;
}
.panel-title {
  font-size: 26px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 0.3px;
}
.panel-sub {
  margin-top: 6px;
  font-size: 13px;
  color: #64748b;
}
.tab-switch {
  position: relative;
  display: flex;
  gap: 4px;
  background: #eef2f7;
  border-radius: 12px;
  padding: 4px;
  margin-bottom: 24px;
}
.tab-pill {
  position: absolute;
  left: 4px;
  top: 4px;
  bottom: 4px;
  width: calc(50% - 4px);
  background: #fff;
  border-radius: 9px;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.08);
  transition: transform 0.25s var(--ease-smooth-out);
  z-index: 0;
}
.tab-pill.right {
  transform: translateX(100%);
}
.tab-btn {
  position: relative;
  z-index: 1;
  flex: 1;
  height: 38px;
  border: none;
  border-radius: 9px;
  background: transparent;
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  transition: transform 160ms var(--ease-out), background-color 0.2s ease, color 0.2s ease;
}
.tab-btn:active {
  transform: scale(0.96);
}
.tab-btn.active {
  background: transparent;
  color: #2563eb;
}
.panel-inner :deep(.el-input__wrapper) {
  border-radius: 12px;
  padding: 2px 14px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
  transition: box-shadow 0.2s ease;
}
.panel-inner :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #2563eb inset, 0 0 0 4px rgba(37, 99, 235, 0.1);
}
.panel-inner :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1.5px #2563eb inset, 0 0 0 4px rgba(37, 99, 235, 0.1);
}
.panel-inner :deep(.el-form-item) {
  margin-bottom: 20px;
}
.submit-btn {
  width: 100%;
  height: 46px;
  margin-top: 6px;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 2px;
  background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
  border: none;
  box-shadow: 0 6px 18px rgba(37, 99, 235, 0.35);
}
.submit-btn:active {
  transform: scale(0.98);
}
@media (hover: hover) and (pointer: fine) {
  .submit-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 22px rgba(37, 99, 235, 0.42);
  }
}

/* ---------- 响应式 ---------- */
@media (max-width: 900px) {
  .auth-hero {
    display: none;
  }
  .auth-panel {
    min-height: 100vh;
  }
}
</style>
