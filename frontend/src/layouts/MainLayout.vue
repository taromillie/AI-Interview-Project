<template>
  <el-container class="layout">
    <el-aside width="224px" class="aside">
      <div class="logo">
        <div class="logo-badge">
          <el-icon :size="19"><MagicStick /></el-icon>
        </div>
        <div>
          <div class="logo-name">AI 模拟面试官</div>
          <div class="logo-sub">Interview Coach</div>
        </div>
      </div>

      <el-menu
        :default-active="$route.path"
        router
        background-color="transparent"
        text-color="#94a3b8"
        active-text-color="#ffffff"
        class="side-menu"
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
        <el-menu-item index="/history">
          <el-icon><Tickets /></el-icon>
          <span>面试记录</span>
        </el-menu-item>
        <el-menu-item index="/career">
          <el-icon><Compass /></el-icon>
          <span>转行诊断</span>
        </el-menu-item>
        <el-menu-item index="/salary">
          <el-icon><Money /></el-icon>
          <span>谈薪评估</span>
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><TrendCharts /></el-icon>
          <span>能力画像</span>
        </el-menu-item>
        <el-menu-item index="/study-plan">
          <el-icon><Calendar /></el-icon>
          <span>备战日历</span>
        </el-menu-item>
        <el-menu-item index="/real-interview">
          <el-icon><EditPen /></el-icon>
          <span>真实面试复盘</span>
        </el-menu-item>
        <el-menu-item index="/offer">
          <el-icon><Trophy /></el-icon>
          <span>Offer 对比</span>
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

      <div class="aside-foot">AI Interview Coach v1.0</div>
    </el-aside>

    <el-container class="body">
      <el-header class="header">
        <div class="header-left">
          <div class="header-title">{{ currentTitle }}</div>
        </div>
        <el-dropdown @command="onCommand">
          <span class="user-chip">
            <span class="user-avatar">{{ avatarText }}</span>
            <span class="user-name">{{ userStore.username }}</span>
            <el-icon class="user-arrow"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout" divided>
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
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
  '/history': '面试记录',
  '/career': '转行诊断',
  '/salary': '谈薪评估',
  '/profile': '能力画像',
  '/study-plan': '备战日历',
  '/real-interview': '真实面试复盘',
  '/offer': 'Offer 对比',
  '/questions': '题库管理',
  '/providers': '模型配置',
}
const currentTitle = computed(() => titles[route.path] || 'AI 模拟面试官')
const avatarText = computed(() => (userStore.username || 'U').slice(0, 1).toUpperCase())

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

/* ---------- 侧边栏 ---------- */
.aside {
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #0b1220 0%, #111c33 60%, #171337 100%);
  overflow: hidden;
}
.logo {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 20px 18px 18px;
}
.logo-badge {
  width: 38px;
  height: 38px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.45);
}
.logo-name {
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.3px;
  line-height: 1.2;
}
.logo-sub {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.42);
  letter-spacing: 0.8px;
  margin-top: 2px;
}

.side-menu {
  flex: 1;
  border-right: none;
  padding: 6px 10px;
}
.side-menu :deep(.el-menu-item) {
  height: 44px;
  line-height: 44px;
  border-radius: 10px;
  margin-bottom: 3px;
  font-size: 14px;
  transition: background 0.2s, color 0.2s;
}
.side-menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.06);
  color: #e2e8f0;
}
.side-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(37, 99, 235, 0.95) 0%, rgba(99, 102, 241, 0.8) 100%);
  color: #fff;
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
}
.side-menu :deep(.el-menu-item .el-icon) {
  font-size: 17px;
}
.aside-foot {
  padding: 14px 20px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.3);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  letter-spacing: 0.4px;
}

/* ---------- 主体 ---------- */
.body {
  min-width: 0;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 62px;
  padding: 0 24px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid #e8edf5;
}
.header-title {
  font-size: 17px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: 0.2px;
}
.user-chip {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  padding: 5px 12px 5px 5px;
  border-radius: 999px;
  cursor: pointer;
  transition: background 0.2s;
}
.user-chip:hover {
  background: #f1f5f9;
}
.user-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
}
.user-name {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}
.user-arrow {
  color: #94a3b8;
  font-size: 12px;
}

.main {
  background: #f5f7fb;
  padding: 20px 24px;
  overflow-y: auto;
}
</style>
