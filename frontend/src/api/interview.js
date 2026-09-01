import http from './http'
import { postSSE } from './sse'

export function createInterview(payload) {
  return http.post('/interviews', payload)
}

export function listInterviews() {
  return http.get('/interviews')
}

// 面试详情（完整问答流 + 复盘报告），用于历史复盘
export function getInterviewDetail(interviewId) {
  return http.get(`/interviews/${interviewId}`)
}

// 开始面试（SSE：preparing → question）
export function startInterview(interviewId, { onEvent, signal } = {}) {
  return postSSE(`/interviews/${interviewId}/start`, {}, { onEvent, signal })
}

// 提交回答（SSE：thinking → question / finished / error）
// requestId：断线重发幂等键，同一回答重发时复用，避免服务端重复记录
export function answerInterview(interviewId, content, { onEvent, signal, requestId } = {}) {
  return postSSE(
    `/interviews/${interviewId}/answer`,
    { content, request_id: requestId },
    { onEvent, signal }
  )
}

// 结束面试并生成报告
export function finishInterview(interviewId) {
  return http.post(`/interviews/${interviewId}/finish`)
}
