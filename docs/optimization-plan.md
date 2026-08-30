# AI 模拟面试系统 · 现状评估与优化方案

> 生成时间：2026-08-30 ｜ 范围：全栈（backend + frontend），基于当前代码静态分析

## 零、方案适用说明

本项目为**学校实训项目（不上线）**，验收导向是"功能完整、演示不翻车、答辩能讲"。
因此**推荐执行精简路线（P0 全做 + P1-5 部分）**，完整清单保留在下方供参考/答辩素材。

### 实训模式 · 精简路线（约 1.5 天）

| 优先级 | 事项 | 工作量 | 状态 |
| --- | --- | --- | --- |
| 必做 | P0-3 SSE 异常兜底（start 与 answer 对齐） | 0.5 天 | ✅ 已完成（`interview.py`） |
| 必做 | P0-1 简化版：LLM 调用加轻量重试（只做重试，不做熔断/封装重构） | 0.5 天 | ✅ 已完成（`openai_compat.py`，2 次指数退避重试） |
| 建议 | P0-4 简化版：finish 幂等（原子状态更新即可，不做线程池） | 0.5 天 | ✅ 已完成（`interview_orchestrator.py`） |
| 建议 | P1-5 补编排器 + 报告降级单测 | 0.5 天 | ✅ 已完成（`test_interview_orchestrator.py` + `test_feedback.py`，22 项用例） |
| 砍掉 | P0-2 安全基线、P1-1/2/3 性能优化、P1-4 组件拆分、全部 P2 | —— | —— |

**额外收获**：编写编排器测试时发现并修复一个真实 bug —— `answer()` 用**消息 id** 而非 `evidence_atom_ids` 过滤已问题目，消息表与原子表各自自增导致 id 撞车、候选被误排除（LLM 失败时回退会直接结束面试）。修复后测试全绿。

> 答辩话术提示：安全项可以讲"生产环境需强制替换默认密钥、启用 DEBUG=False"，作为设计说明而非待办。

---

## 一、项目现状评估

### 1.1 功能完成度（高）

| 模块 | 状态 | 说明 |
| --- | --- | --- |
| 用户体系 | ✅ | 注册/登录/JWT/AES 加密 Provider Key |
| 模拟面试（文字） | ✅ | SSE 流、四信号决策、工具装配、探针限制 |
| 真实面试（视频） | ✅ | WebRTC 摄像头 + 语音识别/合成 + 降级方案 |
| 复盘报告 | ✅ | 后台线程生成、占位报告、能力画像/学习路径 |
| 简历分析 | ✅ | 上传解析、JD 匹配、转行诊断 |
| 职业工具 | ✅ | 谈薪模拟、Offer 对比、岗位广场、题库 |
| 岗位采集 | ✅ | 职友集爬虫 + robots 合规 + 动态同步 |
| 多 LLM Provider | ✅ | 用户自配置 + 自动重试降级 |

### 1.2 质量基线（较好）

- 后端 12 个测试文件、112 项用例；前端 32 项用例，CI 已接入 GitHub Actions
- 结构化请求日志、LLM 调用日志、异常日志完善
- 登录/注册/面试等敏感接口已加 slowapi 限流
- 爬虫合规：robots.txt 检查、UA 轮换、限速、单任务互斥
- SQLite 已启用 WAL + busy_timeout；前端卸载时正确清理 SSE/语音/摄像头

### 1.3 主要短板（按严重程度）

- **高**：LLM 调用无统一封装（无重试/熔断）、历史列表 N+1、报告线程无并发上限、SSE 异常兜底不全
- **中**：爬虫同步阻塞、编排器重复查询、事务边界模糊、前端巨型组件、核心 service 零测试
- **低**：默认密钥硬编码、死代码、MIME 未校验、搜索无防抖、LLM 实例重复创建

---

## 二、P0 · 高优先（稳定性 / 安全 / 上线前必做）

### P0-1 统一 LLM 调用层：重试 / 超时 / 熔断 / 降级

**现状**：`study_plan.py:118`、`salary_eval.py:138`、`career_diagnosis.py:108`、`offer_compare.py:80`、`resume_parser.py:55`、`resume_matcher.py:40,100`、`real_interview_review.py:80`、`question.py:867`、`feedback.py:103`、`agents/interview_agent.py:96` 各自直接 `llm.achat(...)`，代码重复且行为不一致；除底层 `ChatOpenAI(timeout=60)` 外无应用层超时、无重试、无熔断。

**方案**：
1. 新增 `app/llm/call.py`，提供统一入口 `llm_chat(llm, messages, *, max_retries=2, timeout=60, model=None, temperature=None)`。
2. 内置重试策略：仅对可重试错误（`RateLimitError`、`APIConnectionError`、`TimeoutError`、5xx）做指数退避重试（0.5s/1s/2s）。
3. 统一日志与统计：每次调用记录模型、耗时、token 用量、是否重试；为后续成本与质量观测打基础。
4. 失败时抛标准 `LLMError`（含错误码），各 service 捕获后走既有规则兜底（`decide_next` 兜底、`fallback_decision` 等保持不变）。
5. 可选熔断：按 user_id + provider 记录最近 5 分钟失败率，连续失败 >80% 时快速失败，避免雪崩。

**收益**：接口成功率显著提升；LLM 抖动不再直接 502；行为统一可观测。

### P0-2 生产安全基线

**现状**：`config.py:17` `DEBUG=True`；`config.py:33` `JWT_SECRET="please-change-this-secret"`；`config.py:36` `AES_KEY` 同样有默认值。若部署时未覆盖，攻击者可伪造任意用户 JWT、解密所有用户 LLM API Key。

**方案**：
1. 在 `get_settings()` 中增加校验：`DEBUG` 为 True 且 `JWT_SECRET` 仍为默认值时，启动抛错或打印红色告警。
2. `JWT_SECRET`/`AES_KEY` 校验长度（HS256 ≥ 32 字符；AES-256 严格 32 字节），不满足直接启动失败。
3. docker-compose / 部署文档强制要求通过环境变量注入，不在镜像内写默认密钥。

**收益**：消除最大的潜在安全漏洞。

### P0-3 SSE 异常兜底对齐

**现状**：`interview.py:150-161`（`start_interview`）的 `gen()` 未捕获异常；`submit_answer`（:178-197）和 `_sse`（:122-134）有 try/except AppError。LLM 开场失败时，start 的 SSE 流会异常中断，前端收到断流而非规范化 `error` 事件。

**方案**：`start_interview` 的 `gen()` 补 try/except（与 `submit_answer` 对齐），非 `AppError` 也统一 yield `{"event": "error"}`；建议把三处 SSE 包装收敛为一个工具函数（如 `sse_guard(agen)`）。

**收益**：前端对开场失败能正确提示"面试官暂时不可用"，而非莫名断线。

### P0-4 报告生成线程池化 + 幂等

**现状**：`interview_orchestrator.py:325-331` 每次结束面试 `threading.Thread(...).start()`，无并发上限；`finish()` 无幂等保护，同一面试可重复触发后台任务。

**方案**：
1. 全局 `ThreadPoolExecutor(max_workers=4)`（或 8），`submit(generate_report_task, id)`；模块级单例，避免每次新建线程。
2. `finish()` 状态迁移改为原子条件更新：`UPDATE interview SET status='finishing' WHERE id=? AND status IN ('asking','created')`，检查影响行数，非 1 则返回已结束，杜绝重复任务。
3. `generate_report_task` 内对"已有真实报告"做二次校验（已存在 summary 非占位值则跳过）。

**收益**：并发面试下线程数可控、LLM 并发成本可控、重复结束不产生重复报告。

---

## 三、P1 · 中优先（性能 / 架构 / 测试）

### P1-1 面试历史列表消除 N+1

**现状**：`interview.py:217-223` `list_interviews` 对每条记录调 `_make_out`（:46-74），内部再查 Position、Interviewer、Report、消息计数共 4 次；50 条即额外 200 次查询。

**方案**：
1. 一次性取 `rows` 后，收集所有 `position_id`/`interviewer_id` 批量 `IN` 查询成字典。
2. 报告：`SELECT * FROM reports WHERE interview_id IN (...)` 一次取全。
3. 消息计数：`SELECT interview_id, COUNT(*) FROM interview_messages WHERE interview_id IN (...) GROUP BY interview_id` 一次取全。
4. `_make_out` 改为接收这些预取字典组装，或改用 SQLAlchemy `selectinload` + 聚合子查询。

**收益**：历史列表从 1+4N 次查询降到常数次，页面随数据量增长仍流畅。

### P1-2 编排器消息查询复用

**现状**：`interview_orchestrator.py` 的 `answer()` 内 `_messages()` 被调用 6 次以上（`_asked_rounds`、`_probe_streak`、`_avoid_streak`、`_history_text`、`asked_ids` 等），每次整表 SELECT。

**方案**：`answer()` 开头 `msgs = self._messages()` 一次，所有内部方法改为接收 `msgs` 参数（或短暂缓存于实例）。

**收益**：每次作答从 6 次查询降到 1 次，SSE 响应延迟更低。

### P1-3 岗位采集异步化

**现状**：`job_crawler.py:142-156` 同步 `httpx.Client` 请求 robots.txt；`:373-375` `_throttle`/`polite_sleep` 同步 `time.sleep(3~6s)`。`main.py:26-38` 的后台线程整个同步执行，单次同步可能阻塞数分钟，且无法优雅中断。

**方案**：
1. 将爬取主体改异步（`httpx.AsyncClient` + `asyncio.sleep`），后台任务用 `asyncio.create_task` 或独立 asyncio loop 承载。
2. 保留 `_SYNC_LOCK` 单任务互斥；增加取消标志，支持优雅停机。
3. 若改动量大，可先退一步：将 `_ensure_loaded` 的 robots 请求改为 `requests` 带短超时（如 5s），`polite_sleep` 上限封顶（如 ≤10s）。

**收益**：后台同步不占独立线程、可中断；爬虫运行时间更可控。

### P1-4 前端巨型组件拆分

**现状**：`views/Interview.vue` 约 1776 行，混装向导、对话、打字机、语音识别、语音合成、摄像头采集、活动检测、SSE 管理、断线恢复等 8+ 类关注点；`views/JobMarket.vue` 约 1487 行。

**方案**：
1. `Interview.vue` 拆分：
   - `components/interview/WizardStep.vue`：三步设置向导
   - `components/interview/ChatPanel.vue`：消息列表 + 输入区 + 打字机
   - `components/interview/VoiceBar.vue`：语音识别/合成控制条
   - `components/interview/CameraPanel.vue`：视频采集 + 活动检测
   - `composables/useVoice.js`、`useCamera.js`、`useSSE.js`：能力抽离为可测试 hooks
2. `JobMarket.vue` 拆分：`JobFilterBar`、`JobCardList`、`JobDetailDialog` 子组件。
3. 拆分过程中用现有 `utils/typewriter.js` 模式，把纯逻辑抽到 utils/composables 便于单测。

**收益**：可读性/可维护性大幅提升，多人协作冲突减少，逻辑可单测。

### P1-5 补核心 service 单元测试

**现状**：测试覆盖集中在 `interview_agent`、`rag`、`job_crawler`、`question_import`、`real_interview_review`；**核心编排与报告逻辑零覆盖**：`interview_orchestrator.py`、`feedback.py`、`resume_matcher.py`、`salary_eval.py`、`offer_compare.py`、`study_plan.py`、`career_diagnosis.py`。

**方案**（复用现有 FakeLLM + 内存 DB 模式）：
1. `test_interview_orchestrator.py`：状态流转（created→asking→reported）、max_rounds 到点收尾、probe_streak 强制换题、LLM 失败走 `fallback_decision`、`finish()` 幂等。
2. `test_feedback.py`：LLM 返回非法 JSON / 空内容时的降级路径、维度归一化、占比校验。
3. 为 `resume_matcher`/`salary_eval`/`study_plan` 各补一条"LLM 失败 → 规则兜底"用例。

**收益**：核心用户路径获得回归保障，后续重构 LLM 封装层时可安全进行。

---

## 四、P2 · 低优先（打磨）

| # | 问题 | 位置 | 方案 |
| --- | --- | --- | --- |
| P2-1 | 双重 `json.loads` | `resume_matcher.py:45` | `try: data = json.loads(raw)` 只解析一次 |
| P2-2 | 死代码 | `job_crawler.py:585` `_API_TAG_WORDS` 未使用；`JobMarket.vue:379` `applyFilter()` 空函数 | 删除 |
| P2-3 | 简历上传无 MIME 校验 | `resume.py:50-53`、`resume_parser.py:22-29` | 校验 `file.content_type` 白名单（pdf/txt/md）；读取前检查 `content_length` |
| P2-4 | 搜索无防抖 | `JobMarket.vue` 搜索框 | 关键词 debounce 200ms 后再过滤 |
| P2-5 | LLM 客户端重复创建 | `llm_utils.py:12-27` | 按 user_id+provider 做短期缓存（TTL 5min） |
| P2-6 | JSON 字段 LIKE 过滤 | `question.py:658-666` | tags 建规范化关联表或独立索引列 |
| P2-7 | 前端零星吞错/重复弹窗 | `Interview.vue:645`、`JobMarket.vue` 若干 catch | 统一错误策略：拦截器只弹一次，局部 catch 只处理业务分支 |

---

## 五、实施路线图

| 阶段 | 周期 | 内容 | 验收标准 |
| --- | --- | --- | --- |
| 阶段一 | 1-2 天 | P0-1 ~ P0-4 | LLM 抖动下接口成功率上升；并发结束面试线程数有上限；start SSE 异常能收到 error 事件 |
| 阶段二 | 2-3 天 | P1-1 ~ P1-5 | 历史列表 200+ 条毫秒级返回；`Interview.vue` 拆分后子组件 < 500 行；核心 service 测试补齐且 CI 通过 |
| 阶段三 | 持续迭代 | P2-1 ~ P2-7 | lint 无死代码告警；上传校验生效；搜索输入流畅 |

## 六、预期收益总结

1. **稳定性**：LLM 故障从"接口 502"降级为"规则兜底可用"，核心面试/报告流程不中断。
2. **性能**：历史列表、面试作答响应、岗位采集、前端交互全面提速。
3. **安全**：消除默认密钥风险，密钥强制校验。
4. **可维护性**：巨型组件拆分 + 核心测试补齐，为后续功能迭代（多人协作/视频面试增强）扫清障碍。
5. **可观测**：LLM 统一日志为成本控制与效果评估提供数据基础。
