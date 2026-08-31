// SSE 客户端：EventSource 不支持 POST 与自定义 Header，统一用 fetch + ReadableStream 解析。
// 用法：
//   await postSSE('/interviews/1/start', {}, { onEvent: (event, data) => {} })
//   await getSSE('/offers/compare/history/1/stream', { onEvent: (event, data) => {} })
// 两套实现（POST / GET）共用 readSSE 解析器，避免行为分叉。

async function readSSE(resp, onEvent) {
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  const splitter = /\r?\n\r?\n/

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let match = buffer.match(splitter)
    while (match) {
      const block = buffer.slice(0, match.index)
      buffer = buffer.slice(match.index + match[0].length)

      let event = 'message'
      let data = null
      for (const line of block.split(/\r?\n/)) {
        if (line.startsWith('event: ')) event = line.slice(7).trim()
        else if (line.startsWith('data: ')) data = line.slice(6).trim()
      }
      if (data !== null) {
        let payload = data
        try {
          payload = JSON.parse(data)
        } catch {
          /* 保持原始字符串 */
        }
        if (event === 'error') {
          throw new Error(payload?.message || '服务异常')
        }
        onEvent?.(event, payload)
      }
      match = buffer.match(splitter)
    }
  }
}

async function authHeaders() {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function postSSE(url, body = {}, { onEvent, signal } = {}) {
  const resp = await fetch(`/api${url}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(await authHeaders()),
    },
    body: JSON.stringify(body),
    signal,
  })

  if (!resp.ok) {
    let detail = `请求失败（${resp.status}）`
    try {
      const data = await resp.json()
      detail = data.detail || detail
    } catch {
      /* 保持默认错误信息 */
    }
    throw new Error(detail)
  }

  await readSSE(resp, onEvent)
}

export async function getSSE(url, { onEvent, signal } = {}) {
  const resp = await fetch(`/api${url}`, {
    headers: await authHeaders(),
    signal,
  })

  if (!resp.ok) {
    let detail = `请求失败（${resp.status}）`
    try {
      const data = await resp.json()
      detail = data.detail || detail
    } catch {
      /* 保持默认错误信息 */
    }
    throw new Error(detail)
  }

  await readSSE(resp, onEvent)
}
