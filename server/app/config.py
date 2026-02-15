"""服务端配置"""

from pathlib import Path
from pydantic_settings import BaseSettings

# 服务端目录
SERVER_DIR = Path(__file__).parent.parent.resolve()
PROJECT_ROOT = SERVER_DIR.parent


class Settings(BaseSettings):
    """应用配置"""

    # 应用信息
    APP_NAME: str = "VoidView API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # 数据库 - 使用绝对路径
    DATABASE_URL: str = f"sqlite+aiosqlite:///{PROJECT_ROOT / 'data' / 'voidview.db'}"

    # JWT
    JWT_SECRET: str = "voidview-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 文件存储 - 使用绝对路径
    STORAGE_PATH: Path = PROJECT_ROOT / "server" / "storage"
    SCREENSHOTS_PATH: Path = PROJECT_ROOT / "server" / "storage" / "screenshots"
    ATTACHMENTS_PATH: Path = PROJECT_ROOT / "server" / "storage" / "attachments"

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# 确保目录存在
(PROJECT_ROOT / "data").mkdir(parents=True, exist_ok=True)
settings.STORAGE_PATH.mkdir(parents=True, exist_ok=True)
settings.SCREENSHOTS_PATH.mkdir(parents=True, exist_ok=True)
settings.ATTACHMENTS_PATH.mkdir(parents=True, exist_ok=True)
