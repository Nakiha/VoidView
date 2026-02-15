"""启动服务端"""

import sys
from pathlib import Path

# 添加 shared 模块到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "shared" / "src"))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "server.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
