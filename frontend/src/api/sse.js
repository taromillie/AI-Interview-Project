// SSE POST 客户端：EventSource 不支持 POST，改用 fetch + ReadableStream 解析。
// 用法：
//   await postSSE('/interviews/1/start', {}, {
//     onEvent: (event, data) => { ... },
//   })

export async function postSSE(url, body = {}, { onEvent, signal } = {}) {
  const token = localStorage.getItem('token')
  const resp = await fetch(`/api${url}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: token ? `Bearer ${token}` : '',
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
