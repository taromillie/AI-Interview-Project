import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      { path: '', name: 'dashboard', component: () => import('@/views/Dashboard.vue') },
      { path: 'diagnosis', name: 'diagnosis', component: () => import('@/views/ResumeDiagnosis.vue') },
      { path: 'interview', name: 'interview', component: () => import('@/views/Interview.vue') },
      { path: 'history', name: 'history', component: () => import('@/views/InterviewHistory.vue') },
      { path: 'report/:id?', name: 'report', component: () => import('@/views/Report.vue') },
      { path: 'career', name: 'career', component: () => import('@/views/CareerDiagnosis.vue') },
      { path: 'salary', name: 'salary', component: () => import('@/views/SalarySim.vue') },
      { path: 'profile', name: 'profile', component: () => import('@/views/AbilityProfile.vue') },
      { path: 'questions', name: 'questions', component: () => import('@/views/QuestionBank.vue') },
      { path: 'providers', name: 'providers', component: () => import('@/views/ProviderConfig.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 登录守卫
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (!to.meta.public && !token) {
    return { name: 'login' }
  }
  if (to.name === 'login' && token) {
    return { name: 'dashboard' }
  }
})

export default router
