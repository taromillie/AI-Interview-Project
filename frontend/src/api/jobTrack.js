import http from './http'

export const APPLICATION_STATUS = {
  saved: { label: '稍后投', type: 'info' },
  applied: { label: '已投递', type: 'primary' },
  interviewing: { label: '面试中', type: 'warning' },
  offer: { label: '已获 Offer', type: 'success' },
  rejected: { label: '未通过', type: 'danger' },
}

export function getJobTrackSummary() {
  return http.get('/job-track/summary')
}

export function favoritePosition(positionId) {
  return http.post(`/job-track/positions/${positionId}/favorite`)
}

export function unfavoritePosition(positionId) {
  return http.delete(`/job-track/positions/${positionId}/favorite`)
}

export function setApplication(positionId, status, note = '') {
  return http.put(`/job-track/positions/${positionId}/application`, null, {
    params: { status, note },
  })
}

export function removeApplication(positionId) {
  return http.delete(`/job-track/positions/${positionId}/application`)
}
