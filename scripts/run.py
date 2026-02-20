#!/usr/bin/env python
"""VoidView 运行脚本 - 启动客户端或服务端"""

import subprocess
import sys
import webbrowser
from pathlib import Path


def run_server():
    """启动服务端"""
    project_root = Path(__file__).parent.parent
    server_main = project_root / "server" / "app" / "main.py"

    if not server_main.exists():
        print(f"Error: {server_main} not found!")
        sys.exit(1)

    print("Starting VoidView server...")
    subprocess.run([sys.executable, "-m", "uvicorn", "app.main:app", "--reload"], cwd=project_root / "server")


def run_client_dev():
    """启动客户端 (开发模式)"""
    project_root = Path(__file__).parent.parent
    client_main = project_root / "client" / "src" / "main.py"

    if not client_main.exists():
        print(f"Error: {client_main} not found!")
        sys.exit(1)

    print("Starting VoidView client (dev mode)...")
    subprocess.run([sys.executable, str(client_main)], cwd=project_root / "client" / "src")


def run_client_exe():
    """启动客户端 (打包模式)"""
    project_root = Path(__file__).parent.parent
    exe_path = project_root / "client" / "dist" / "VoidView.exe"

    if not exe_path.exists():
        print(f"Error: {exe_path} not found!")
        print("Please run 'python scripts/build.py' first.")
        sys.exit(1)

    print("Starting VoidView client (packaged)...")
    subprocess.run([str(exe_path)], cwd=project_root)


def open_docs():
    """打开 API 文档"""
    url = "http://localhost:8000/docs"
    print(f"Opening API docs at {url}...")
    webbrowser.open(url)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="VoidView Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run.py server    Start the backend server
  python scripts/run.py client    Start the client (dev mode)
  python scripts/run.py exe       Start the client (packaged)
  python scripts/run.py docs      Open API documentation
        """
    )

    parser.add_argument(
        "command",
        choices=["server", "client", "exe", "docs"],
        help="Command to run"
    )

    args = parser.parse_args()

    commands = {
        "server": run_server,
        "client": run_client_dev,
        "exe": run_client_exe,
        "docs": open_docs,
    }

    commands[args.command]()


if __name__ == "__main__":
    main()
