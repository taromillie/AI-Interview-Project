# AI 模拟面试官与职业规划系统 — 架构设计文档

| 项目名称 | AI 模拟面试官与职业规划系统 |
|---|---|
| 文档版本 | v1.1 |
| 创建日期 | 2026-08-27（v1.1 修订于 2026-08-27） |
| 文档类型 | 架构设计文档 |
| 关联文档 | [需求文档](requirements.md) v1.1 |
| 项目定位 | 课程 / 毕业设计项目 |
| 技术路线 | Python（FastAPI + LangChain + 向量检索） |

> **v1.1 修订说明**：① 新增**前端设计系统**章节（向导式分步布局、极简导航、视觉基线）；② 新增**面试官角色系统**与**难度档位体系**设计（Interviewer 模型 + Prompt 注入 + 编排器集成）；③ 新增**岗位广场**设计（Position 模型扩展 + 岗位广场 API）；④ 数据模型与接口设计同步更新。

---

## 1. 概述

### 1.1 设计目标

本文档将需求文档（40 条功能需求、11 条非功能需求）转化为可实施的系统架构，实现以下目标：

| 编号 | 设计目标 | 对应需求 |
|---|---|---|
| AD-01 | 支撑"简历×JD 诊断 → 模拟面试 → 复盘 → 职业规划"全链路 | GOAL-01~05 |
| AD-02 | 实现**有边界的面试 Agent**（工具约束 + JSON 契约 + 失败回退） | FR-C-04/05/09 |
| AD-03 | 实现**动态 RAG 追问决策**（四类信号驱动下一问策略） | FR-C-05 |
| AD-04 | 保证业务真相与向量索引解耦（向量库可随时重建） | NFR-06/07 |
| AD-05 | 支持多 LLM Provider 可插拔、多岗位方向可配置 | NFR-08/09 |
| AD-06 | 架构分层清晰、便于测试与评审 | NFR-11 |
| AD-07 | 支撑**面试官角色系统**：角色库可配置，人设 Prompt 注入 Agent | FR-C-10 / FR-I-01~03 |
| AD-08 | 支撑**难度档位体系**：创建面试选难度，Agent 行为按档调节 | FR-C-11 / FR-I-04 |
| AD-09 | 支撑**岗位广场**：岗位卡片网格 → 一键发起岗位导向面试 | GOAL-07 / FR-H-01~03 |
| AD-10 | 统一**前端设计系统**：向导式分步布局 + 极简导航 + 视觉基线 | GOAL-09 / FR-J-01~04 |

### 1.2 设计范围

- 覆盖需求文档中的 7 个功能模块（A 用户管理 / B 简历匹配 / C 模拟面试 / D 复盘 / E 转行 / F 谈薪 / G 题库）
- 覆盖非功能需求（安全、性能、可靠性、可扩展性）
- 不含：移动端、多租户、支付计费（需求文档标记为 W 级）

---

## 2. 总体架构

### 2.1 架构风格

采用**单体模块化分层架构**（Modular Monolith）：

- 单一部署单元，内部按业务模块边界划分；
- 模块间通过**服务接口**通信，禁止跨层调用（如 API 层直接访问 Repository）；
- 后期如需拆分微服务，按模块边界即可切割。

**选型理由**：课程/毕设项目规模下，微服务引入分布式复杂度（服务发现、链路追踪、分布式事务）是过度设计；模块化单体保留清晰边界的同时，将运维与调试成本降到最低。

### 2.2 分层架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        Vue 3 前端                            │
│    页面 / SSE 客户端 / Web Speech API / (face-api.js 后期)     │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS / SSE / JSON
┌──────────────────────────────▼──────────────────────────────┐
│                        FastAPI 应用层                        │
│  ┌───────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │ API 路由层     │  │ 认证/中间件      │  │ SSE 流式端点    │   │
│  │ (Routers)     │  │ (JWT/限流/日志)  │  │ (面试对话流)    │   │
│  └───────┬───────┘  └───────┬────────┘  └───────┬────────┘   │
├──────────┴──────────────────┴──────────────────┴────────────┤
│                      业务服务层 (Services)                    │
│  ┌────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │简历×JD匹配  │ │复盘/画像  │ │转行诊断   │ │谈薪评估       │   │
│  │Service     │ │Service   │ │Service   │ │Service       │   │
│  └────────────┘ └──────────┘ └──────────┘ └──────────────┘   │
├──────────────────────────────┬──────────────────────────────┤
│             面试编排器 Interview Orchestrator                 │
│   ┌───────────────────────────────────────────────────┐      │
│   │  状态机(面试阶段)  +  有边界 Agent  +  动态RAG决策    │      │
│   └──────┬────────────┬────────────┬────────┬─────────┘      │
│          │            │            │        │                │
├──────────▼────────────▼────────────▼────────▼───────────────┤
│   领域服务层: Agent工具 检索服务  学习覆盖   回退规则           │
├──────────────────────────────┬──────────────────────────────┤
│                      数据访问层 (Repository)                 │
│   SQLAlchemy ORM         |       向量存储适配器               │
├──────────────┬──────────────┼──────────────┬────────────────┤
│   SQLite     │  PostgreSQL  │  ChromaDB    │   (Qdrant)     │
│  (MVP)       │  (预留/生产)   │  (MVP向量)   │  (预留/生产)   │
└──────────────┴──────────────┴──────────────┴────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  LLM Provider 适配层  │  ← 可插拔
                    │ DeepSeek/Kimi/GLM/  │
                    │ Qwen/OpenAI兼容接口  │
                    └─────────────────────┘
```

### 2.3 核心设计原则

| 原则 | 说明 | 来源 |
|---|---|---|
| **有边界 Agent** | 面试 Agent 单轮最多调用 3 次只读工具；工具仅限岗位知识/简历证据/学习覆盖；输出受 JSON Schema 约束 | 借鉴 InterWise |
| **业务真相在关系库** | 知识原子、面试记录等业务数据以关系数据库为准，向量库仅为可重建的语义索引 | 借鉴 InterWise |
| **动态 RAG 决策** | 检索结果不拼接成"参考答案"，而是作为"下一问策略"的决策输入 | 借鉴 InterWise |
| **失败降级** | LLM/向量库不可用时走规则回退，主流程不中断 | 需求 NFR-06/07 |
| **输入输出契约化** | 核心模块输入/输出使用 Pydantic 模型定义，前后端共用字段级规格 | 需求 2.2 数据规格 |
| **Provider 可插拔** | LLM 适配层统一接口，多供应商可切换 | 需求 NFR-09 |

---

## 3. 技术选型

### 3.1 选型决策表

| 层次 | 选项 | 决策 | 理由 |
|---|---|---|---|
| 后端语言 | Python 3.11+ | ✅ | AI 生态成熟、FastAPI 原生异步 |
| Web 框架 | FastAPI | ✅ | 异步、SSE 支持好、自动 OpenAPI、Pydantic v2 |
| ORM/迁移 | SQLAlchemy 2.0 + Alembic | ✅ | 类型安全查询、迁移管理 |
| 数据库 | SQLite(MVP) → PostgreSQL(生产) | ✅ | MVP 零配置；ORM 层抽象保证平滑迁移 |
| 向量库 | ChromaDB(MVP) → Qdrant(生产) | ✅ | 本地嵌入零运维；预留存储适配器 |
| AI 编排 | LangChain | ✅ | 工具调用/Agent/输出解析成熟 |
| Embedding | OpenAI 兼容接口 或 BAAI/bge-m3(本地) | ✅ | 中文效果好；可本地化 |
| 流式 | Server-Sent Events (SSE) | ✅ | 单向流足够文字面试；WebSocket 后续按需 |
| 认证 | JWT (python-jose / PyJWT) | ✅ | 无状态、适合前后端分离 |
| 密码/密钥 | bcrypt / AES-GCM | ✅ | 密码哈希 + API Key 加密存储 |
| 简历解析 | PyMuPDF / pdfplumber | ✅ | PDF 文本抽取稳定 |
| 前端 | Vue 3 + Element Plus + Vite + Axios | ✅ | 中文生态、组件丰富、与需求一致 |
| 语音 | Web Speech API（浏览器原生） | ✅ | 免后端语音服务；识别失败回退文字 |
| 视频 | face-api.js（后期 C 级需求） | ✅ | 浏览器端人脸/情绪分析 |
| 部署 | Docker Compose | ✅ | 一键启动、便于演示 |

### 3.2 目录结构（后端）

```
backend/
├── app/
│   ├── main.py                  # FastAPI 入口，CORS、中间件、路由注册
│   ├── core/                    # 配置、安全、常量
│   │   ├── config.py            # pydantic-settings 环境配置
│   │   ├── security.py          # JWT、bcrypt、AES 加解密
│   │   └── exceptions.py        # 统一异常与错误码
│   ├── api/                     # 路由层（只做参数校验与响应组装）
│   │   ├── deps.py              # 依赖注入（当前用户、DB session）
│   │   ├── auth.py              # 认证接口
│   │   ├── resume.py            # 简历诊断接口
│   │   ├── interview.py         # 面试接口（含 SSE 端点）
│   │   ├── report.py            # 复盘报告接口
│   │   ├── career.py            # 转行诊断接口
│   │   ├── salary.py            # 谈薪评估接口
│   │   ├── question.py          # 题库管理接口
│   │   └── provider.py          # LLM Provider 配置接口
│   ├── services/                # 业务服务层
│   │   ├── resume_matcher.py    # 简历×JD 匹配服务
│   │   ├── interview_orchestrator.py  # 面试编排器（状态机+Agent+决策）
│   │   ├── feedback.py          # 复盘与评分服务
│   │   ├── career_diagnosis.py  # 转行诊断服务
│   │   ├── salary_eval.py       # 谈薪评估服务
│   │   └── ability_profile.py   # 能力画像聚合服务
│   ├── agents/                  # 有边界 Agent 层
│   │   ├── interview_agent.py   # 面试官 Agent（工具绑定/限制/JSON契约）
│   │   ├── tools.py             # 只读工具（岗位知识/简历证据/学习覆盖）
│   │   └── prompts.py           # 各类角色 Prompt 模板
│   ├── rag/                     # 检索增强层
│   │   ├── retriever.py         # 检索服务（向量召回+过滤）
│   │   ├── next_question_decision.py  # 动态RAG：四信号→下一问策略
│   │   └── embedding.py         # Embedding 客户端封装
│   ├── models/                  # SQLAlchemy ORM
│   │   ├── user.py
│   │   ├── position.py
│   │   ├── knowledge_atom.py
│   │   ├── resume.py
│   │   ├── interview.py
│   │   ├── report.py
│   │   └── career.py
│   ├── schemas/                 # Pydantic 输入输出契约
│   ├── repositories/            # 数据访问层
│   ├── llm/                     # LLM Provider 适配层
│   │   ├── base.py              # Provider 抽象接口
│   │   ├── openai_compat.py     # OpenAI 兼容实现
│   │   └── factory.py           # Provider 工厂（按配置选择）
│   └── workers/                 # 后台任务（报告生成等）
├── alembic/                     # 数据库迁移
├── tests/                       # pytest 单元/集成测试
├── requirements.txt
├── pyproject.toml
└── Dockerfile
```

### 3.3 目录结构（前端）

```
frontend/
├── src/
│   ├── main.js
│   ├── App.vue
│   ├── router/                  # 路由（登录/诊断/面试/复盘/规划/题库/岗位广场）
│   ├── stores/                  # Pinia（用户、面试会话、Provider、岗位）
│   ├── api/                     # Axios 封装 + SSE 客户端
│   ├── views/
│   │   ├── Login.vue
│   │   ├── Dashboard.vue        # 首页：Lollipop 风格（大输入框 + 岗位卡片网格）
│   │   ├── JobMarket.vue        # 岗位广场（卡片网格/筛选/详情/一键面试）
│   │   ├── InterviewSetup.vue   # 面试设置向导（岗位→面试官→难度→简历）
│   │   ├── Interview.vue        # 面试会话（文字/语音）
│   │   ├── Report.vue           # 复盘报告
│   │   ├── ResumeDiagnosis.vue  # 简历×JD 诊断（向导式）
│   │   ├── OfferCompare.vue     # Offer 对比（向导式）
│   │   ├── CareerDiagnosis.vue  # 转行诊断
│   │   ├── SalarySim.vue        # 谈薪模拟
│   │   └── QuestionBank.vue     # 题库管理
│   └── components/
│       ├── layout/              # 极简导航/侧边栏（可折叠）
│       ├── wizard/              # 向导式通用组件（步骤条/卡片/底部导航）
│       └── common/              # 通用组件
├── package.json
└── vite.config.js
```

---

## 4. 核心子系统设计

### 4.1 面试编排器（Interview Orchestrator）★ 核心

**职责**：管理面试会话全生命周期，串联状态机、有边界 Agent 与动态 RAG 决策。

**状态机**：

```
┌────────┐   start   ┌──────────┐   首问     ┌──────────┐
│  created │ ──────► │ warming  │ ────────► │ asking   │
└────────┘          └──────────┘            └────┬─────┘
                                                 │ 收到回答
                                     ┌───────────▼───────────┐
                                     │  decide_next (动态RAG)  │
                                     │  四信号→下一问策略       │
                                     └────┬──────┬──────┬─────┘
              ┌────────────────────────────┘      │      └──────────────┐
              ▼                                   ▼                      ▼
        ┌──────────┐                        ┌──────────┐          ┌──────────┐
        │ asking   │ (深挖/换题)             │ 补充说明 │(补救)    │ finishing │
        └────┬─────┘                        └──────────┘          └────┬─────┘
             └─────────────── 继续循环 ◄──────────────────────┐        │
                                                              │        ▼
                                                              │  ┌──────────┐
                                                              └──│  reported │ (异步生成报告)
                                                                 └──────────┘
```

**状态说明**：

| 状态 | 触发条件 | 动作 |
|---|---|---|
| `created` | 创建面试会话 | 加载岗位/简历/已用知识点集合 |
| `warming` | 会话开始 | Agent 生成开场白与首个问题 |
| `asking` | Agent 提问完成 | 等待用户回答；记录策略与证据 |
| `decide_next` | 收到用户回答 | 运行四信号分析 → 决策下一问策略 |
| `finishing` | 达到结束条件 | 生成结束语，触发报告生成（异步） |
| `reported` | 报告生成完成 | 终态 |

**结束条件**：达到预设问题轮数（默认 6 轮）/ 用户主动结束 / 连续 3 轮空回答 / Agent 判定"可结束"。

### 4.2 有边界面试 Agent ★ 核心

**工具契约**：

| 工具名 | 作用域 | 单轮调用上限 | 输出 |
|---|---|---|---|
| `search_knowledge` | 岗位知识原子检索 | 1 次/轮 | `[{atom_id, question, tags, difficulty}]` |
| `get_resume_evidence` | 简历证据查询 | 1 次/轮 | `{skills, experiences, projects}` |
| `get_coverage` | 已问知识点覆盖 | 1 次/轮 | `{asked_atom_ids, covered_tags}` |

**约束实现**：
- 单轮总工具调用 ≤ 3 次（计数在会话上下文维护）；
- Agent 输出经 **JSON Schema 校验**（`interviewer_plan`：`{strategy, question, tool_plan}`）；
- 工具只读、无副作用；不持久化 Agent 思维链；
- 非法输出/超时 → **规则回退**：从候选知识原子按未问过+匹配度降序取题。

**Agent 决策输入**（Prompt 注入）：

```
角色：资深技术面试官
输入：岗位要求 / 简历证据 / 面试阶段 / 已问知识点 / 用户最新回答摘要 / 检索召回候选
输出：interviewer_plan { strategy: "deep_dive"|"remedy"|"switch_topic"|"project_probe",
                         question: "...",
                         tool_plan: [...] }
约束：工具调用≤3次；问题只含一个考察点；不得输出思维链
```

### 4.3 动态 RAG 追问决策 ★ 核心

**四类追问信号 → 策略映射**：

| 信号 | 识别方式 | 策略 |
|---|---|---|
| 低信息回答 | 回答长度/关键词密度低于阈值 | `deep_dive` 深挖：追问"请展开讲讲具体实现" |
| 弱召回 | 问题涉及的知识原子未被用户命中要点 | `remedy` 补救：换同知识点低难度题 |
| 连续回避 | ≥2 轮用户转移话题/答非所问 | `switch_topic` 换知识点 |
| 已用知识点排除 | 已问过的 atom 从召回中过滤 | 过滤 + 高匹配度候选 |

**决策流程**：
1. 用户回答 → 信号提取（规则 + LLM 辅助标注）；
2. 信号向量 → 结合检索召回（排除已用 atom，按缺口权重重排）；
3. 策略输出 → Agent 生成问题 → 校验 → 返回前端。

### 4.4 简历 × JD 匹配服务

```
输入: PDF/文本简历 → 解析(结构化画像) + JD文本
流程:
  1. 简历解析: PyMuPDF 抽文本 → LLM 结构化提取(技能/经历/项目/教育)
  2. JD解析: LLM 提取技能要求与任职资格
  3. 匹配计算:
     - Embedding 语义相似度(简历技能 × JD要求)
     - LLM 差距分析: 每项JD要求 → {required_level, current_level, suggestion}
  4. 输出: match_score(0-100) + gaps[] + resume_suggestions[]
```

**一致性要求**：对同一简历+JD，评分需稳定可复现（LLM temperature=0，结构化输出）。

### 4.5 复盘与能力画像服务

- **复盘报告**（面试结束后异步生成）：读取消息流 → LLM 按维度评分（tech/expression/logic/project）→ 逐题反馈；
- **能力画像**：多场面试的维度分聚合（加权平均 + 趋势斜率），输出技能雷达图数据；
- **弱点扑灭**：统计"连续答差"的知识标签 → 推送学习材料 + 专项练习建议。

### 4.6 转行诊断 / 谈薪评估服务

- 转行诊断：`当前岗位 → 目标岗位`，LLM 生成双岗位能力模型对比，输出 `transferable[] / gaps[] / career_path[]`；
- 谈薪评估：技能栈+年限+城市 → LLM 结合内置市场参考价表给出区间与策略；谈薪模拟复用面试编排器的角色扮演能力（HR 人设）。

### 4.7 题库与知识原子

- 知识原子状态机：`draft → published → archived`（ADMIN 可发布公共题库）；
- **发布约束**：仅 `published` 状态可被检索与追问（向量索引只收录 published）；
- 向量索引重建：知识原子变更后按需重建 Chroma 集合，业务数据不受影响（可重建原则）。

### 4.8 面试官角色系统（Interviewer）

**设计目标**：将"面试官人设"从硬编码 Prompt 中抽离为可配置数据，支持按角色注入差异化提问风格（FR-C-10 / FR-I-01~03）。

**Interviewer 模型字段**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | str | 角色名，如「CTO 技术面」「HR 综合面」 |
| `title` | str | 角色标签/职务描述 |
| `persona` | text | 人设描述（注入 system prompt 的角色设定） |
| `style` | text | 提问风格要点（注入 prompt 的风格指令） |
| `interview_type` | str | 适用模式：normal / switch / salary / all |
| `difficulty_bias` | int | 难度偏移（-1 偏易 / 0 标准 / +1 偏难），叠加用户所选难度 |
| `is_public` | bool | 是否内置公开角色（ADMIN 维护） |
| `created_by` | FK | 自建角色归属用户 |

**与编排器集成**：

```
创建面试(携带 interviewer_id + difficulty)
  → 编排器加载 Interviewer
  → Agent Prompt 注入:
      system = 角色persona + style
      difficulty 指令 = 难度档位模板(easy/normal/hard) × difficulty_bias 修正
  → 状态机与动态RAG逻辑不变（角色只影响"怎么说"，不改变"问什么"的决策框架）
  → 面试记录持久化 interviewer_id / difficulty
```

**设计约束**：面试官角色**不影响**动态 RAG 的追问信号决策骨架（那是能力正确性的核心），只调节语言风格、深度档位与容错度，保证角色可配置而不破坏面试质量。

### 4.9 难度档位体系（Difficulty）

| 档位 | 标识 | 提问深度 | 追问强度 | 容错度 | 典型题型 |
|---|---|---|---|---|---|
| 简单 | `easy` | 基础概念、定义类 | 低（少深挖） | 高（给提示引导） | 概念解释、简单场景 |
| 标准 | `normal` | 常规应用、原理 | 中（正常深挖） | 中 | 原理+简单场景分析 |
| 困难 | `hard` | 原理深挖、组合考察 | 高（持续深挖） | 低（少提示） | 场景设计、组合知识点、压测 |

**实现位置**：
- `agents/prompts.py`：三套难度指令模板 + 角色 persona 拼接函数；
- `services/interview_orchestrator.py`：创建会话时将 `difficulty` 与 `interviewer_id` 写入 `config_json`；
- `rag/next_question_decision.py`：追问策略按难度加权（如 hard 档提升 `deep_dive` 触发概率、easy 档提升 `remedy` 与引导）。

**默认值联动**：岗位 `positions.difficulty` → 面试默认难度；用户可手动覆盖（FR-C-11）。

### 4.10 岗位广场（Job Market）

**数据源分层**（FR-H-02）：

| 层 | 来源 | 可见性 | 说明 |
|---|---|---|---|
| PUBLIC | ADMIN 内置岗位库 | 所有用户 | 系统预设的通用岗位（后端/前端/算法/产品/运营…） |
| PRIVATE | 用户自建 | 仅本人 | 用户针对具体公司/岗位创建 |
| SYNC（预留） | 外部招聘 API | 按数据源 | 预留接口位，MVP 不实现 |

**岗位卡片 → 面试链路**：

```
岗位广场(卡片网格 + 筛选)
  ├─ 点击卡片 → 岗位详情(技能/参考JD/难度)
  │    ├─「开始面试」→ InterviewSetup 向导(面试官→难度→简历) → 创建面试
  │    └─「带去诊断」→ 岗位参考 JD 预填到 ResumeDiagnosis
  └─ 首页大输入框搜索 → 命中岗位卡片 or 生成"自定义岗位"入口
```

**岗位模型扩展字段**：`company / salary_range_json / location / source(public/private/sync) / description / jd_text`。

### 4.11 前端设计系统（向导式 + 极简导航）

**布局骨架（全站统一）**：

```
┌────────────────────────────────────────────────┐
│  极简顶栏: 品牌 + 全局搜索 + 用户菜单            │
│  ┌──────┬────────────────────────────────────┐ │
│  │ 窄侧边│ 主内容区（大留白，居中 ≤880px）       │ │
│  │ 栏(可 │  ┌ 步骤条(可选，向导页) ─────────┐  │ │
│  │ 折叠) │  │ 单卡片内容区                  │  │ │
│  │       │  └────────────────────────────┘  │ │
│  │       │  ┌ 底部导航: 上一步/下一步 ──────┐  │ │
│  └──────┴──┴────────────────────────────────┘ │
└────────────────────────────────────────────────┘
```

**设计令牌**：`--app-brand`（主色）、`--app-radius-lg/md`（大/中圆角）、`--app-shadow-sm/md`（阴影）、`--ease-out`（动效缓动）；步骤切换统一 300ms 上浮淡入。

**向导式通用组件（`components/wizard/`）**：
- `WizardBar.vue`：步骤条（圆点徽章 + 连接线，已完成绿色对勾、当前高亮，可点击回退）；
- `WizardCard.vue`：单卡片容器（头部渐变图标 + 标题 + 描述 + 内容插槽）；
- `WizardNav.vue`：底部导航（上一步 / 下一步 / 主操作按钮 + 提示文案）。

**首页（Dashboard）Lollipop 风格**：居中大输入框"告诉 AI 你想面试的岗位" + 岗位卡片网格 + 快捷功能入口，侧边栏弱化为窄栏。

---

## 5. 数据模型设计

### 5.1 ER 概要

```
users 1───N providers
users 1───N resumes
users 1───N interviews
positions 1───N knowledge_atoms
positions 1───N interviews
interviewers 1───N interviews
resumes 1───N match_diagnostics
interviews 1───N interview_messages
interviews 1───1 reports
users 1───N career_plans
users 1───N salary_evals
users 1───N ability_profiles
users 1───N interviewers          (自建面试官角色)
users 1───N positions             (自建岗位)
users 1───N user_favorites        (岗位收藏, C级)
```

### 5.2 核心表设计

| 表 | 关键字段 | 说明 |
|---|---|---|
| `users` | id, username, password_hash, email, role(user/admin), target_city, years_of_exp, target_position, created_at | 用户与资料 |
| `llm_providers` | id, user_id, provider_name, api_key_encrypted, base_url, model, is_active | API Key 加密存储 |
| `positions` | id, name, direction, difficulty(easy/normal/hard), skills_json, company, salary_range_json, location, source(public/private/sync), jd_text, description, is_public, creator_id, status | 岗位，方向可配置，含招聘信息（岗位广场数据源） |
| `interviewers` | id, name, title, persona, style, interview_type(normal/switch/salary/all), difficulty_bias, is_public, created_by | 面试官角色库（人设+风格+难度偏移） |
| `knowledge_atoms` | id, position_id, question, reference_points_json, tags_json, difficulty, status(draft/published/archived), created_by | 知识原子 |
| `resumes` | id, user_id, file_path, parsed_json, skills_json, created_at | 简历画像 |
| `match_diagnostics` | id, user_id, resume_id, jd_text, match_score, gaps_json, suggestions_json, created_at | 诊断记录 |
| `interviews` | id, user_id, position_id, resume_id, interviewer_id, difficulty(easy/normal/hard), mode(text/voice/video), interview_type(normal/switch/salary), status, config_json, created_at, finished_at | 面试会话（含面试官与难度） |
| `interview_messages` | id, interview_id, role, content, strategy, evidence_atom_ids_json, created_at | 消息流（含策略与证据） |
| `reports` | id, interview_id, overall_score, dimensions_json, question_feedback_json, weak_points_json, created_at | 复盘报告 |
| `ability_profiles` | id, user_id, dimensions_json, updated_at | 能力画像聚合 |
| `career_plans` | id, user_id, from_position, to_position, transferable_json, gaps_json, roadmap_json, created_at | 转行规划 |
| `salary_evals` | id, user_id, skill_stack_json, years, city, target_position, result_json, created_at | 谈薪评估 |

> JSON 字段使用 SQLite JSON 类型（可迁移到 PostgreSQL JSONB）。

---

## 6. 接口设计

### 6.1 REST API 概览

| 模块 | 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|---|
| 认证 | POST | `/api/auth/register` | 注册 | 无 |
| 认证 | POST | `/api/auth/login` | 登录，返回 JWT | 无 |
| Provider | GET/POST/PUT | `/api/providers` | 配置 LLM Provider | JWT |
| 简历 | POST | `/api/resumes/upload` | 上传 PDF/文本 | JWT |
| 诊断 | POST | `/api/diagnostics` | 简历×JD 匹配诊断 | JWT |
| 诊断 | GET | `/api/diagnostics/{id}` | 查询诊断结果 | JWT |
| 面试 | POST | `/api/interviews` | 创建面试会话（携带 interviewer_id + difficulty） | JWT |
| 面试 | GET | `/api/interviews/{id}/stream` | SSE 面试对话流 | JWT |
| 面试 | POST | `/api/interviews/{id}/answer` | 提交回答（SSE 用） | JWT |
| 面试 | POST | `/api/interviews/{id}/finish` | 主动结束 | JWT |
| 面试官 | GET | `/api/interviewers` | 面试官角色列表（按 interview_type 过滤） | JWT |
| 面试官 | POST | `/api/interviewers` | 自建面试官角色 | JWT |
| 岗位 | GET | `/api/positions` | 岗位广场列表（筛选：方向/难度/来源 + 关键词搜索） | JWT |
| 岗位 | GET | `/api/positions/{id}` | 岗位详情（技能/JD/薪资区间） | JWT |
| 岗位 | POST | `/api/positions` | 用户自建岗位 | JWT |
| 报告 | GET | `/api/reports/{id}` | 查询复盘报告 | JWT |
| 转行 | POST | `/api/career/diagnosis` | 转行诊断 | JWT |
| 谈薪 | POST | `/api/salary/evaluate` | 薪资评估 | JWT |
| 题库 | CRUD | `/api/questions` | 知识原子管理（ADMIN 发布） | JWT+角色 |

**岗位创建请求（POST /api/positions）**：

```json
{
  "name": "后端开发工程师",
  "direction": "backend",
  "difficulty": "normal",
  "skills": ["Python", "MySQL", "FastAPI"],
  "company": "某互联网公司",
  "salary_range": { "min": 20000, "max": 35000 },
  "location": "杭州",
  "jd_text": "负责……任职要求……"
}
```

**面试创建请求（POST /api/interviews）扩展字段**：

```json
{
  "position_id": 1,
  "resume_id": 2,
  "interviewer_id": 3,
  "difficulty": "hard",
  "interview_type": "normal",
  "max_rounds": 6
}
```

### 6.2 SSE 面试流契约

**客户端 → 服务器**（POST `/api/interviews/{id}/answer`）：

```json
{ "content": "我在项目里用 Redis 做了缓存……" }
```

**服务器 → 客户端**（SSE 事件流）：

```
event: question      data: {"strategy": "deep_dive", "question": "你说的缓存击穿，具体怎么解决的？"}
event: hint          data: {"type": "retry", "message": "请输入你的回答"}
event: finished      data: {"message": "面试结束，正在生成报告……"}
```

| 事件 | 时机 | 数据 |
|---|---|---|
| `question` | Agent 提问 | `{strategy, question}` |
| `hint` | 输入校验失败/超时 | `{type, message}` |
| `finished` | 面试结束 | `{message, report_id}` |

---

## 7. 关键流程时序

### 7.1 模拟面试主流程（文字/SSE）

```
前端            API            面试编排器        有边界Agent       RAG/检索       LLM
 │ POST create  │                 │                │              │           │
 │ ───────────► │  创建会话+状态机  │                │              │           │
 │              │ ──────────────► │  warming        │              │           │
 │              │                 │ 首问决策         │ 工具:岗位检索   │           │
 │              │                 │ ──────────────► │ ───────────► │           │
 │              │                 │                 │ 生成问题       │ ────────► │
 │  SSE question │ ◄───────────── │ ◄────────────── │              │           │
 │ POST answer  │                 │  receiving      │              │           │
 │ ───────────► │ ──────────────► │  四信号分析      │              │           │
 │              │                 │ ────────────────────────────► 向量召回     │
 │              │                 │  decide_next     │              │           │
 │              │                 │ ──────────────► 工具+生成问题    │ ────────► │
 │  SSE question │ ◄───────────── │ ◄────────────── │              │           │
 │   ...循环至结束...              │                 │              │           │
 │              │                 │ finishing       │              │           │
 │              │                 │ 触发报告生成(异步)│              │           │
 │ SSE finished │ ◄───────────── │                 │              │           │
```

### 7.2 简历×JD 诊断流程

```
前端 → 上传简历+JD → 解析(LLM结构化) → Embedding → 匹配计算 → gaps分析(LLM) → 返回诊断报告
```

---

## 8. 非功能架构

| 维度 | 设计 |
|---|---|
| **安全** | JWT 无状态鉴权；密码 bcrypt；API Key AES-GCM 加密；面试上下文归属校验（仅本人可读）；限流中间件 |
| **可靠性** | LLM 故障/超时/非法输出 → 规则回退；向量库不可用 → 关键词降级检索；报告生成异步重试 |
| **可扩展性** | Provider 工厂模式（新增供应商仅需实现 `base.py` 接口）；岗位方向配置化；向量存储适配器抽象 |
| **性能** | SSE 流式首 token < 2s；诊断 < 30s；报告异步生成；面试消息增量持久化 |
| **可维护** | 分层清晰；Pydantic 契约；pytest 单元测试覆盖核心编排逻辑；Alembic 迁移管理 |

---

## 9. 部署架构

```
┌──────────────── Docker Compose ────────────────┐
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ frontend │──│ backend  │──│  sqlite/vol  │  │
│  │  (nginx) │  │ (uvicorn)│  │  (数据卷)     │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
│                     │                          │
│              ┌──────┴──────┐                   │
│              │ chromadb    │ (可选 Docker 化)   │
│              └─────────────┘                   │
└────────────────────────────────────────────────┘
```

**环境变量**（`.env`）：`DATABASE_URL`、`JWT_SECRET`、`AES_KEY`、`DEFAULT_EMBEDDING_MODEL`、`VITE_API_BASE` 等。

---

## 10. 风险与应对

| 风险 | 影响 | 应对 |
|---|---|---|
| LLM 输出不稳定（JSON 解析失败） | 面试流程中断 | 严格 Schema 校验 + 规则回退（FR-C-09） |
| Embedding 模型质量影响召回 | 追问质量下降 | 提供可评测的检索配置；预留 rerank 接口 |
| 前端语音识别兼容性 | 语音面试体验差 | 降级为文字输入（边界表已定） |
| SQLite→PostgreSQL 迁移成本 | 部署环境差异 | 全程 SQLAlchemy 方言兼容写法 |
| 视频面试（face-api.js）浏览器兼容 | C 级功能延期 | 标记为可选功能，不影响 MVP |

---

## 11. 演进路径

| 阶段 | 架构扩展 |
|---|---|
| Phase 1 MVP | 本文档全量实现（SQLite + ChromaDB + 文字/语音面试 + 难度选择 + 岗位广场基础 + 向导式骨架） |
| Phase 2 | 面试官角色库、能力画像/成长追踪/转行诊断/谈薪模块、首页 Lollipop 风格 |
| Phase 3 | 公共题库审核、视频面试（face-api.js）、岗位详情与搜索、我的岗位 |
| Phase 4 | PostgreSQL + Qdrant 生产化、多岗位方向扩展、外部招聘 API 同步（SYNC 源）、离线 RAG 评测 |

---

*（文档结束）*
