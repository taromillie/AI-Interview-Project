# AI 模拟面试官与职业规划系统

面向求职者的 AI 面试训练与职业规划平台：简历 × JD 智能匹配诊断、动态追问模拟面试（文字/语音）、面试复盘与能力成长追踪、真实面试复盘、转行诊断、谈薪模拟、Offer 对比与备战计划。

## 功能特性

| 模块 | 说明 |
| --- | --- |
| 简历 × JD 智能匹配 | 上传简历 + 粘贴目标岗位 JD，输出匹配分、技能缺口与逐项优化建议 |
| 简历 → 岗位匹配 | 按简历技能从岗位库匹配推荐岗位 Top N，展示命中/缺口技能、匹配度与推荐理由 |
| 动态追问模拟面试 | 有边界面试 Agent，基于回答动态决策「深挖 / 补救 / 换题 / 项目追问」，SSE 流式对话；支持语音输入与语音播报（Web Speech API） |
| 面试官角色库 | 内置/自建面试官人设（风格、追问偏好、难度偏移），面试前按需选择 |
| 复盘报告 | 逐题批改、四维度评分、弱点标签、总评建议 |
| 能力画像与成长趋势 | 多场面试聚合六维雷达图 + 技能评分 + 高频弱点 + 时间维度趋势折线 |
| 真实面试复盘 | 录入真实面试问答，AI 逐题批改与整体复盘，沉淀为能力画像数据 |
| 备战计划 | 基于能力画像缺口与目标岗位生成 N 天冲刺计划，任务勾选跟踪进度 |
| 转行诊断 | 双岗位能力模型对比、可迁移技能图谱、转行专属面试模式 |
| 谈薪模拟 | 薪资竞争力评估 + HR 人设谈薪模拟 |
| Offer 对比 | 多 Offer 加权评分对比 + AI 综合分析建议 |
| 岗位广场 | 内置岗位库 + 职友集真实岗位数据同步，支持筛选、检索与一键发起岗位面试 |
| 公共题库 | 岗位知识原子库，管理员发布、草稿 → 发布流转 |
| 多 LLM Provider 可插拔 | 支持 DeepSeek / Kimi / GLM / Qwen / 任意 OpenAI 兼容接口，无需改代码切换 |

## 技术栈

| 端 | 技术 |
| --- | --- |
| 后端 | Python 3.11+ / FastAPI / SQLAlchemy / SQLite / SSE 流式响应 |
| 前端 | Vue 3 (Composition API) / Vite / Vue Router / Pinia / Element Plus |
| 部署 | Docker Compose（后端 + 前端 Nginx 双容器） |

## 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 首次使用：复制部署环境变量（可选，所有项均有默认值）
#   Windows:  copy .env.example .env
#   macOS/Linux: cp .env.example .env
docker compose up --build
```

- 前端：<http://localhost:5173>
- 后端 API 文档：<http://localhost:8000/docs>

> 依赖 Docker（需要本机已安装并启动 Docker Desktop / Docker Engine）。
> 后端数据（SQLite + 向量库）持久化在 Docker 卷 `backend_data` 中。
> 实机验证清单见 `docs/deploy-verification.md`（12 项检查：健康 / 持久化 / SSE / 日志级别等）。

### 方式二：本地开发

**后端**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
cp .env.example .env         # 填入 LLM API Key 等配置
uvicorn app.main:app --reload --port 8000
```

**前端**

```bash
cd frontend
npm install
npm run dev                   # 默认 http://localhost:5173
```

## 使用前配置

编辑 `backend/.env`，必填项：

```ini
# LLM Provider（默认 deepseek）
LLM_PROVIDER=deepseek
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

所有 Provider（DeepSeek / Kimi / GLM / Qwen / 自定义）均可在前端「模型配置」页切换，无需改代码。不配置 Key 时系统会降级为「规则模板 + 离线诊断」，仍可体验完整流程。

## 文档

| 文档 | 内容 |
| --- | --- |
| `docs/design.md` | 架构设计：决策记录、目录结构、ER 设计、API 设计、演进路径 |
| `docs/next-step-plan.md` | 下一步迭代方案（P4 打磨验收与发布准备） |
| `docs/requirements.md` | 需求说明 |

## 开发进度

### Phase 1 · MVP 闭环 ✅（2026-08-27 ~ 08-28）

- ✅ 注册登录 / 工作台 / 面试启动
- ✅ 简历上传解析与预览
- ✅ 简历 × JD 智能匹配诊断（匹配分、技能缺口、逐项建议）
- ✅ 动态追问模拟面试（文字版，SSE 流式）
- ✅ 面试复盘报告（逐题批改、四维评分、弱点标签）

### Phase 2 · 职业规划与成长追踪 ✅（2026-08-28）

- ✅ 转行诊断：双岗位能力模型对比 + 可迁移技能图谱 + 专属面试模式
- ✅ 谈薪模拟：薪资竞争力评估 + HR 人设谈判
- ✅ 能力画像：多场面试聚合六维雷达图 + 技能评分 + 高频弱点
- ✅ 面试历史与报告回看
- ✅ 面试官角色库：人设配置 + 面试难度档位
- ✅ 多 LLM Provider 可插拔

### Phase 3 · 面试闭环与数据增强 ✅（2026-08-28 ~ 08-29）

- ✅ 语音面试：Web Speech API 语音输入 + 语音播报，识别失败自动回退文字
- ✅ 真实面试复盘：录入真实面试问答 → AI 逐题批改 → 整体复盘，聚合进能力画像
- ✅ 备战日历：基于能力画像缺口 + 目标岗位生成 N 天冲刺计划，任务勾选推进、完成自动收尾
- ✅ 岗位广场：内置岗位库 + 职友集真实岗位数据同步（幂等入库 + 失败兜底）
- ✅ 简历 → 岗位智能匹配：按简历技能匹配 Top N 推荐岗位，覆盖式保存结果
- ✅ Offer 对比：多 Offer 加权评分 + AI 综合建议
- ✅ 能力画像增强：新增成长趋势（时间维度折线）
- ✅ 公共题库：管理员发布机制

### 待办 · P4 打磨验收与发布准备

- [ ] T2 部署验证：Docker Compose 实机验证（清单 `docs/deploy-verification.md`）、`.env` 生产化（需 Docker 机器）
- [ ] T4 后端测试补强：RAG 链路、真实复盘、岗位同步（目标 ≥45 项）
- [ ] T5 前端自动化测试（Vitest，≥10 项）
- [ ] T3 演示准备：一键演示数据脚本 + 演示脚本文档
- [ ] T6 体验优化：面试流式展示/断线提示、报告加载态、首屏性能
- [ ] 视频面试（C 级低优先）、题库批量导入、岗位投递状态跟踪

## 目录结构

```
ai模拟面试/
├── backend/
│   ├── app/
│   │   ├── api/           # 路由：auth / resume / jd / interview / report
│   │   │                  #       profile / real_interview / study_plan
│   │   │                  #       offer / position_match / question
│   │   │                  #       interviewer / career / salary / provider
│   │   ├── models/        # SQLAlchemy 模型（用户/简历/面试/报告/岗位/Offer…）
│   │   ├── services/      # 业务服务（面试编排/复盘/能力画像/爬虫/匹配/规划…）
│   │   └── main.py
│   ├── scripts/           # 数据脚本
│   ├── tests/             # pytest 测试
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── views/         # 17 个页面：面试/复盘/画像/岗位/复盘/备战/Offer…
│       ├── components/    # 复用组件
│       ├── router/        # 路由（含登录守卫）
│       ├── stores/        # Pinia 状态
│       └── api/           # 接口封装
├── docker-compose.yml     # 后端 + 前端双容器编排
└── docs/                  # 设计文档 / 迭代方案
```
