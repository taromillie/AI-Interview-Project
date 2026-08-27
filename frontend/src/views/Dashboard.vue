<template>
  <div>
    <el-card class="welcome">
      <h2>你好，{{ userStore.username }} 👋</h2>
      <p>AI 求职伙伴已就绪：诊断差距 → 定向备战 → 模拟面试 → 复盘提升。</p>
    </el-card>

    <el-row :gutter="16" class="cards">
      <el-col v-for="card in cards" :key="card.path" :xs="24" :sm="12" :md="8">
        <el-card class="feature-card" shadow="hover" @click="go(card.path)">
          <el-icon :size="28" :color="card.color">
            <component :is="card.icon" />
          </el-icon>
          <h3>{{ card.title }}</h3>
          <p>{{ card.desc }}</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const cards = [
  { path: '/diagnosis', title: '简历 × JD 诊断', desc: '上传简历 + 粘贴 JD，30 秒定位差距与优化方向', icon: 'Document', color: '#409eff' },
  { path: '/interview', title: '模拟面试', desc: '有边界的 AI 面试官，基于回答动态追问', icon: 'Microphone', color: '#67c23a' },
  { path: '/career', title: '转行诊断', desc: '双岗位能力对比，可迁移技能图谱', icon: 'Compass', color: '#e6a23c' },
  { path: '/salary', title: '谈薪评估', desc: '薪资区间参考与谈薪话术演练', icon: 'Money', color: '#f56c6c' },
  { path: '/questions', title: '题库管理', desc: '知识原子维护与发布', icon: 'Collection', color: '#909399' },
  { path: '/providers', title: '模型配置', desc: '配置你的 LLM API Key（多供应商）', icon: 'Setting', color: '#7b68ee' },
]

function go(path) {
  router.push(path)
}
</script>

<style scoped>
.welcome {
  margin-bottom: 16px;
}

.welcome p {
  color: #909399;
  margin-top: 8px;
}

.cards {
  margin-top: 8px;
}

.feature-card {
  margin-bottom: 16px;
  cursor: pointer;
  transition: transform 0.2s;
}

.feature-card:hover {
  transform: translateY(-4px);
}

.feature-card h3 {
  margin: 12px 0 6px;
  font-size: 16px;
}

.feature-card p {
  color: #909399;
  font-size: 13px;
  line-height: 1.5;
}
</style>
