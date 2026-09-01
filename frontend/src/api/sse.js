// SSE 客户端：EventSource 不支持 POST 与自定义 Header，统一用 fetch + ReadableStream 解析。
// 用法：
//   await postSSE('/interviews/1/start', {}, { onEvent: (event, data) => {} })
//   await getSSE('/offers/compare/history/1/stream', { onEvent: (event, data) => {} })
// 两套实现（POST / GET）共用 readSSE 解析器，避免行为分叉。
//
// 断线防护：
// - 服务端空闲心跳（sse-starlette ping=15）保活连接
// - 本客户端内置 idleTimeout 看门狗：超过阈值未收到任何数据（含心跳）判定连接僵死，
//   抛出 SSETimeoutError，供上层展示断线提示并走重试逻辑

const DEFAULT_IDLE_TIMEOUT = 45000 // 服务端心跳 15s，错过 3 个心跳才判定断线

function readSSE(resp, onEvent, { idleTimeout = DEFAULT_IDLE_TIMEOUT, signal } = {}) {
  return new Promise((resolve, reject) => {
    const controller = new AbortController()
    if (signal) {
      if (signal.aborted) {
        reject(new DOMException('Aborted', 'AbortError'))
        return
      }
      signal.addEventListener('abort', () => controller.abort(), { once: true })
    }

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    const splitter = /\r?\n\r?\n/
    let buffer = ''
    let lastActive = Date.now()
    let watchdog = null

    const finish = () => {
      if (watchdog) clearInterval(watchdog)
      resolve()
    }
    const fail = (err) => {
      if (watchdog) clearInterval(watchdog)
      reject(err)
    }

    // 僵死连接检测：任何数据（含心跳注释）都会刷新 lastActive
    watchdog = setInterval(() => {
      if (Date.now() - lastActive > idleTimeout) {
        controller.abort()
        const err = new Error('连接已断开，请检查网络后重试')
        err.name = 'SSETimeoutError'
        fail(err)
      }
    }, 5000)

    async function pump() {
      try {
        while (true) {
          let result
          try {
            result = await reader.read()
          } catch (e) {
            if (controller.signal.aborted) {
              fail(new DOMException('Aborted', 'AbortError'))
              return
            }
            throw e
          }
          if (result.done) {
            finish()
            return
          }
          lastActive = Date.now()
          buffer += decoder.decode(result.value, { stream: true })

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
                controller.abort()
                const err = new Error(payload?.message || '服务异常')
                err.name = 'SSEError'
                fail(err)
                return
              }
              try {
                onEvent?.(event, payload)
              } catch (e) {
                // 回调异常不应破坏流解析，交由上层自行处理
              }
            }
            match = buffer.match(splitter)
          }
        }
      } catch (e) {
        if (controller.signal.aborted) {
          fail(new DOMException('Aborted', 'AbortError'))
          return
        }
        fail(e)
      }
    }
    pump()
  })
}

async function authHeaders() {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function postSSE(url, body = {}, { onEvent, signal, idleTimeout } = {}) {
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

  await readSSE(resp, onEvent, { idleTimeout, signal })
}

export async function getSSE(url, { onEvent, signal, idleTimeout } = {}) {
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

  await readSSE(resp, onEvent, { idleTimeout, signal })
}
