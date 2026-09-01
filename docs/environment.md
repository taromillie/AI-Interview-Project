# 部署环境变量说明

后端配置由环境变量 / `.env` 文件驱动（pydantic-settings），模板见 `backend/.env.example`。
Docker 部署时，`docker-compose.yml` 会从仓库根目录的 `.env` 透传部分变量（未配置时使用下表默认值）。

> 原则：**未显式配置即视为生产模式**。生产部署必须设置强密钥，否则容器拒绝启动。

## 应用

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `APP_NAME` | AI 模拟面试官与职业规划系统 | 应用名称 |
| `DEBUG` | `false` | `false`=生产模式（默认密钥被强校验拦截）；`true`=开发模式（默认密钥可用，仅告警）。**本地开发必须显式设为 `true`** |
| `LOG_LEVEL` | `INFO` | 日志级别：`DEBUG` / `INFO` / `WARNING` / `ERROR` |

## 数据库

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./app.db` | MVP 使用 SQLite；生产可切换 PostgreSQL，如 `postgresql+psycopg://user:pass@localhost:5432/ai_interview` |

## 向量库（可选增强）

未配置 Embedding 时自动降级为关键词检索，不影响核心功能。

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `VECTOR_DB_PATH` | `./data/chroma` | Chroma 向量库存储路径 |
| `VECTOR_COLLECTION` | `knowledge_atoms` | 向量集合名 |
| `EMBEDDING_ENABLED` | `false` | 是否启用向量检索 |
| `EMBEDDING_BASE_URL` | 空 | OpenAI 兼容地址，如 `https://api.openai.com/v1` |
| `EMBEDDING_API_KEY` | 空 | Embedding API Key |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | 向量模型 |
| `EMBEDDING_TIMEOUT` | `30` | 请求超时（秒） |

## 安全（生产必配）

| 变量 | 默认值 | 要求 |
| --- | --- | --- |
| `JWT_SECRET` | `please-change-this-secret` | 生产模式须 ≥32 字符且非默认值，否则拒绝启动 |
| `JWT_ALGORITHM` | `HS256` | 签名算法 |
| `JWT_EXPIRE_MINUTES` | `10080`（7 天） | Token 有效期 |
| `AES_KEY` | `please-change-this-aes-key-32bytes!` | 生产模式须 32 字节且非默认值，否则拒绝启动 |

> 快速生成强密钥：
> - Linux/macOS：`openssl rand -hex 32`
> - Windows PowerShell：`-join ((1..64) | ForEach-Object { '{0:x}' -f (Get-Random -Max 16) })`

## CORS

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | 逗号分隔的允许来源 |

## 默认模型（用户未在设置页配置时的回退）

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `DEFAULT_LLM_MODEL` | `gpt-4o-mini` | 回退模型名 |
| `DEFAULT_LLM_BASE_URL` | `https://api.openai.com/v1` | OpenAI 兼容 Base URL |

## 岗位采集（Docker 透传）

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `JOB_SOURCE_ENABLED` | `jobui` | 逗号分隔：`jobui`(职友集，中国真实岗位) / `builtin`(离线示例兜底) |
| `JOB_SYNC_ON_STARTUP` | `true` | 启动后立即同步一次岗位 |
| `JOB_SYNC_INTERVAL_HOURS` | `0.5` | 自动同步间隔（小时） |
