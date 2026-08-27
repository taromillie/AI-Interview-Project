import http from './http'

// 能力画像（多场面试聚合）
export function getProfile() {
  return http.get('/profile')
}
