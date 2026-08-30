import request from './http'

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
 * SSE 流式拉取一条对比记录的 AI 分析文本。
 * @param {number} recordId
 * @param {(chunk: string) => void} onChunk 每收到一块文本片段时回调
 */
export async function streamCompareAnalysis(recordId, onChunk) {
  const token = localStorage.getItem('token')
  const resp = await fetch(`/api/offers/compare/history/${recordId}/stream`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!resp.ok || !resp.body) {
    throw new Error(`AI 分析流式接口异常（${resp.status}）`)
  }
  const reader = resp.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buf = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    let idx
    while ((idx = buf.indexOf('\n\n')) >= 0) {
      const raw = buf.slice(0, idx)
      buf = buf.slice(idx + 2)
      const line = raw.split('\n').find((l) => l.startsWith('data: '))
      if (!line) continue
      const payload = JSON.parse(line.slice(6))
      if (payload.chunk) onChunk(payload.chunk)
    }
  }
}
