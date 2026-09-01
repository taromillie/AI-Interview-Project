# 数据备份与恢复

项目数据由两部分组成，二者都随后端数据目录持久化：

| 数据 | 位置 | 说明 |
| --- | --- | --- |
| 业务数据（用户/简历/面试/报告等） | SQLite 文件 `app.db` | 核心数据 |
| 向量库 | `data/chroma/` | JD 知识库向量索引，可重建（删除后知识库退化为关键词检索，不影响业务数据） |

> 备份与恢复前，建议先停止后端写入，保证数据一致性：
> - Docker：`docker compose stop backend`
> - 本地：停止 uvicorn 进程

## Docker 部署（命名卷 `backend_data`）

### 备份

```bash
# Linux / macOS
docker run --rm -v backend_data:/data -v "$PWD":/backup alpine \
  sh -c "cd /data && tar czf /backup/backend_data_$(date +%Y%m%d_%H%M).tar.gz ."

# Windows PowerShell
docker run --rm -v backend_data:/data -v "${PWD}:/backup" alpine `
  sh -c "cd /data && tar czf /backup/backend_data.tar.gz ."
```

备份产物为仓库目录下的 `backend_data_YYYYmmdd_HHMM.tar.gz`，请转移到安全位置。

### 恢复

```bash
# 将备份文件放到当前目录后执行（Linux / macOS）
docker run --rm -v backend_data:/data -v "$PWD":/backup alpine \
  sh -c "rm -rf /data/* && tar xzf /backup/backend_data_20250101_1200.tar.gz -C /data"

# 恢复后重启服务
docker compose up -d
```

## 本地部署（源码运行）

数据文件位于后端工作目录：

- `backend/app.db`
- `backend/data/chroma/`

直接复制这两个路径即可完成备份；恢复时复制回原路径后重启服务。

## 建议

- 备份时机：**每次发布前** + **定期**（按数据变更频率，如每日/每周）
- 仅备份 `app.db` 即可保证业务数据不丢；向量库可在恢复后通过"JD 重新导入/同步"重建
- 恢复后验证：`curl http://localhost:8000/health`，确认 `status=ok` 且用户数据可见
