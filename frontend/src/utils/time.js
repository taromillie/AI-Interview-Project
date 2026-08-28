// 后端数据库统一存 UTC 时间（func.now()），接口返回的 ISO 字符串无时区标记。
// 因此解析时一律按 UTC 处理，再转浏览器本地时区显示（如北京时间）。
// 若字符串已带时区标记（Z / ±hh:mm），则原样交给 Date 解析。

function hasTz(s) {
  return /(?:Z|[+-]\d{2}:?\d{2})$/i.test(s.trim())
}

// 将后端返回的时间字符串解析为本地时间 Date（naive 字符串按 UTC 补 Z）
export function parseDate(s) {
  if (!s) return null
  const raw = String(s).trim()
  if (!raw) return null
  const iso = hasTz(raw) ? raw : raw.replace(' ', 'T') + 'Z'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? null : d
}

const p2 = (n) => String(n).padStart(2, '0')

// YYYY-MM-DD HH:mm（本地时区，即北京时间）
export function formatDateTime(s) {
  const d = parseDate(s)
  if (!d) return s ? String(s) : ''
  return `${d.getFullYear()}-${p2(d.getMonth() + 1)}-${p2(d.getDate())} ${p2(d.getHours())}:${p2(d.getMinutes())}`
}

// MM-DD（本地时区）
export function shortDate(s) {
  const d = parseDate(s)
  if (!d) return ''
  return `${p2(d.getMonth() + 1)}-${p2(d.getDate())}`
}

// YYYY-MM-DD（本地时区）
export function formatDate(s) {
  const d = parseDate(s)
  if (!d) return ''
  return `${d.getFullYear()}-${p2(d.getMonth() + 1)}-${p2(d.getDate())}`
}
