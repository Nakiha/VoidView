"""服务端配置"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings

# 服务端目录
SERVER_DIR = Path(__file__).parent.parent.resolve()
PROJECT_ROOT = SERVER_DIR.parent


def _get_default_storage_dir() -> Path:
    """获取默认存储目录"""
    # 优先使用环境变量
    if "STORAGE_PATH" in os.environ:
        return Path(os.environ["STORAGE_PATH"])

    # 默认使用项目 server/storage 目录
    return PROJECT_ROOT / "server" / "storage"


class Settings(BaseSettings):
    """应用配置"""

    # 应用信息
    APP_NAME: str = "VoidView API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # JWT
    JWT_SECRET: str = "voidview-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 文件存储 - 支持环境变量覆盖
    STORAGE_PATH: str = ""
    SCREENSHOTS_PATH: str = ""
    ATTACHMENTS_PATH: str = ""

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 设置默认存储路径
        if not self.STORAGE_PATH:
            self.STORAGE_PATH = str(_get_default_storage_dir())

        # 确保存储路径是 Path 对象
        self._storage_path = Path(self.STORAGE_PATH) if self.STORAGE_PATH else _get_default_storage_dir()

        # 设置子目录
        if not self.SCREENSHOTS_PATH:
            self._screenshots_path = self._storage_path / "screenshots"
        else:
            self._screenshots_path = Path(self.SCREENSHOTS_PATH)

        if not self.ATTACHMENTS_PATH:
            self._attachments_path = self._storage_path / "attachments"
        else:
            self._attachments_path = Path(self.ATTACHMENTS_PATH)

    @property
    def storage_path(self) -> Path:
        return self._storage_path

    @property
    def screenshots_path(self) -> Path:
        return self._screenshots_path

    @property
    def attachments_path(self) -> Path:
        return self._attachments_path


settings = Settings()

# 确保目录存在
settings.storage_path.mkdir(parents=True, exist_ok=True)
settings.screenshots_path.mkdir(parents=True, exist_ok=True)
settings.attachments_path.mkdir(parents=True, exist_ok=True)
