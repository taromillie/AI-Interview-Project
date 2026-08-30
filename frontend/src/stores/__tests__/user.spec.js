import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useUserStore } from '@/stores/user'

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
})

describe('用户 store', () => {
  it('初始从 localStorage 恢复 token', () => {
    localStorage.setItem('token', 'cached-token')
    const store = useUserStore()
    expect(store.token).toBe('cached-token')
  })

  it('setToken 写入状态并持久化', () => {
    const store = useUserStore()
    store.setToken('new-token')
    expect(store.token).toBe('new-token')
    expect(localStorage.getItem('token')).toBe('new-token')
  })

  it('setProfile 后 username 取用户名', () => {
    const store = useUserStore()
    store.setProfile({ username: '面试者', email: 'a@b.com' })
    expect(store.username).toBe('面试者')
  })

  it('logout 清空状态与本地存储', () => {
    localStorage.setItem('token', 't')
    localStorage.setItem('profile', JSON.stringify({ username: 'u' }))
    const store = useUserStore()
    store.setToken('t')
    store.setProfile({ username: 'u' })
    store.logout()
    expect(store.token).toBe('')
    expect(store.username).toBe('用户') // 未登录时回退默认名
    expect(localStorage.getItem('token')).toBeNull()
  })
})
