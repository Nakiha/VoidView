"""本地服务器管理器 - 用于在客户端中启动本地服务器"""

import re
import subprocess
import sys
import time
import socket
import threading
from pathlib import Path
from typing import Optional, TextIO

from voidview_shared import get_logger

logger = get_logger()

# ANSI 颜色转义码正则表达式
ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-9;]*m')


def find_free_port(start_port: int = 8000, max_attempts: int = 100) -> int:
    """查找可用端口

    Args:
        start_port: 起始端口
        max_attempts: 最大尝试次数

    Returns:
        可用的端口号
    """
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"无法找到可用端口 (尝试范围: {start_port}-{start_port + max_attempts})")


def _log_stream(stream, log_file: Optional[TextIO] = None):
    """后台线程中记录子进程输出

    Args:
        stream: 子进程的 stdout 或 stderr 流
        log_file: 可选的日志文件句柄，如果提供则写入文件
    """
    try:
        for line in iter(stream.readline, b''):
            if line:
                decoded_line = line.decode('utf-8', errors='replace')

                # 去除 ANSI 颜色转义码
                clean_line = ANSI_ESCAPE_RE.sub('', decoded_line)

                # 去除末尾的空白字符（包括 \r\n 或 \n），然后统一添加换行
                clean_line = clean_line.rstrip() + '\n'

                # 写入独立的服务器日志文件
                if log_file and not log_file.closed:
                    try:
                        log_file.write(clean_line)
                        log_file.flush()
                    except:
                        pass
    except:
        pass
    finally:
        stream.close()


class LocalServerManager:
    """本地服务器管理器"""

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._port: Optional[int] = None
        self._data_dir: Optional[Path] = None
        self._log_file: Optional[TextIO] = None

    def _get_log_file_path(self) -> Path:
        """获取服务器日志文件路径"""
        # 使用客户端日志目录
        if getattr(sys, 'frozen', False):
            # 打包模式：使用用户目录
            if sys.platform == "win32":
                log_dir = Path.home() / "AppData" / "Local" / "VoidView" / "logs"
            elif sys.platform == "darwin":
                log_dir = Path.home() / "Library" / "Logs" / "VoidView"
            else:
                log_dir = Path.home() / ".local" / "state" / "VoidView" / "logs"
        else:
            # 开发模式：使用项目目录
            client_dir = Path(__file__).parent.parent.parent
            log_dir = client_dir / "logs"

        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / "local-server.log"

    @property
    def is_running(self) -> bool:
        """检查服务器是否在运行"""
        if self._process is None:
            return False
        return self._process.poll() is None

    @property
    def port(self) -> Optional[int]:
        """获取服务器端口"""
        return self._port

    @property
    def url(self) -> Optional[str]:
        """获取服务器 URL"""
        if self._port:
            return f"http://127.0.0.1:{self._port}/api/v1"
        return None

    def start(self, port: Optional[int] = None, data_dir: Optional[Path] = None) -> bool:
        """启动本地服务器

        Args:
            port: 服务器端口，None 则自动选择
            data_dir: 数据目录，None 则使用默认目录

        Returns:
            是否启动成功
        """
        if self.is_running:
            logger.warning("本地服务器已在运行中")
            return True

        # 确定端口
        if port is None:
            self._port = find_free_port()
        else:
            self._port = port

        # 确定数据目录
        if data_dir is None:
            if sys.platform == "win32":
                self._data_dir = Path.home() / "AppData" / "Local" / "VoidView" / "data"
            elif sys.platform == "darwin":
                self._data_dir = Path.home() / "Library" / "Application Support" / "VoidView" / "data"
            else:
                self._data_dir = Path.home() / ".local" / "share" / "VoidView" / "data"
        else:
            self._data_dir = data_dir

        # 确保数据目录存在
        self._data_dir.mkdir(parents=True, exist_ok=True)

        # 设置环境变量
        env = {
            **subprocess.os.environ,
            "DATABASE_URL": f"sqlite+aiosqlite:///{self._data_dir / 'voidview.db'}",
            "STORAGE_PATH": str(self._data_dir / "storage"),
            "VOIDVIEW_DATA_DIR": str(self._data_dir),
        }

        # 查找服务器模块路径
        if getattr(sys, 'frozen', False):
            # 打包模式
            base_path = Path(sys._MEIPASS)
            embedded_server = base_path / "embedded_server"
            server_dir = None
        else:
            # 开发模式
            client_dir = Path(__file__).parent.parent.parent
            project_root = client_dir.parent
            embedded_server = client_dir / "embedded_server"
            server_dir = project_root / "server"

        cwd = None
        cmd = None

        if embedded_server.exists():
            # 使用嵌入的服务器
            server_main = embedded_server / "main.py"
            if server_main.exists():
                logger.info(f"启动嵌入的服务器: {server_main}")
                cmd = [sys.executable, str(server_main), "--port", str(self._port)]
                cwd = str(embedded_server)
            else:
                logger.error(f"嵌入的服务器主文件不存在: {server_main}")
                return False
        elif server_dir and server_dir.exists():
            # 开发模式: 使用项目中的服务器
            logger.info(f"使用开发模式启动服务器，目录: {server_dir}")
            cmd = [
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--host", "127.0.0.1",
                "--port", str(self._port),
            ]
            cwd = str(server_dir)
            # 添加 shared 模块路径
            project_root = server_dir.parent
            shared_src = str(project_root / "shared" / "src")
            env["PYTHONPATH"] = shared_src + ";" + env.get("PYTHONPATH", "")
        else:
            logger.error("找不到服务器代码")
            return False

        logger.info(f"启动命令: {' '.join(cmd)}")
        logger.debug(f"工作目录: {cwd}")

        # 打开服务器日志文件
        log_path = self._get_log_file_path()
        try:
            self._log_file = open(log_path, 'a', encoding='utf-8')
            logger.info(f"服务器日志将写入: {log_path}")
        except Exception as e:
            logger.warning(f"无法打开服务器日志文件: {e}，服务器输出将丢失")
            self._log_file = None

        self._process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
        )

        # 启动后台线程记录子进程输出到独立日志文件
        threading.Thread(
            target=_log_stream,
            args=(self._process.stdout, self._log_file),
            daemon=True
        ).start()
        threading.Thread(
            target=_log_stream,
            args=(self._process.stderr, self._log_file),
            daemon=True
        ).start()

        # 等待服务器启动
        logger.info(f"本地服务器启动中，端口: {self._port}")
        time.sleep(2)

        if self.is_running:
            logger.info(f"本地服务器已启动: {self.url}")
            return True
        else:
            logger.error("本地服务器启动失败")
            self.stop()
            return False

    def stop(self):
        """停止本地服务器"""
        if self._process:
            logger.info("正在停止本地服务器...")
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("本地服务器未响应，强制终止")
                self._process.kill()
                try:
                    self._process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
            self._process = None
            logger.info("本地服务器已停止")

        # 先将日志文件引用置空，防止后台线程继续写入
        log_file = self._log_file
        self._log_file = None

        # 等待后台线程处理完毕（它们是 daemon 线程，会自动退出）
        time.sleep(0.1)

        # 关闭日志文件
        if log_file:
            try:
                log_file.close()
            except:
                pass

    def wait_for_ready(self, timeout: float = 10.0) -> bool:
        """等待服务器就绪

        Args:
            timeout: 超时时间（秒）

        Returns:
            服务器是否就绪
        """
        import httpx

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = httpx.get(f"http://127.0.0.1:{self._port}/health", timeout=1.0)
                if response.status_code == 200:
                    return True
            except:
                pass
            time.sleep(0.5)

        return False


# 全局本地服务器管理器
local_server = LocalServerManager()
