import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    profile: null,
  }),
  getters: {
    username: (state) => state.profile?.username || '用户',
  },
  actions: {
    setToken(token) {
      this.token = token
      localStorage.setItem('token', token)
    },
    setProfile(profile) {
      this.profile = profile
    },
    logout() {
      this.token = ''
      this.profile = null
      localStorage.removeItem('token')
    },
  },
})
