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
