#!/usr/bin/env python
"""VoidView 客户端打包脚本"""

import subprocess
import sys
import shutil
from pathlib import Path


def ensure_pyinstaller() -> bool:
    """确保 PyInstaller 已安装"""
    try:
        import PyInstaller
        return True
    except ImportError:
        print("PyInstaller not found, installing...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            capture_output=True
        )
        return result.returncode == 0


def build_client(clean: bool = True) -> bool:
    """打包客户端"""
    project_root = Path(__file__).parent.parent
    client_dir = project_root / "client"
    spec_file = client_dir / "VoidView.spec"

    if not spec_file.exists():
        print(f"Error: {spec_file} not found!")
        return False

    # 切换到 client 目录
    print(f"Building VoidView client...")
    print(f"  Working directory: {client_dir}")

    cmd = [sys.executable, "-m", "PyInstaller", "VoidView.spec"]
    if clean:
        cmd.append("--clean")

    result = subprocess.run(cmd, cwd=client_dir)

    if result.returncode == 0:
        exe_path = client_dir / "dist" / "VoidView.exe"
        print("\n" + "=" * 50)
        print("Build completed successfully!")
        print(f"Executable: {exe_path}")
        print("=" * 50)
        return True
    else:
        print("\nBuild failed!")
        return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Build VoidView client")
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Don't clean build cache"
    )
    args = parser.parse_args()

    if not ensure_pyinstaller():
        print("Failed to install PyInstaller")
        sys.exit(1)

    success = build_client(clean=not args.no_clean)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
