import request from './http'

export function createRealInterview(payload) {
  return request.post('/real-interview', payload)
}

export function listRealInterviews() {
  return request.get('/real-interview')
}

export function getRealInterview(id) {
  return request.get(`/real-interview/${id}`)
}

export function reviewRealInterview(id) {
  return request.post(`/real-interview/${id}/review`)
}

export function deleteRealInterview(id) {
  return request.delete(`/real-interview/${id}`)
}
