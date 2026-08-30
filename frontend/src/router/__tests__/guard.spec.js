import { beforeEach, describe, expect, it } from 'vitest'
import router from '@/router'

const name = () => router.currentRoute.value.name

beforeEach(async () => {
  localStorage.clear()
  // 回到初始公开页，避免跨测试残留导航
  await router.replace('/')
  await router.isReady()
})

describe('路由登录守卫', () => {
  it('未登录访问受保护路由 → 重定向登录页', async () => {
    await router.push('/dashboard')
    await router.isReady()
    expect(name()).toBe('login')
  })

  it('未登录访问公开路由放行', async () => {
    await router.push('/login')
    await router.isReady()
    expect(name()).toBe('login')
  })

  it('已登录访问登录页 → 重定向工作台', async () => {
    localStorage.setItem('token', 'mock-token')
    await router.push('/login')
    await router.isReady()
    expect(name()).toBe('dashboard')
  })

  it('已登录访问受保护路由放行', async () => {
    localStorage.setItem('token', 'mock-token')
    await router.push('/history')
    await router.isReady()
    expect(name()).toBe('history')
  })
})
