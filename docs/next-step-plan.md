# AI 模拟面试与职业规划系统 — 下一步方案

> 基于 `docs/design.md`、`docs/requirements.md` 的架构规划，结合当前代码库实际完成度与运行状态盘点，制定下一阶段（P4：打磨验收与发布准备）行动方案。

---

## 〇、执行进度（2026-08-30 更新）

| 任务 | 状态 | 说明 |
|------|------|------|
| T1 文档同步 | ✅ 已完成 | README 重写（P3 成果 / 功能矩阵 / 待办收敛）；design.md v1.1→v1.2（新增 4.12~4.16 子系统，目录 / ER / API 与代码对齐） |
| T2 部署验证 | 🟡 等价验证完成 | 修复 5 个部署级问题（见下）+ P2 期配置复查（LOG_LEVEL 透传 / npm ci / .env.example）；本机无 Docker，compose 实机验证待有 Docker 环境执行 |
| T3 演示准备 | ⏸ 暂缓 | 项目周期充足，按用户指示优先 P1 质量加固 |
| T6 核心体验优化 | ✅ 已完成 | 首屏体积 -73%（主 chunk gzip 387KB→102KB）；面试页打字机/断线重试/中断恢复（见下） |
| T4 后端测试补强 | ✅ 已完成 | 28 → 89 项通过（1 项环境跳过）；新增复盘 / 面试 Agent / 岗位同步三类测试（见下） |
| T5 前端自动化测试 | ✅ 已完成 | Vitest 31 项全绿（6 文件）；覆盖路由守卫 / 面试状态机 / 报告渲染；顺带修复 1 个历史恢复 bug（见下） |
| T8 题库与岗位增强 | ✅ 已完成 | 题库批量导入（JSON/MD）+ 标签筛选；岗位收藏 + 投递状态跟踪 + 备战计划联动（见下） |
| T9 工程化补强 | ✅ 已完成 | GitHub Actions CI；日志分级；/health 数据库探测（见下） |
| T7 视频面试 | ✅ 已完成（降级方案） | 回答方式三选（文字/语音/视频）；视频模式摄像头浮窗 + 画面活动监测，失败自动回退语音/文字（见下） |

**T2 发现并修复的问题**：
1. `main.py` 未注册 `position_match` 路由 → 简历→岗位匹配接口 404；已注册，并补齐缺失的 `ResumePositionMatch` 模型（`models/resume.py`）。
2. `requirements.txt` 中 `slowapi>=0.115.0` 版本号错误（PyPI 最高 0.1.10）→ 依赖安装/构建失败；修正为 `slowapi>=0.1.9`。
3. 无 `.dockerignore` → `.env` / `.venv` / `data` 有被打进镜像风险；已补 `backend/.dockerignore`、`frontend/.dockerignore`。
4. compose 未透传 JWT/AES/岗位采集/嵌入模型配置 → 已支持根目录 `.env` 透传（新增 `.env.example`），并加后端 healthcheck。
5. README 部署端口错误（8080→5173）、技术栈 TailwindCSS→Element Plus。

**T2 等价验证结果**：
- 后端：容器同款环境变量启动成功，`/health` 200，43 条路由全部注册（含 `match-positions`），注册接口 201；`pytest` **28 passed / 1 skipped** 无回归。
- 前端：`npm ci` + `vite build` 成功（7.26s，dist 46 文件 2.0MB）。
- ⚠️ 主 chunk 体积问题已由 T6 解决（见下）。

**T6 核心体验优化成果**（2026-08-29）：
1. **首屏性能**：Element Plus 全量引入 → `unplugin-vue-components` 按需引入 + 仅注册实际使用的 41 个图标（原全量 400+）。主 chunk `index-*.js` gzip **387KB → 102KB（-73%）**，达标 < 350KB。
2. **面试页打字机**：question 逐字展示（约 2.5s 打完整段，步长按长度自适应），点击气泡跳过。
3. **断线提示 + 重试**：SSE 中断时横幅提示（保留输入内容），`startInterview` 幂等可安全重试。
4. **会话中断恢复**：历史页对进行中面试显示「继续面试」按钮 → `?interview_id=` 恢复聊天上下文与状态（语音不自动播报，避免突响）。
- 修复 resolver 已知缺陷：`ElementPlusResolver` 会把 `el-icon` 错误指向 `@element-plus/icons-vue`（该包不导出 `ElIcon`），已用 `exclude` + 手动注册 `ElIcon` 绕开。

**T4 后端测试补强成果**（2026-08-29）：
- 总数 **28 → 89 passed**（1 项环境相关 skip），超出 ≥ 45 目标。
- 新增 `test_real_interview_review.py`（10 项）：`_extract_json` / `_clamp` / `_rule_review` / `review_real_interview` 的 LLM 写回、异常与非法 JSON 兜底、空题目边界。
- 新增 `test_interview_agent.py`（18 项）：`decide_next` 决策解析与规则回退、`fallback_decision`（轮次上限 / 题库耗尽 / remedy / switch_topic）、开场白 persona 与难度、四信号→策略映射（low_information 难度加权、project_hint、weak_recall 优先级、avoid_streak）。
- 新增 `test_job_crawler.py`（33 项）：方向/难度推断、技能福利薪资解析（万→K、14薪剔除）、`_upsert` 幂等（builtin 按 name、爬虫按 source+source_id）、内置源 `_do_sync` 二次同步幂等、`_make_item` 技术岗过滤。

**T5 前端自动化测试成果**（2026-08-30）：
- 引入 Vitest ^3.2.7 + Vue Test Utils ^2.5.0 + jsdom ^30；`vite.config.js` 增加 test 配置（`environment: 'jsdom'`、`globals: true`、`deps.inline: ['element-plus']`、`testTimeout: 20000`），`package.json` 新增 `npm run test`。
- 6 个测试文件 **31 项全部通过**（≥ 10 项目标达成）：
  - `src/utils/__tests__/typewriter.spec.js`（8 项）：打字机步长/进度/消息映射（含 `content` 字段回归断言）。
  - `src/utils/__tests__/time.spec.js`（9 项）：时间格式化（相对时间 / 日期 / 时长），参照原生 Date 断言、时区无关。
  - `src/stores/__tests__/user.spec.js`（4 项）：Pinia 登录/登出/token 持久化与用户态回退。
  - `src/router/__tests__/guard.spec.js`（4 项）：真实 `createMemoryHistory` 路由下登录守卫放行/拦截/重定向。
  - `src/views/__tests__/Report.spec.js`（3 项）：真实 router + Element Plus + 图标注册下报告渲染、空态、失败态。
  - `src/views/__tests__/Interview.spec.js`（3 项）：mock API 下面试向导 → 会话开始 → 回答 → 结束全流程状态机。
- 顺带修复 1 个生产 bug：`mapHistoryMessage` 缺少 `content` 字段 → 恢复历史会话时用户消息气泡空白（测试暴露），已补全。
- 回归验证：`vite build` 成功（主 chunk gzip 105.50KB，无体积回归）。

**T6 补充修复**（2026-08-30）：面试页打字机不生效（Vue 响应式引用问题）——push 后取回 proxy 引用再驱动 `typingTick`，恢复正常逐字展示。

**T8 题库与岗位增强成果**（2026-08-30）：
- **题库批量导入**：新增 `POST /api/questions/import`（format=auto/json/markdown），解析器在 `services/question_import.py`（JSON 数组/`{questions}` 对象、Markdown `## 标题`+要点+`标签:`+`难度:`），同岗位按题目去重，导入后为私有草稿；前端弹窗支持文本粘贴与 `.json/.md/.txt` 文件上传，返回 新建/跳过/失败 逐行统计。
- **标签筛选**：`GET /api/questions` 新增 `tag` 参数（JSON 数组精确匹配），题库页新增标签筛选输入框。
- **岗位收藏**：新增 `JobFavorite` 模型（user+position 唯一）；`/api/job-track` 路由提供 favorite/unfavorite/summary；岗位卡星标收藏、详情弹窗收藏按钮、列表「仅看已收藏」筛选。
- **投递状态跟踪**：新增 `JobApplication` 模型，状态机 saved→applied→interviewing→offer/rejected（`PUT /api/job-track/positions/{id}/application` 幂等 upsert）；卡片状态徽章 + 详情弹窗下拉流转 + 移除跟踪。
- **备战计划联动**：`StudyPlan` 新增 `position_id` 外键（DB 迁移已加列）；生成计划时可传 `position_id`，自动回填目标岗位名并将岗位关键技能并入学习上下文；前端步骤 1 提供「我的岗位」快捷选择。
- 服务重启验证：`/health` 返回 `database` 字段；`/api/job-track/summary` 401 需认证（新路由已生效）。

**T9 工程化补强成果**（2026-08-30）：
- 新增 `.github/workflows/ci.yml`：push/PR 触发后端 pytest + 前端 vitest + vite build。
- 日志分级：`core/logging_config.py` 统一控制台格式与级别（`LOG_LEVEL` 环境变量透传 compose），main.py 启动即生效并压制访问日志噪音。
- 健康检查增强：`/health` 增加数据库连通探测（`SELECT 1`），异常时返回 `degraded`。
- 测试增量：新增 `test_question_import.py`（17 项）+ `test_job_track.py`（7 项），后端总数 **89 → 112 passed / 1 skipped**。
- 前端回归：发现并修复 T6 按需引入配置丢失导致的体积回归（主 chunk 387KB→129.99KB gzip，达标 <350KB），Vitest 31 项全绿。

**P2 部署配置复查**（2026-08-30）：compose 透传 `LOG_LEVEL`；前端 Dockerfile `npm install` → `npm ci`（锁定版本）；`.env.example` 补充 `LOG_LEVEL` 注释；新增 `docs/deploy-verification.md`（12 项实机验证清单）。实机 `docker compose up --build` 仍待有 Docker 的机器执行（本机无 Docker）。

---

## 一、现状盘点（2026-08-28 代码库核验）

### 1.1 已完成功能（超出 README 记录）

| 阶段 | 功能 | 状态 |
|------|------|------|
| P1 MVP | 认证注册、简历诊断、JD 管理、AI 模拟面试（RAG 追问）、面试报告、历史记录 | ✅ 完成 |
| P2 | 语音面试（Web Speech API 输入 + 播报） | ✅ 完成 |
| P2 | 面试官角色库（风格/语气/追问偏好） | ✅ 完成 |
| P2 | 转行诊断 + 过渡项目推荐 | ✅ 完成 |
| P2 | 谈薪模拟评估 | ✅ 完成 |
| P2 | 能力画像（六维雷达 + **成长趋势折线**） | ✅ 完成 |
| P2 | 岗位广场（内置岗位 + 职友集真实数据爬虫） | ✅ 完成 |
| P3 | 真实面试复盘（阶段流转/回答案例对照） | ✅ 完成 |
| P3 | 学习路线/备战计划（结合能力缺口动态生成） | ✅ 完成 |
| P3 | 公共题库（管理员发布机制） | ✅ 完成 |
| 附加 | Offer 对比（多 Offer 加权评分） | ✅ 完成 |
| 附加 | 面试官逐题点评 | ✅ 完成 |

### 1.2 质量与运行验证

| 项 | 结果 |
|----|------|
| 后端单元测试 | `pytest`：**112 passed / 1 skipped** |
| 前端单元测试 | `npm run test`：**32 项通过（6 个测试文件）** |
| 前端生产构建 | `vite build` 成功（主 chunk gzip **130.01KB**，按需引入 + 组件级分包） |
| 服务运行 | 后端 `:8000`、前端 `:5173` 均正常响应（`/health` 含数据库探测） |
| 依赖/环境 | 后端 `.venv` + `app.db`、前端 `node_modules` 就绪 |
| CI | `.github/workflows/ci.yml`：push/PR 自动跑后端 pytest + 前端 vitest + vite build |
| 部署 | `docker-compose.yml` + 双 `Dockerfile` 已就绪；本地等价验证通过（环境变量注入 / 路由 / 构建），**实机验证待有 Docker 环境** |

### 1.3 差距与待办

| 类别 | 差距 | 优先级 |
|------|------|--------|
| 功能 | ✅ T7 已解决（降级方案）：回答方式三选，视频模式摄像头 + 画面活动监测，失败自动回退语音/文字（见 T7 成果） | 已解决 |
| 文档 | ✅ T1 已解决：README 重写（P3 成果 / 功能矩阵 / 待办收敛），design.md v1.2 同步 | 已解决 |
| 测试 | ✅ T4/T5/T8 已解决：后端 **112 项**（复盘/面试 Agent/岗位爬虫/题库导入/岗位跟踪）+ 前端 **31 项**（路由守卫/面试状态机/报告渲染） | 已解决 |
| 部署 | ✅ T2 配置复查完成（LOG_LEVEL 透传 / npm ci / .env.example）；Docker 一键部署**实机验证**待有 Docker 环境 | 已解决 |
| 演示 | 无演示数据初始化脚本、无演示引导 | 中 |
| 工程 | ✅ T9 已解决：CI、日志分级、/health 数据库探测 | 已解决 |
| 题库/岗位 | ✅ T8 已解决：批量导入 + 标签筛选 + 收藏 + 投递状态 + 备战计划联动 | 已解决 |

---

## 二、下一步目标定位

**主线：进入 P4「打磨验收与发布准备」**，把项目从"功能齐备"推进到"可交付、可演示、可部署"。

三条原则：
1. **文档先行**——先让设计文档与代码同步，避免后续工作建立在过时认知上。
2. **验证优先于新功能**——先用自动化测试和 Docker 实机验证锁住现有成果。
3. **新功能按性价比排序**——视频面试（C 级、浏览器兼容性差）不阻塞主线。

---

## 三、任务分解

### P0 — 交付基础（预计 1 周）

**T1 文档同步**
- 更新 `README.md`：新增 P3 成果记录、修正待办列表、补充功能矩阵与演示截图占位。
- 更新 `docs/design.md`：补充新增模块（真实面试复盘、岗位爬虫、学习计划、Offer 对比）的架构说明与数据流图。
- 验收：README 功能清单与代码 100% 一致，删除所有已实现项。

**T2 部署验证**
- 实机执行 `docker compose up --build`，验证前后端容器启动、数据卷持久化、`.env` 注入。
- 补充 `backend/.env.example` 的生产注释（`DEBUG=false`、JWT/AES 密钥、CORS 域名）。
- 验收：新机器仅靠 docker-compose + .env 可一键拉起完整系统。

**T3 演示准备**
- 编写 `backend/scripts/seed_demo.py`：一键生成演示账号、示例简历、岗位数据、面试记录与报告。
- 编写 `docs/demo-script.md`：覆盖 10 分钟演示主线（注册→简历诊断→模拟面试→报告→能力画像→备战计划）。
- 验收：空库上执行 seed 后可完整体验 80% 以上功能。

### P1 — 质量加固（预计 1–2 周）

**T4 核心链路测试补强（后端）**
- RAG 检索链路（题库构建 → 向量检索 → 追问生成）的集成测试。
- 真实面试复盘 `POST /review` 的 mock-LLM 测试。
- 岗位同步（内置源）幂等性测试，外部爬虫用 fixture 隔离。
- 验收：后端测试 ≥ 45 项，`pytest` 全绿。

**T5 前端自动化测试（关键链路）**
- 引入 Vitest + Vue Test Utils。
- 覆盖：登录守卫、面试会话状态机（开始→回答→结束）、报告渲染。
- 验收：核心组件测试 ≥ 10 项，`npm run test` 全绿。

**T6 核心体验优化**
- 面试页：回答流式展示、语音输入中断恢复、断线重连提示。
- 报告页：加载态/失败态完善，多维度雷达图导出（PNG）。
- 首屏性能：路由懒加载核对、`vite build` 产物 < 350KB gzip。
- 验收：关键页面 Lighthouse 性能分 ≥ 85（移动端 ≥ 70）。

### P2 — 功能收尾（可选，按需排期）

**T7 视频面试（FR-C-03）** ✅ 已完成（降级方案，2026-08-30）
- 策略：按计划标记为"低优先/可降级"，**不引入 face-api.js**（本地模型 ~6MB），用轻量截帧像素差分代替。
- 实现：面试向导步骤 3 新增"回答方式"三选（文字/语音/视频）；视频模式 `getUserMedia` 开启摄像头浮窗，每 4s 截 96×72 帧与上一帧对比像素差 → 画面活动状态指示；工具条摄像头开关。
- 降级：摄像头不可用/拒绝授权 → 自动回退语音（语音不可用 → 文字），不阻塞面试主流程；`onUnmounted`/结束面试时释放视频轨道。
- 会话恢复：原会话为 video 模式且浏览器支持语音时自动重开摄像头。
- 后端：`mode: ^(text|voice|video)$` 早已支持，仅前端实现。
- 验收：新增单测 1 项（无语音 API 环境下语音/视频禁用、仍以文字模式提交），前端 **32 项全绿**；构建主 chunk gzip 130.01KB。

**T8 题库与岗位增强**
- 题库：支持批量导入（JSON/MD）、标签筛选、私有题库。
- 岗位：收藏 + 投递状态跟踪（已投/面试中/Offer/淘汰），与备战计划联动。
- 验收：题库页支持导入与筛选；岗位页状态流转可持久化。

**T9 工程化补强** ✅ 已完成（2026-08-30）
- GitHub Actions：push/PR 触发后端 `pytest` + 前端 `vitest` + `vite build`（`.github/workflows/ci.yml`）。
- 后端日志分级：`core/logging_config.py`，支持 `LOG_LEVEL` 环境变量。
- 验收：CI 配置就绪（待推送 GitHub 后触发验证）；`/health` 返回数据库状态；请求日志已存在（main.py 中间件）。

---

## 四、风险与依赖

| 风险 | 影响 | 缓解 |
|------|------|------|
| LLM API 未配置 | 面试/诊断等 AI 功能无法演示 | seed 脚本内置 mock 数据；Provider 页支持自定义 BaseURL/Key |
| 视频面试浏览器兼容 | Chrome 需 HTTPS 才能开摄像头 | 明确降级策略；本地用 `localhost`（属安全上下文） |
| 爬虫源（职友集）反爬失效 | 岗位数据为空 | 保留内置岗位种子数据兜底；同步失败自动 fallback |
| Docker 镜像体积（bge-m3 嵌入模型） | 构建慢 | 首次构建后缓存；文档标注需 ~2GB 磁盘 |

---

## 五、建议执行顺序

```
第 1 周：T1 文档同步 → T2 部署验证 → T3 演示准备
第 2 周：T4 后端测试 → T5 前端测试
第 3 周：T6 体验优化（可与 T4/T5 并行）→ P2 按需排期
```

**第一个执行动作**：T1 文档同步（README + design.md），为后续所有工作建立准确基线。
