<template>
  <div class="layout">
    <!-- 全站共享液态极光背景 -->
    <div class="aurora" aria-hidden="true">
      <span class="blob blob-cyan"></span>
      <span class="blob blob-blue"></span>
      <span class="blob blob-amber"></span>
      <span class="grid-overlay"></span>
    </div>

    <header class="top-nav" :class="{ scrolled: scrolled }">
      <router-link to="/dashboard" class="wordmark">
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
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowDown } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const primaryLinks = [
  { path: '/dashboard', label: '首页' },
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

/* 顶栏滚动加深 */
const scrolled = ref(false)
function onScroll() {
  scrolled.value = window.scrollY > 8
}
onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', onScroll))
</script>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
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

/* ---------- 顶部导航 ---------- */
.top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 28px;
  height: 62px;
  padding: 0 clamp(1.5rem, 5vw, 3rem);
  background: rgba(8, 11, 20, 0.55);
  backdrop-filter: blur(20px) saturate(150%);
  -webkit-backdrop-filter: blur(20px) saturate(150%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  transition: background 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
}
.top-nav.scrolled {
  background: rgba(8, 11, 20, 0.78);
  border-bottom-color: rgba(255, 255, 255, 0.14);
  box-shadow: 0 8px 30px -14px rgba(0, 0, 0, 0.6);
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
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: var(--app-brand-gradient);
  color: #071018;
  font-size: 16px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 0 0 rgba(255, 255, 255, 0.4) inset, 0 6px 18px -6px rgba(90, 208, 230, 0.6);
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
  padding: 8px 14px;
  border-radius: 999px;
  font-size: 14px;
  color: var(--app-text-secondary);
  text-decoration: none;
  cursor: pointer;
  white-space: nowrap;
  border: 1px solid transparent;
  transition: color 160ms var(--ease-out), background-color 160ms var(--ease-out), border-color 160ms var(--ease-out);
}
@media (hover: hover) and (pointer: fine) {
  .nav-link:hover {
    color: var(--app-text);
    background: rgba(255, 255, 255, 0.06);
  }
}
.nav-link.active {
  color: var(--app-text);
  font-weight: 600;
  background: var(--app-brand-soft);
  border-color: rgba(90, 208, 230, 0.35);
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
  padding: 6px 12px 6px 6px;
  border-radius: 999px;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
  transition: background-color 160ms var(--ease-out), border-color 160ms var(--ease-out);
  outline: none;
}
@media (hover: hover) and (pointer: fine) {
  .user-chip:hover {
    background: rgba(255, 255, 255, 0.09);
    border-color: rgba(255, 255, 255, 0.2);
  }
}
.user-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--app-brand-gradient);
  color: #071018;
  font-size: 12px;
  font-weight: 700;
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
  position: relative;
  z-index: 1;
  flex: 1;
  width: 100%;
  max-width: 1180px;
  margin: 0 auto;
  padding: 28px clamp(1.5rem, 5vw, 3rem) 56px;
}

@media (max-width: 900px) {
  .nav-links {
    gap: 0;
  }
  .nav-link {
    padding: 8px 10px;
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
