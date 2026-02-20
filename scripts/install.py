#!/usr/bin/env python
"""VoidView 依赖安装脚本"""

import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str], cwd: Path | None = None) -> bool:
    """运行命令并返回是否成功"""
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode == 0


def install_package(path: Path, name: str) -> bool:
    """安装单个包"""
    print(f"\n[{name}] Installing {path.name}...")
    return run_cmd([sys.executable, "-m", "pip", "install", "-e", "."], cwd=path)


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent

    packages = [
        ("shared", "1/3"),
        ("server", "2/3"),
        ("client", "3/3"),
    ]

    print("=" * 50)
    print("VoidView Dependency Installer")
    print("=" * 50)

    failed = []
    for pkg_name, step in packages:
        pkg_path = project_root / pkg_name
        if not pkg_path.exists():
            print(f"  [!] {pkg_name} directory not found, skipping...")
            continue

        print(f"\n[{step}] Installing {pkg_name}...")
        if not install_package(pkg_path, step):
            failed.append(pkg_name)

    print("\n" + "=" * 50)
    if failed:
        print(f"Failed to install: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("All dependencies installed successfully!")
    print("=" * 50)
    print("\nUsage:")
    print("  python scripts/run.py server   # Start server")
    print("  python scripts/run.py client   # Start client (dev mode)")
    print("  python scripts/run.py exe      # Start client (packaged)")
    print()


if __name__ == "__main__":
    main()
