<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="logo">
        <el-icon size="24"><MagicStick /></el-icon>
        <span>AI 面试官</span>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        background-color="#1f2d3d"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <span>工作台</span>
        </el-menu-item>
        <el-menu-item index="/diagnosis">
          <el-icon><Document /></el-icon>
          <span>简历 × JD 诊断</span>
        </el-menu-item>
        <el-menu-item index="/interview">
          <el-icon><Microphone /></el-icon>
          <span>模拟面试</span>
        </el-menu-item>
        <el-menu-item index="/career">
          <el-icon><Compass /></el-icon>
          <span>转行诊断</span>
        </el-menu-item>
        <el-menu-item index="/salary">
          <el-icon><Money /></el-icon>
          <span>谈薪评估</span>
        </el-menu-item>
        <el-menu-item index="/questions">
          <el-icon><Collection /></el-icon>
          <span>题库管理</span>
        </el-menu-item>
        <el-menu-item index="/providers">
          <el-icon><Setting /></el-icon>
          <span>模型配置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-title">{{ currentTitle }}</div>
        <el-dropdown @command="onCommand">
          <span class="user-chip">
            <el-icon><UserFilled /></el-icon>
            {{ userStore.username }}
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const titles = {
  '/': '工作台',
  '/diagnosis': '简历 × JD 智能匹配诊断',
  '/interview': '模拟面试',
  '/career': '转行诊断',
  '/salary': '谈薪评估',
  '/questions': '题库管理',
  '/providers': '模型配置',
}
const currentTitle = computed(() => titles[route.path] || 'AI 模拟面试官')

function onCommand(cmd) {
  if (cmd === 'logout') {
    userStore.logout()
    router.push({ name: 'login' })
  }
}
</script>

<style scoped>
.layout {
  height: 100vh;
}

.aside {
  background: #1f2d3d;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  padding: 18px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.aside :deep(.el-menu) {
  border-right: none;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}

.header-title {
  font-size: 16px;
  font-weight: 500;
}

.user-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #303133;
}

.main {
  background: #f5f7fa;
}
</style>
