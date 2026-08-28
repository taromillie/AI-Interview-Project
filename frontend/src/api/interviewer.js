import http from './http'

// 面试官角色列表（interview_type: all/normal/switch/salary，可省略）
export function listInterviewers(interviewType) {
  return http.get('/interviewers', {
    params: interviewType && interviewType !== 'all' ? { interview_type: interviewType } : undefined,
  })
}

// 用户自建面试官角色
export function createInterviewer(payload) {
  return http.post('/interviewers', payload)
}

// 删除本人自建角色
export function deleteInterviewer(interviewerId) {
  return http.delete(`/interviewers/${interviewerId}`)
}
