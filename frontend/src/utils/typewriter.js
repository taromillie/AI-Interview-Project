// 面试消息打字机纯逻辑（无副作用，便于单元测试）

export const TYPEWRITER_TICK_MS = 16
// 目标时长：整段问题约 2.5 秒打完
export const TYPEWRITER_TARGET_MS = 2500

/** 创建 AI 打字机消息的初始状态 */
export function createAiMessage(content) {
  return { role: 'ai', full: content, shown: '', typing: true, _timer: null }
}

/** 计算打字机步长：按目标时长与文本长度自适应 */
export function typewriterStep(length) {
  return Math.max(1, Math.ceil(length / (TYPEWRITER_TARGET_MS / TYPEWRITER_TICK_MS)))
}

/** 推进一次打字机 tick，返回新位置与是否完成 */
export function typingTick(pos, step, length) {
  const next = pos + step
  return { pos: next >= length ? length : next, done: next >= length }
}

/** 将后端历史消息映射为聊天展示消息（恢复面试时使用） */
export function mapHistoryMessage(m) {
  return {
    role: m.role === 'assistant' ? 'ai' : 'user',
    // content 供用户气泡渲染，full/shown 供 AI 气泡（打字机）渲染
    content: m.content,
    full: m.content,
    shown: m.content,
    typing: false,
  }
}
