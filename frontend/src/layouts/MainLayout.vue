<template>
  <div class="layout">
    <header class="top-nav">
      <router-link to="/" class="wordmark">
        <span class="wordmark-mark">M</span>
        <span class="wordmark-text">AI 面试官</span>
      </router-link>

      <nav class="nav-links">
        <router-link
          v-for="item in primaryLinks"
          :key="item.path"
          :to="item.path"
          class="nav-link"
          :class="{ active: isActive(item) }"
        >
          {{ item.label }}
        </router-link>

        <el-dropdown trigger="hover" class="more-dropdown">
          <span class="nav-link" :class="{ active: isMoreActive }">
            更多功能
            <el-icon :size="12"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="item in moreLinks"
                :key="item.path"
                @click="go(item.path)"
              >
                {{ item.label }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </nav>

      <div class="nav-right">
        <el-dropdown trigger="click">
          <span class="user-chip">
            <span class="user-avatar">{{ avatarText }}</span>
            <span class="user-name">{{ userStore.username || '未登录' }}</span>
            <el-icon :size="12"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="go('/profile')">能力画像</el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <main class="layout-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowDown } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const primaryLinks = [
  { path: '/', label: '首页' },
  { path: '/jobs', label: '岗位广场' },
  { path: '/interview', label: '模拟面试' },
  { path: '/history', label: '面试记录' },
  { path: '/diagnosis', label: '简历诊断' },
]

const moreLinks = [
  { path: '/real-interview', label: '真实面试复盘' },
  { path: '/career', label: '转行诊断' },
  { path: '/salary', label: '谈薪评估' },
  { path: '/offer', label: 'Offer 对比' },
  { path: '/profile', label: '能力画像' },
  { path: '/study-plan', label: '备战日历' },
  { path: '/questions', label: '题库管理' },
  { path: '/providers', label: '模型配置' },
]

const isMoreActive = computed(() =>
  moreLinks.some((l) => route.path.startsWith(l.path))
)

function isActive(item) {
  if (item.path === '/') return route.path === '/'
  return route.path.startsWith(item.path)
}

function go(path) {
  router.push(path)
}

const avatarText = computed(() => {
  const name = userStore.username || '用'
  return name.slice(0, 1)
})

function handleLogout() {
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ---------- 顶部导航 ---------- */
.top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 28px;
  height: 60px;
  padding: 0 clamp(1.5rem, 5vw, 3rem);
  background: rgba(247, 247, 245, 0.86);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--app-border);
}

.wordmark {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: var(--app-text);
  flex-shrink: 0;
}
.wordmark-mark {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  background: var(--app-brand);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  letter-spacing: 0;
}
.wordmark-text {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.2px;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.nav-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 8px 13px;
  border-radius: 8px;
  font-size: 14px;
  color: var(--app-text-secondary);
  text-decoration: none;
  cursor: pointer;
  white-space: nowrap;
  transition: color 160ms var(--ease-out), background-color 160ms var(--ease-out);
}
@media (hover: hover) and (pointer: fine) {
  .nav-link:hover {
    color: var(--app-text);
    background: var(--app-brand-soft);
  }
}
.nav-link.active {
  color: var(--app-text);
  font-weight: 600;
  background: var(--app-brand-soft);
}

.more-dropdown {
  outline: none;
}

.nav-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.user-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  cursor: pointer;
  transition: background-color 160ms var(--ease-out);
  outline: none;
}
@media (hover: hover) and (pointer: fine) {
  .user-chip:hover {
    background: var(--app-brand-soft);
  }
}
.user-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--app-brand);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}
.user-name {
  font-size: 13px;
  color: var(--app-text);
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ---------- 内容区 ---------- */
.layout-main {
  flex: 1;
  width: 100%;
  max-width: 1180px;
  margin: 0 auto;
  padding: 28px clamp(1.5rem, 5vw, 3rem) 56px;
}

/* 窄屏：收起次级导航与用户名 */
@media (max-width: 900px) {
  .nav-links {
    gap: 0;
  }
  .nav-link {
    padding: 8px 9px;
    font-size: 13px;
  }
  .user-name {
    display: none;
  }
}
@media (max-width: 720px) {
  .wordmark-text {
    display: none;
  }
  .nav-link:nth-child(n + 3) {
    display: none;
  }
}
</style>
