"""VoidView 客户端入口"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "shared" / "src"))

from app.application import VoidViewApplication


def main():
    """主函数"""
    app = VoidViewApplication()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
