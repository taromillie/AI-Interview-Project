import http from './http'
import { postSSE } from './sse'

export function createInterview(payload) {
  return http.post('/interviews', payload)
}

export function listInterviews() {
  return http.get('/interviews')
}

// 开始面试（SSE：preparing → question）
export function startInterview(interviewId, { onEvent, signal } = {}) {
  return postSSE(`/interviews/${interviewId}/start`, {}, { onEvent, signal })
}

// 提交回答（SSE：thinking → question / finished / error）
export function answerInterview(interviewId, content, { onEvent, signal } = {}) {
  return postSSE(`/interviews/${interviewId}/answer`, { content }, { onEvent, signal })
}

// 结束面试并生成报告
export function finishInterview(interviewId) {
  return http.post(`/interviews/${interviewId}/finish`)
}
