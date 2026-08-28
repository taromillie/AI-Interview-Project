<template>
  <el-container class="layout">
    <el-aside :width="collapsed ? '64px' : '208px'" class="aside">
      <div class="logo" @click="collapsed = !collapsed">
        <div class="logo-badge">
          <el-icon :size="19"><MagicStick /></el-icon>
        </div>
        <div v-show="!collapsed" class="logo-text">
          <div class="logo-name">AI 面试官</div>
          <div class="logo-sub">Interview Coach</div>
        </div>
      </div>

      <el-menu
        :default-active="$route.path"
        :collapse="collapsed"
        :collapse-transition="false"
        router
        class="side-menu"
      >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <template #title>工作台</template>
        </el-menu-item>

        <div v-show="!collapsed" class="menu-group">面试实战</div>
        <el-menu-item index="/jobs">
          <el-icon><Grid /></el-icon>
          <template #title>岗位广场</template>
        </el-menu-item>
        <el-menu-item index="/diagnosis">
          <el-icon><Document /></el-icon>
          <template #title>简历 × JD 诊断</template>
        </el-menu-item>
        <el-menu-item index="/interview">
          <el-icon><Microphone /></el-icon>
          <template #title>模拟面试</template>
        </el-menu-item>
        <el-menu-item index="/real-interview">
          <el-icon><EditPen /></el-icon>
          <template #title>真实面试复盘</template>
        </el-menu-item>
        <el-menu-item index="/history">
          <el-icon><Tickets /></el-icon>
          <template #title>面试记录</template>
        </el-menu-item>

        <div v-show="!collapsed" class="menu-group">职业决策</div>
        <el-menu-item index="/career">
          <el-icon><Compass /></el-icon>
          <template #title>转行诊断</template>
        </el-menu-item>
        <el-menu-item index="/salary">
          <el-icon><Money /></el-icon>
          <template #title>谈薪评估</template>
        </el-menu-item>
        <el-menu-item index="/offer">
          <el-icon><Trophy /></el-icon>
          <template #title>Offer 对比</template>
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><TrendCharts /></el-icon>
          <template #title>能力画像</template>
        </el-menu-item>
        <el-menu-item index="/study-plan">
          <el-icon><Calendar /></el-icon>
          <template #title>备战日历</template>
        </el-menu-item>

        <div v-show="!collapsed" class="menu-group">系统设置</div>
        <el-menu-item index="/questions">
          <el-icon><Collection /></el-icon>
          <template #title>题库管理</template>
        </el-menu-item>
        <el-menu-item index="/providers">
          <el-icon><Setting /></el-icon>
          <template #title>模型配置</template>
        </el-menu-item>
      </el-menu>

      <div class="aside-foot" v-show="!collapsed">AI Interview Coach v1.1</div>
    </el-aside>

    <el-container class="body">
      <el-header class="header">
        <div class="header-left">
          <button class="fold-btn" @click="collapsed = !collapsed" title="收起/展开导航">
            <el-icon :size="18"><Expand v-if="collapsed" /><Fold v-else /></el-icon>
          </button>
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
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowDown,
  Calendar,
  Collection,
  Compass,
  Document,
  EditPen,
  Expand,
  Fold,
  Grid,
  HomeFilled,
  MagicStick,
  Microphone,
  Money,
  Setting,
  SwitchButton,
  Tickets,
  TrendCharts,
  Trophy,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const collapsed = ref(false)

const titles = {
  '/': '工作台',
  '/jobs': '岗位广场',
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

/* ---------- 侧边栏（弱化：浅色、窄栏、可折叠） ---------- */
.aside {
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-right: 1px solid #eef1f6;
  overflow: hidden;
  transition: width 0.28s var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 14px 14px;
  cursor: pointer;
  white-space: nowrap;
}
.logo-badge {
  width: 36px;
  height: 36px;
  border-radius: 11px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}
.logo-name {
  color: #0f172a;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.2;
}
.logo-sub {
  font-size: 10px;
  color: #94a3b8;
  letter-spacing: 0.6px;
  margin-top: 2px;
}

.side-menu {
  flex: 1;
  border-right: none;
  padding: 2px 8px 12px;
  overflow-y: auto;
  overflow-x: hidden;
}
.side-menu :deep(.el-menu) {
  border-right: none;
}
.menu-group {
  padding: 14px 10px 6px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1px;
  color: #a5b0c2;
  text-transform: uppercase;
  white-space: nowrap;
}
.side-menu :deep(.el-menu-item) {
  height: 42px;
  line-height: 42px;
  border-radius: 10px;
  margin-bottom: 2px;
  font-size: 13px;
  color: #64748b;
  transition: background 0.2s, color 0.2s;
}
.side-menu :deep(.el-menu-item:hover) {
  background: #f1f5f9;
  color: #0f172a;
}
.side-menu :deep(.el-menu-item.is-active) {
  background: rgba(37, 99, 235, 0.08);
  color: #2563eb;
  font-weight: 600;
}
.side-menu :deep(.el-menu-item .el-icon) {
  font-size: 16px;
}
.aside-foot {
  padding: 12px 16px;
  font-size: 10px;
  color: #b6c0d0;
  border-top: 1px solid #f1f4f9;
  letter-spacing: 0.4px;
  white-space: nowrap;
}

/* ---------- 主体 ---------- */
.body {
  min-width: 0;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 20px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid #eef1f6;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.fold-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
  color: #64748b;
  cursor: pointer;
  transition: background 0.2s, color 0.2s, transform 160ms var(--ease-out, cubic-bezier(0.22, 1, 0.36, 1));
}
.fold-btn:hover {
  background: #e2e8f0;
  color: #0f172a;
}
.fold-btn:active {
  transform: scale(0.94);
}
.header-title {
  font-size: 16px;
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
