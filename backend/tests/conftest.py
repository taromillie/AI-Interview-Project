"""pytest 全局配置：使用独立临时数据库，避免污染开发库 app.db。

必须在导入 app 之前设置 DATABASE_URL 环境变量（引擎在 import 时创建）。
"""
import os
import tempfile
import uuid

_db_dir = tempfile.mkdtemp(prefix="pytest_db_")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_db_dir, f'test_{uuid.uuid4().hex}.db')}"
# 测试环境：开发模式 + 强密钥，避免生产密钥强校验拦截（密钥校验本身有独立测试覆盖）
os.environ["DEBUG"] = "true"
os.environ["JWT_SECRET"] = "test-only-jwt-secret-0123456789abcdef"
os.environ["AES_KEY"] = "test-only-aes-key-0123456789abcdef"
