"""启动后端：脚本所在目录设为工作目录并加入 sys.path，再运行 uvicorn。"""
import os
import sys

_BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(_BASE)
sys.path.insert(0, _BASE)

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
