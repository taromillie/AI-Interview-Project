import { describe, expect, it } from 'vitest'
import { formatDate, formatDateTime, parseDate, shortDate } from '@/utils/time'

// 参照原生 Date 解析结果断言，与时区无关
const pad = (n) => String(n).padStart(2, '0')

function localRef(iso) {
  const d = new Date(iso)
  return {
    date: `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`,
    time: `${pad(d.getHours())}:${pad(d.getMinutes())}`,
    monthDay: `${pad(d.getMonth() + 1)}-${pad(d.getDate())}`,
  }
}

describe('parseDate', () => {
  it('空值返回 null', () => {
    expect(parseDate(null)).toBeNull()
    expect(parseDate('')).toBeNull()
    expect(parseDate(undefined)).toBeNull()
  })

  it('非法日期字符串返回 null', () => {
    expect(parseDate('not-a-date')).toBeNull()
    expect(parseDate('2024-99-99')).toBeNull()
  })

  it('无时区字符串按 UTC 解析（等价 new Date(s + Z)）', () => {
    const s = '2024-06-15 12:30:00'
    expect(parseDate(s).getTime()).toBe(new Date('2024-06-15T12:30:00Z').getTime())
  })

  it('带 Z 时区字符串原样解析', () => {
    const s = '2024-06-15T12:30:00Z'
    expect(parseDate(s).getTime()).toBe(new Date(s).getTime())
  })

  it('带偏移时区字符串原样解析', () => {
    const s = '2024-06-15T12:30:00+08:00'
    expect(parseDate(s).getTime()).toBe(new Date(s).getTime())
  })
})

describe('格式化函数', () => {
  it('formatDateTime 输出本地日期时间', () => {
    const s = '2024-06-15 12:30:00'
    const ref = localRef('2024-06-15T12:30:00Z')
    expect(formatDateTime(s)).toBe(`${ref.date} ${ref.time}`)
  })

  it('formatDate 输出本地日期', () => {
    const s = '2024-06-15 12:30:00'
    expect(formatDate(s)).toBe(localRef('2024-06-15T12:30:00Z').date)
  })

  it('shortDate 输出 MM-DD', () => {
    const s = '2024-06-15 12:30:00'
    expect(shortDate(s)).toBe(localRef('2024-06-15T12:30:00Z').monthDay)
  })

  it('非法输入回退原值', () => {
    expect(formatDateTime('bad')).toBe('bad')
    expect(formatDate('bad')).toBe('')
    expect(shortDate('bad')).toBe('')
    expect(formatDate(null)).toBe('')
  })
})
