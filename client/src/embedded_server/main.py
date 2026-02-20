"""嵌入式服务器入口 - 用于客户端本地模式"""

import sys
import argparse
from pathlib import Path

# 确定服务器代码路径
_embedded_dir = Path(__file__).parent

# 检查是否在打包模式下运行
if getattr(sys, 'frozen', False):
    # PyInstaller 打包模式
    _base_path = Path(sys._MEIPASS)
    _server_dir = _base_path / "server"
else:
    # 开发模式
    _project_root = _embedded_dir.parent.parent.parent.parent
    _server_dir = _project_root / "server"

# 添加服务器路径到 sys.path
if _server_dir.exists():
    sys.path.insert(0, str(_server_dir))

# 添加 shared 模块路径
if getattr(sys, 'frozen', False):
    _shared_dir = _base_path
else:
    _project_root = _embedded_dir.parent.parent.parent.parent
    _shared_dir = _project_root / "shared" / "src"

if _shared_dir.exists():
    sys.path.insert(0, str(_shared_dir))


def main():
    """启动嵌入式服务器"""
    import uvicorn
    from voidview_shared import setup_logging, get_logger

    parser = argparse.ArgumentParser(description="VoidView 嵌入式服务器")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="服务器地址")
    args = parser.parse_args()

    # 配置日志（打包模式使用用户目录）
    dev_mode = not getattr(sys, 'frozen', False)
    setup_logging(
        app_name="voidview-server",
        level="INFO",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        dev_mode=dev_mode,
    )

    logger = get_logger()
    logger.info(f"嵌入式服务器启动，路径: {_server_dir}")

    # 启动服务器
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
