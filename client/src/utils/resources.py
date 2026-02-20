"""资源加载工具"""

from pathlib import Path
from PySide6.QtGui import QIcon, QPixmap, Qt
from PySide6.QtCore import QSize


# 资源目录路径
RESOURCES_DIR = Path(__file__).parent.parent / "resources"
ICONS_DIR = RESOURCES_DIR / "icons"


def get_icon_path(name: str) -> Path:
    """获取图标路径

    Args:
        name: 图标文件名 (不含扩展名或含扩展名)

    Returns:
        图标文件的完整路径
    """
    icon_path = ICONS_DIR / name
    if not icon_path.exists():
        # 尝试添加 .svg 扩展名
        svg_path = ICONS_DIR / f"{name}.svg"
        if svg_path.exists():
            return svg_path
        # 尝试添加 .png 扩展名
        png_path = ICONS_DIR / f"{name}.png"
        if png_path.exists():
            return png_path
    return icon_path


def load_icon(name: str, size: QSize | None = None) -> QIcon:
    """加载图标

    Args:
        name: 图标文件名
        size: 可选的图标大小

    Returns:
        QIcon 对象
    """
    icon_path = get_icon_path(name)
    if icon_path.exists():
        icon = QIcon(str(icon_path))
        return icon
    return QIcon()


def load_pixmap(name: str, size: QSize | None = None) -> QPixmap:
    """加载位图

    Args:
        name: 图标文件名
        size: 可选的缩放大小

    Returns:
        QPixmap 对象
    """
    pixmap_path = get_icon_path(name)
    if pixmap_path.exists():
        pixmap = QPixmap(str(pixmap_path))
        if size and not size.isEmpty():
            return pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        return pixmap
    return QPixmap()


def get_logo_path() -> Path:
    """获取应用 logo 路径"""
    return get_icon_path("logo")
