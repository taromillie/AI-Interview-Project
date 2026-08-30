import { beforeEach, describe, expect, it } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { CircleCheckFilled, WarningFilled } from '@element-plus/icons-vue'
import { createMemoryHistory, createRouter } from 'vue-router'
import Report from '@/views/Report.vue'
import { getReport } from '@/api/report'

vi.mock('@/api/report', () => ({ getReport: vi.fn() }))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/report/:id', component: { template: '<div />' } },
    { path: '/questions', name: 'questions', component: { template: '<div />' } },
  ],
})

const fullReport = {
  overall_score: 85,
  dimensions: { tech: 80, expression: 70, logic: 60, project: 75 },
  summary: '整体表现优秀，继续巩固算法基础。',
  weak_points: ['算法', '系统设计'],
  coverage: {
    covered: ['Vue', 'HTTP'],
    uncovered: ['Webpack', '浏览器渲染'],
  },
  learning_path: [
    { phase: '筑基', duration: '2周', action: '补充计算机网络基础' },
  ],
  question_feedback: [
    { question: '讲讲你的项目', answer: '主导了 XX 模块', comment: '结构清晰', score: 85 },
  ],
}

function mountReport() {
  return mount(Report, {
    global: {
      plugins: [router, ElementPlus],
      components: { CircleCheckFilled, WarningFilled },
      // el-tag 根元素是 <Transition>，默认被 stub 成 TRANSITION-STUB 导致 click 透传失败
      stubs: { transition: false },
    },
  })
}

beforeEach(async () => {
  await router.replace({ path: '/report/1' })
  await router.isReady()
})

describe('面试复盘报告', () => {
  it('加载成功后渲染总分、维度、弱点与逐题批改', async () => {
    vi.mocked(getReport).mockResolvedValue(fullReport)
    const wrapper = mountReport()
    await flushPromises()

    const text = wrapper.text()
    expect(text).toContain('面试复盘报告')
    expect(text).toContain('85') // 总分
    expect(text).toContain('技术能力')
    expect(text).toContain('表达沟通')
    expect(text).toContain('整体表现优秀')
    expect(text).toContain('算法')
    expect(text).toContain('Webpack')
    expect(text).toContain('Vue')
    expect(text).toContain('补充计算机网络基础')
    expect(text).toContain('讲讲你的项目')
    expect(text).toContain('结构清晰')
  })

  it('加载失败展示空态提示', async () => {
    vi.mocked(getReport).mockRejectedValue(new Error('network'))
    const wrapper = mountReport()
    await flushPromises()
    expect(wrapper.text()).toContain('暂无报告')
  })

  it('点击薄弱知识点跳转题库', async () => {
    vi.mocked(getReport).mockResolvedValue(fullReport)
    const wrapper = mountReport()
    await flushPromises()

    const tag = wrapper.findAll('.cov-tag.clickable').find((t) => t.text() === 'Webpack')
    expect(tag).toBeTruthy()
    await tag.trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/questions')
    expect(router.currentRoute.value.query.keyword).toBe('Webpack')
  })
})
