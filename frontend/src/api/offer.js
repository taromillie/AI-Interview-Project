import request from './http'
import { getSSE } from './sse'

export function createOffer(payload) {
  return request.post('/offers', payload)
}

export function listOffers() {
  return request.get('/offers')
}

export function updateOffer(id, payload) {
  return request.put(`/offers/${id}`, payload)
}

export function deleteOffer(id) {
  return request.delete(`/offers/${id}`)
}

export function compareOffers(offerIds = []) {
  // 传空数组时后端默认对比全部 Offer（向后兼容）
  return request.post('/offers/compare', { offer_ids: offerIds })
}

export function listCompareHistory() {
  return request.get('/offers/compare/history')
}

export function getCompareHistory(id) {
  return request.get(`/offers/compare/history/${id}`)
}

export function deleteCompareHistory(id) {
  return request.delete(`/offers/compare/history/${id}`)
}

/**
 * SSE 流式拉取一条对比记录的 AI 分析文本（复用 api/sse.js 的通用实现）。
 * @param {number} recordId
 * @param {(chunk: string) => void} onChunk 每收到一块文本片段时回调
 */
export async function streamCompareAnalysis(recordId, onChunk) {
  await getSSE(`/offers/compare/history/${recordId}/stream`, {
    onEvent: (_event, payload) => {
      if (payload?.chunk) onChunk(payload.chunk)
    },
  })
}
