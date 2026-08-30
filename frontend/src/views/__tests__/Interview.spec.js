import { beforeEach, describe, expect, it } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import ElementPlus from 'element-plus'
import * as Icons from '@element-plus/icons-vue'
import { createMemoryHistory, createRouter } from 'vue-router'
import Interview from '@/views/Interview.vue'
import {
  createInterview,
  getInterviewDetail,
  startInterview,
} from '@/api/interview'
import { listInterviewers } from '@/api/interviewer'

vi.mock('@/api/diagnostic', () => ({ listResumes: vi.fn().mockResolvedValue([]) }))
vi.mock('@/api/question', () => ({ listPositions: vi.fn().mockResolvedValue([]) }))
vi.mock('@/api/interviewer', () => ({ listInterviewers: vi.fn().mockResolvedValue([]) }))
vi.mock('@/api/interview', () => ({
  answerInterview: vi.fn().mockResolvedValue(undefined),
  createInterview: vi.fn().mockResolvedValue({ id: 1 }),
  finishInterview: vi.fn().mockResolvedValue(undefined),
  getInterviewDetail: vi.fn().mockResolvedValue(undefined),
  startInterview: vi.fn().mockResolvedValue(undefined),
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [{ path: '/interview', component: { template: '<div />' } }],
})

const interviewer = {
  id: 1,
  name: '张伟',
  title: '资深面试官',
  interview_type: 'tech',
  difficulty_bias: 'normal',
  persona: '严谨专业，关注真实能力。',
}

const interviewIcons = [
  'Aim', 'User', 'Check', 'DataAnalysis', 'ArrowLeft',
  'ArrowRight', 'MagicStick', 'Warning', 'Microphone', 'Promotion',
  'Bell', 'BellFilled', 'VideoCamera',
]

async function mountInterview(query = {}) {
  await router.replace({ path: '/interview', query })
  await router.isReady()
  return mount(Interview, {
    global: {
      plugins: [router, ElementPlus],
      components: Object.fromEntries(interviewIcons.map((n) => [n, Icons[n]])),
      // el-tag 根元素是 <Transition>，默认被 stub 成 TRANSITION-STUB 导致 click 透传失败
      stubs: { transition: false },
    },
  })
}

beforeEach(async () => {
  await router.replace('/interview')
  await router.isReady()
  listInterviewers.mockResolvedValue([interviewer])
  createInterview.mockResolvedValue({ id: 1 })
  getInterviewDetail.mockResolvedValue(undefined)
  startInterview.mockResolvedValue(undefined)
})

describe('AI 模拟面试页', () => {
  it('无继续面试参数时展示岗位向导', async () => {
    const wrapper = await mountInterview({})
    await flushPromises()
    const text = wrapper.text()
    expect(text).toContain('岗位库')
    expect(text).toContain('自定义')
    expect(wrapper.find('.chat-input').exists()).toBe(false)
  })

  it('带 interview_id 时恢复会话并渲染历史问答', async () => {
    getInterviewDetail.mockResolvedValue({
      id: 9,
      status: 'asking',
      target_position: '前端工程师',
      difficulty: 'normal',
      max_rounds: 6,
      interviewer_id: 1,
      interviewer,
      messages: [
        { role: 'assistant', content: '欢迎参加本次面试' },
        { role: 'user', content: '我叫小明' },
      ],
    })
    const wrapper = await mountInterview({ interview_id: '9' })
    await flushPromises()

    expect(getInterviewDetail).toHaveBeenCalledWith(9)
    const text = wrapper.text()
    expect(text).toContain('欢迎参加本次面试')
    expect(text).toContain('我叫小明')
    expect(wrapper.find('.chat-input').exists()).toBe(true)
    wrapper.unmount()
  })

  it('向导三步后开始面试，收到 question 事件触发打字机消息', async () => {
    let onEvent = null
    startInterview.mockImplementation(async (_id, opts) => {
      onEvent = opts.onEvent
    })

    // 通过 query.target 注入自定义岗位，跳过岗位交互（applyQueryParams 会设置）
    const wrapper = await mountInterview({ target: '前端工程师' })
    await flushPromises()

    // ① 自定义岗位（已就绪）→ 下一步
    const nextBtn = () =>
      wrapper.findAll('.w-nav .el-button').find((b) => b.text().includes('下一步'))
    await nextBtn().trigger('click')
    await nextTick()

    // ② 面试官（已自动选中第一个）→ 下一步
    await nextBtn().trigger('click')
    await nextTick()

    // ③ 开始面试
    const startBtn = wrapper.findAll('.w-nav .el-button').find((b) => b.text().includes('开始面试'))
    await startBtn.trigger('click')
    await flushPromises()

    expect(createInterview).toHaveBeenCalledWith(
      expect.objectContaining({ mode: 'text', difficulty: 'normal', interviewer_id: 1 }),
    )
    expect(startInterview).toHaveBeenCalledTimes(1)
    expect(typeof onEvent).toBe('function')

    // 触发 question → 打字机 AI 消息出现
    onEvent('question', { question: '请做个自我介绍' })
    await nextTick()
    const aiMsg = wrapper.find('.msg.ai')
    expect(aiMsg.exists()).toBe(true)

    // 点击气泡跳过打字机 → 完整文本展示
    await aiMsg.trigger('click')
    expect(wrapper.text()).toContain('请做个自我介绍')
    expect(wrapper.find('.typing-caret').exists()).toBe(false)

    wrapper.unmount()
  })

  it('向导步骤 3 展示回答方式：无语音 API（jsdom）下语音/视频禁用，仍以文字模式开始', async () => {
    const wrapper = await mountInterview({ target: '前端工程师' })
    await flushPromises()
    const nextBtn = () =>
      wrapper.findAll('.w-nav .el-button').find((b) => b.text().includes('下一步'))
    // 步骤切换被 <transition mode="out-in"> 包裹，jsdom 无动画需等待 1ms 兜底 timer
    const goNext = async () => {
      await nextBtn().trigger('click')
      await new Promise((r) => setTimeout(r, 60))
    }
    await goNext()
    await goNext()

    // 回答方式三选项：文字 / 语音 / 视频（T7 降级方案）
    const radios = wrapper.findAll('.mode-group .el-radio-button')
    expect(radios.length).toBe(3)
    expect(radios[0].text()).toContain('文字')
    expect(radios[1].text()).toContain('语音')
    expect(radios[2].text()).toContain('视频')

    // jsdom 无 SpeechRecognition → 语音/视频不可选，仅文字可用（降级保障）
    const disabled = wrapper.findAll('.mode-group .el-radio-button.is-disabled')
    expect(disabled.length).toBe(2)

    // 默认文字模式开始面试，不请求摄像头
    const startBtn = wrapper.findAll('.w-nav .el-button').find((b) => b.text().includes('开始面试'))
    await startBtn.trigger('click')
    await flushPromises()
    expect(createInterview).toHaveBeenCalledWith(expect.objectContaining({ mode: 'text' }))
    wrapper.unmount()
  })
})
