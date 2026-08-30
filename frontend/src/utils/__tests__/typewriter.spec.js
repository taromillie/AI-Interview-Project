import { describe, expect, it } from 'vitest'
import {
  TYPEWRITER_TICK_MS,
  createAiMessage,
  mapHistoryMessage,
  typewriterStep,
  typingTick,
} from '@/utils/typewriter'

describe('打字机纯逻辑', () => {
  it('createAiMessage 创建初始打字机状态', () => {
    const m = createAiMessage('你好，请做自我介绍')
    expect(m.role).toBe('ai')
    expect(m.full).toBe('你好，请做自我介绍')
    expect(m.shown).toBe('')
    expect(m.typing).toBe(true)
    expect(m._timer).toBeNull()
  })

  it('短文本步长为 1', () => {
    expect(typewriterStep(1)).toBe(1)
    expect(typewriterStep(100)).toBe(1)
  })

  it('长文本步长自适应增大且至少为 1', () => {
    const short = typewriterStep(150)
    const long = typewriterStep(600)
    expect(short).toBeGreaterThanOrEqual(1)
    expect(long).toBeGreaterThan(short)
    expect(long).toBeGreaterThan(1)
  })

  it('目标时长约束：整段约 2.5 秒打完', () => {
    const len = 300
    const step = typewriterStep(len)
    const ticks = Math.ceil(len / step)
    const ms = ticks * TYPEWRITER_TICK_MS
    expect(ms).toBeLessThanOrEqual(2500 + TYPEWRITER_TICK_MS)
    expect(ms).toBeGreaterThan(2000)
  })

  it('typingTick 未完成时推进位置', () => {
    const r = typingTick(0, 3, 100)
    expect(r.pos).toBe(3)
    expect(r.done).toBe(false)
  })

  it('typingTick 完成时位置收敛到长度', () => {
    const r = typingTick(97, 5, 100)
    expect(r.pos).toBe(100)
    expect(r.done).toBe(true)
  })

  it('mapHistoryMessage 将 assistant 映射为 ai 且完整展示', () => {
    const m = mapHistoryMessage({ role: 'assistant', content: '第一个问题' })
    expect(m.role).toBe('ai')
    expect(m.content).toBe('第一个问题')
    expect(m.full).toBe('第一个问题')
    expect(m.shown).toBe('第一个问题')
    expect(m.typing).toBe(false)
  })

  it('mapHistoryMessage 将 user 映射为用户消息（含 content 字段）', () => {
    const m = mapHistoryMessage({ role: 'user', content: '我的回答' })
    expect(m.role).toBe('user')
    expect(m.content).toBe('我的回答')
    expect(m.shown).toBe('我的回答')
  })
})
