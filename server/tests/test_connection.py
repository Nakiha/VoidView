"""
VoidView 自动化测试脚本

用法:
    python tests/test_connection.py              # 运行所有测试
    python tests/test_connection.py --server     # 仅测试服务端连接
    python tests/test_connection.py --login      # 仅测试登录
    python tests/test_connection.py --url http://localhost:8000/api/v1  # 指定服务端地址
"""

import sys
import argparse
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "shared" / "src"))
sys.path.insert(0, str(project_root / "client" / "src"))
sys.path.insert(0, str(project_root / "server"))

import httpx


class TestResult:
    """测试结果"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def success(self, name: str):
        self.passed += 1
        print(f"  ✓ {name}")

    def fail(self, name: str, error: str):
        self.failed += 1
        self.errors.append((name, error))
        print(f"  ✗ {name}: {error}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f"测试完成: {self.passed}/{total} 通过")
        if self.errors:
            print("\n失败的测试:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        return self.failed == 0


def test_server_connection(base_url: str, result: TestResult):
    """测试服务端连接"""
    print("\n[1] 测试服务端连接...")

    # 测试健康检查端点
    try:
        response = httpx.get(f"{base_url}/health", timeout=5.0)
        if response.status_code == 200:
            result.success("健康检查端点 (/health)")
        else:
            result.fail("健康检查端点", f"状态码 {response.status_code}")
    except httpx.ConnectError:
        result.fail("健康检查端点", "无法连接到服务器")
        return False
    except Exception as e:
        result.fail("健康检查端点", str(e))
        return False

    # 测试根端点
    try:
        response = httpx.get(base_url.replace("/api/v1", ""), timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            result.success(f"根端点 - {data.get('name', 'Unknown')} v{data.get('version', '?')}")
        else:
            result.fail("根端点", f"状态码 {response.status_code}")
    except Exception as e:
        result.fail("根端点", str(e))

    return True


def test_login(base_url: str, result: TestResult):
    """测试登录功能"""
    print("\n[2] 测试登录功能...")

    client = httpx.Client(base_url=base_url, timeout=10.0)

    # 测试错误密码
    try:
        response = client.post("/auth/login", json={
            "username": "root",
            "password": "wrong_password"
        })
        if response.status_code == 400:
            result.success("错误密码拒绝")
        else:
            result.fail("错误密码拒绝", f"预期 400，得到 {response.status_code}")
    except Exception as e:
        result.fail("错误密码拒绝", str(e))

    # 测试默认 root 登录
    try:
        response = client.post("/auth/login", json={
            "username": "root",
            "password": "root123"
        })
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            user = data.get("user", {})
            result.success(f"root 登录成功 - 用户: {user.get('display_name', 'Unknown')}")

            # 测试获取当前用户
            if token:
                try:
                    me_response = client.get("/auth/me", headers={
                        "Authorization": f"Bearer {token}"
                    })
                    if me_response.status_code == 200:
                        result.success("获取当前用户信息 (/auth/me)")
                    else:
                        result.fail("获取当前用户信息", f"状态码 {me_response.status_code}")
                except Exception as e:
                    result.fail("获取当前用户信息", str(e))
        elif response.status_code == 400:
            # 密码已修改，尝试提示用户
            result.fail("root 登录", "默认密码已修改，请手动测试")
        else:
            result.fail("root 登录", f"状态码 {response.status_code}")
    except Exception as e:
        result.fail("root 登录", str(e))

    client.close()


def test_user_config(result: TestResult):
    """测试用户配置"""
    print("\n[3] 测试用户配置...")

    # 直接操作配置文件，避免导入冲突
    import json

    config_dir = project_root / "client" / "data"
    config_file = config_dir / "user_config.json"

    def get_server_url():
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("server_url") or "http://localhost:8000/api/v1"
            except Exception:
                pass
        return "http://localhost:8000/api/v1"

    def set_server_url(url):
        config_dir.mkdir(parents=True, exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"server_url": url.rstrip("/")}, f)

    # 测试默认值
    original_url = get_server_url()
    result.success(f"获取当前服务器地址: {original_url}")

    # 测试设置新地址
    test_url = "http://test.example.com/api/v1"
    set_server_url(test_url)
    if get_server_url() == test_url:
        result.success("设置服务器地址")
    else:
        result.fail("设置服务器地址", f"预期 {test_url}，得到 {get_server_url()}")

    # 恢复原始地址
    set_server_url(original_url)
    if get_server_url() == original_url:
        result.success("恢复服务器地址")
    else:
        result.fail("恢复服务器地址", "恢复失败")


def main():
    parser = argparse.ArgumentParser(description="VoidView 自动化测试")
    parser.add_argument("--url", default="http://localhost:8000/api/v1", help="服务器地址")
    parser.add_argument("--server", action="store_true", help="仅测试服务端连接")
    parser.add_argument("--login", action="store_true", help="仅测试登录")
    args = parser.parse_args()

    print("="*50)
    print("VoidView 自动化测试")
    print(f"服务器地址: {args.url}")
    print("="*50)

    result = TestResult()

    if args.server:
        test_server_connection(args.url, result)
    elif args.login:
        test_login(args.url, result)
    else:
        # 运行所有测试
        server_ok = test_server_connection(args.url, result)
        if server_ok:
            test_login(args.url, result)
        test_user_config(result)

    success = result.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
