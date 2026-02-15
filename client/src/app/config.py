"""客户端配置"""

from pathlib import Path
from pydantic_settings import BaseSettings

# 客户端目录
CLIENT_DIR = Path(__file__).parent.parent.parent.resolve()
PROJECT_ROOT = CLIENT_DIR.parent


class Settings(BaseSettings):
    """客户端配置"""

    # API 服务器地址
    API_BASE_URL: str = "http://localhost:8000/api/v1"

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


settings = Settings()

# 确保目录存在
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
settings.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
settings.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
