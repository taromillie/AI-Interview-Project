# AI 模拟面试官与职业规划系统

面向求职者的 AI 面试训练与职业规划平台：简历 × JD 智能匹配诊断、动态追问模拟面试、面试复盘与能力成长追踪、转行诊断、跳槽谈薪模拟。

## 功能特性

- **简历 × JD 智能匹配**：上传简历 + 粘贴目标岗位 JD，30 秒内输出匹配分、缺口清单与优化建议
- **动态追问模拟面试**：有边界的面试 Agent，基于回答动态决策"深挖/补救/换题/项目追问"
- **面试复盘与成长追踪**：逐题批改、四维度评分、多场面试能力画像与趋势
- **转行诊断**：双岗位能力模型对比、可迁移技能图谱、转行专属面试模式
- **跳槽谈薪**：HR 人设谈薪模拟、薪资竞争力评估
- **多 LLM Provider 可插拔**：支持 DeepSeek / Kimi / GLM / Qwen / 任意 OpenAI 兼容接口

## 技术栈

| 层次 | 技术 |
|---|---|
| 后端 | Python 3.11+ / FastAPI / SQLAlchemy 2.0 / Alembic / LangChain |
| 数据 | SQLite（MVP）→ PostgreSQL / ChromaDB 向量库 |
| 前端 | Vue 3 / Element Plus / Vite / Axios / SSE |
| 部署 | Docker Compose |

## 快速开始

### 方式一：Docker Compose（推荐演示）

```bash
docker compose up --build
```

### 方式二：本地开发

**后端：**

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 按需修改
uvicorn app.main:app --reload --port 8000
```

接口文档：http://localhost:8000/docs

**前端：**

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

## 使用前配置

1. 注册账号并登录
2. 在"模型配置"页填入你的 LLM API Key（支持 DeepSeek/Kimi/GLM/Qwen 等 OpenAI 兼容接口）
3. 上传简历 → 粘贴 JD → 开始诊断 → 发起模拟面试

## 文档

- [需求文档](docs/requirements.md)
- [架构设计文档](docs/design.md)

## 开发进度

### Phase 1 · MVP 闭环 ✅（2026-08-27 ~ 08-28）

- ✅ 注册/登录、LLM Provider 配置
- ✅ 简历上传（PDF/TXT/粘贴文本）+ LLM 结构化解析
- ✅ 简历×JD 匹配诊断：匹配分、技能缺口、优化建议
- ✅ 文字模拟面试：SSE 流式对话、动态追问（深挖/项目追问/换题）、轮数上限自动结束、LLM 失败规则回退兜底
- ✅ 复盘报告：四维度评分、逐题批改、弱点标签、总评建议（LLM 失败自动规则降级）
- ✅ 题库管理：岗位/题目维护、草稿→发布流转
- ✅ 后端集成测试（FakeLLM 全链路 6/6 通过）+ 前端构建通过

### Phase 2 · 职业规划与成长追踪 ✅（2026-08-28 ~ 08-28）

- ✅ 转行诊断：当前岗位 → 目标岗位，LLM 生成可迁移技能 / 技能缺口 / 学习路径，历史记录可回看
- ✅ 谈薪评估：技能栈 + 年限 + 城市 → 薪资区间（min/mid/max）+ 影响因素 + 可执行谈薪策略，历史记录可回看
- ✅ 能力画像：多场面试复盘报告聚合 → 四维度雷达图 + 技能评分 + 高频弱点（SVG 自绘，零依赖）
- ✅ 三模块均内置规则兜底（LLM 失败自动降级），SQLite 轻量迁移（ALTER TABLE ADD COLUMN）

### 待办（后续 Phase）

- 语音/视频面试、真实面试复盘、公共题库、成长趋势（时间维度折线）

## 目录结构

```
├── backend/          # FastAPI 后端
│   └── app/
│       ├── api/          # 路由层
│       ├── services/     # 业务服务层
│       ├── agents/       # 有边界面试 Agent
│       ├── rag/          # 检索增强层
│       ├── llm/          # LLM Provider 适配层
│       ├── models/       # SQLAlchemy ORM
│       ├── schemas/      # Pydantic 契约
│       └── core/         # 配置/安全/异常
├── frontend/         # Vue 3 前端
├── docs/             # 需求/设计文档
└── docker-compose.yml
```
