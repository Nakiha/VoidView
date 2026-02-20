"""客户端配置"""

import json
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

# 客户端目录
CLIENT_DIR = Path(__file__).parent.parent.parent.resolve()
PROJECT_ROOT = CLIENT_DIR.parent


class Settings(BaseSettings):
    """客户端配置（从环境变量/ .env 文件读取）"""

    # 本地数据目录 - 使用绝对路径
    DATA_DIR: Path = PROJECT_ROOT / "client" / "data"
    CACHE_DIR: Path = PROJECT_ROOT / "client" / "data" / "cache"
    SCREENSHOTS_DIR: Path = PROJECT_ROOT / "client" / "data" / "screenshots"
    EXPORTS_DIR: Path = PROJECT_ROOT / "client" / "data" / "exports"

    # UI 配置
    WINDOW_WIDTH: int = 1280
    WINDOW_HEIGHT: int = 800
    WINDOW_MIN_WIDTH: int = 1024
    WINDOW_MIN_HEIGHT: int = 600

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class UserConfig:
    """用户配置（存储在本地 JSON 文件中，可动态修改）"""

    DEFAULT_SERVER_URL = "http://localhost:8000/api/v1"

    def __init__(self):
        self._config_dir = PROJECT_ROOT / "client" / "data"
        self._config_file = self._config_dir / "user_config.json"
        self._server_url: Optional[str] = None
        self._load()

    def _load(self):
        """从文件加载配置"""
        if self._config_file.exists():
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._server_url = data.get("server_url")
            except Exception:
                self._server_url = None

    def _save(self):
        """保存配置到文件"""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        data = {"server_url": self._server_url}
        with open(self._config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @property
    def server_url(self) -> str:
        """获取服务器地址"""
        return self._server_url or self.DEFAULT_SERVER_URL

    def set_server_url(self, url: str):
        """设置服务器地址"""
        # 移除末尾斜杠
        url = url.rstrip("/")
        self._server_url = url
        self._save()


settings = Settings()
user_config = UserConfig()

# 确保目录存在
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
settings.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
settings.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
