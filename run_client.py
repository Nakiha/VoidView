"""启动客户端"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "shared" / "src"))
sys.path.insert(0, str(project_root / "client" / "src"))

from app.application import VoidViewApplication

if __name__ == "__main__":
    app = VoidViewApplication()
    sys.exit(app.run())
