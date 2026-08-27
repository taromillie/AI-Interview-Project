<template>
  <div class="login-page">
    <el-card class="login-card">
      <div class="brand">
        <el-icon :size="36" color="#409eff"><MagicStick /></el-icon>
        <h2>AI 模拟面试官</h2>
        <p>简历诊断 · 动态追问面试 · 职业规划</p>
      </div>

      <el-tabs v-model="tab">
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" @submit.prevent="onLogin">
            <el-form-item>
              <el-input v-model="loginForm.username" placeholder="用户名" :prefix-icon="User" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="loginForm.password" type="password" placeholder="密码" show-password :prefix-icon="Lock" />
            </el-form-item>
            <el-button type="primary" class="submit" :loading="loading" @click="onLogin">
              登录
            </el-button>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form :model="registerForm" @submit.prevent="onRegister">
            <el-form-item>
              <el-input v-model="registerForm.username" placeholder="用户名" :prefix-icon="User" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="registerForm.email" placeholder="邮箱（可选）" :prefix-icon="Message" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="registerForm.password" type="password" placeholder="密码（至少 6 位）" show-password :prefix-icon="Lock" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="registerForm.confirmPassword" type="password" placeholder="确认密码" show-password :prefix-icon="Lock" />
            </el-form-item>
            <el-button type="primary" class="submit" :loading="loading" @click="onRegister">
              注册并登录
            </el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'
import http from '@/api/http'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const tab = ref('login')
const loading = ref(false)
const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', email: '', password: '', confirmPassword: '' })

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
    router.push({ name: 'dashboard' })
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
    ElMessage.success('注册成功')
    router.push({ name: 'dashboard' })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1f2d3d 0%, #2c3e50 100%);
}

.login-card {
  width: 400px;
  padding: 12px 8px;
}

.brand {
  text-align: center;
  margin-bottom: 20px;
}

.brand h2 {
  margin: 8px 0 4px;
  color: #303133;
}

.brand p {
  color: #909399;
  font-size: 13px;
}

.submit {
  width: 100%;
}
</style>
