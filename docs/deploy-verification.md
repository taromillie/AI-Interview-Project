# Docker 实机验证清单

> 目的：在**有 Docker 的机器**上执行 `docker compose up --build` 一键部署的完整验证。
> 当前开发机无 Docker，已完成全部可离线等价验证（见 `next-step-plan.md`「P2 部署配置复查」），
> 本清单用于补足实机环节。预计耗时约 15 分钟。

## 0. 前置条件

- Docker Engine ≥ 24（含 Compose v2 插件），或 Docker Desktop
- 空闲端口：`8000`（后端）、`5173`（前端 Nginx 映射）
- 可用磁盘 ≥ 2GB（前端镜像含 node_modules 构建层）

## 1. 构建与启动

```bash
cd <项目根目录>          # 含 docker-compose.yml 的目录
docker compose up --build -d
```

预期：构建后端（Python 3.11 + requirements）与前端（node:20-alpine 构建 + nginx:alpine 托管）两个镜像并启动。

## 2. 验证清单

| # | 检查项 | 命令 / 操作 | 预期结果 |
|---|--------|------------|---------|
| 1 | 容器状态 | `docker compose ps` | 2 个容器 `Up`（healthy） |
| 2 | 后端健康 | `curl http://localhost:8000/health` | `{"status":"ok","database":"ok",...}` |
| 3 | 前端首页 | 浏览器访问 `http://localhost:5173` | 登录页正常加载，无控制台报错 |
| 4 | 登录链路 | 注册 → 登录（页面操作） | 登录成功进入首页 |
| 5 | 数据库持久化 | 登录后：`docker compose restart backend`，刷新页面 | 会话/数据不丢失（volume `backend_data` 持久化 `/app/data/app.db`） |
| 6 | 面试主流程 | 模拟面试：创建会话 → 回答 → 结束 → 查看报告 | 全流程可用（SSE 流式回复正常） |
| 7 | 题库导入 | 题库页 → 导入 JSON/MD | 新建/跳过/失败统计展示 |
| 8 | 岗位收藏/投递 | 岗位库收藏 + 设置投递状态 | 刷新后状态保留 |
| 9 | 日志级别 | `docker compose exec backend sh -c "echo \$LOG_LEVEL"` | 默认 `INFO`；`.env` 中设置 `LOG_LEVEL=DEBUG` 后 `docker compose up -d --force-recreate backend` 可见 DEBUG 日志 |
| 10 | 访问日志 | `docker compose logs backend` | 请求日志含方法/路径/状态码/耗时 |
| 11 | 前端产物 | `docker compose exec frontend ls /usr/share/nginx/html/assets` | 含按需引入的 el-* 分包文件 |
| 12 | 优雅停止 | `docker compose down` | 容器停止，数据 volume 保留（再次 up 数据仍在） |

## 3. 配置速查

- 后端端口：`docker-compose.yml` 中 `services.backend.ports`（默认 `8000:8000`）
- 前端端口：`services.frontend.ports`（默认 `5173:80`，即宿主机 5173 → Nginx 80）
- 网络：前端所有请求（含 SSE 流式，路径 `/api/interviews/{id}/start`）统一走 `/api/` 前缀，Nginx `location /api/` 反代到 `backend:8000`（见 `frontend/nginx.conf`，含 `proxy_buffering off` 保证 SSE 流式）
- 环境变量：`.env.example` 复制为 `.env`；`LOG_LEVEL` 控制后端日志级别（默认 `INFO`）
- 安全密钥：容器内 `DEBUG` 默认 `false`（生产模式），必须设置强 `JWT_SECRET`（≥32 字符）与 `AES_KEY`（32 字节），否则容器因密钥强校验拒绝启动；仅本地演示可设 `DEBUG=true` 使用默认密钥
- 健康检查：`/health`（就绪，含 DB 探测）、`/health/live`（存活，不依赖外部）；compose healthcheck 仅当 `/health` 返回 `status=ok` 时标记 healthy
- 数据持久化：命名卷 `backend_data` → 容器内 `/app/data/app.db`（含 SQLite + chroma 向量库）

## 4. 常见问题

- **端口占用**：`docker compose up` 报端口冲突 → 释放端口或修改 compose 映射。
- **前端页面 API 404**：确认 Nginx `location /api/` 反代到 `backend:8000`（容器内主机名，勿用 localhost）；浏览器控制台确认请求路径以 `/api/` 开头。
- **后端启动失败（database 异常）**：`docker compose logs backend` 查看迁移错误；`/app/data` 目录权限不足时可 `docker compose exec backend mkdir -p /app/data`。
- **构建慢**：前端镜像依赖 `npm ci`，首构建约 3-5 分钟；后续构建命中 Docker 层缓存。
- **SSE 流式回复不工作**：确认 Nginx 配置中 `proxy_buffering off` 已生效（本项目已配置）；若手动反代了 `/sse` 前缀，注意项目实际路径是 `/api/interviews/{id}/start`。

## 5. 完成标准

清单 1-12 全部为预期结果即通过；任一失败请记录现象与日志，反馈到部署配置问题。

## 6. 与本地等价验证的差异

| 差异点 | 本地开发（已验） | Docker 实机（本清单） |
|--------|----------------|---------------------|
| Python 环境 | 本机 `.venv`（3.14） | 镜像内 Python 3.11（requirements 安装） |
| Node 环境 | 本机 node_modules | 镜像内 node:20-alpine `npm ci` |
| 静态托管 | Vite dev server（5173） | Nginx 生产构建产物（80） |
| 数据存储 | 本机 `app.db` | volume 挂载 `app.db` |
| 网络 | localhost 直连 | 容器网络 + Nginx 反代 `/api`（含 SSE 流式） |
