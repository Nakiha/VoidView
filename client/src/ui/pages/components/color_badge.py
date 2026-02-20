"""点缀色徽章组件"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QFrame
from qfluentwidgets import BodyLabel, CaptionLabel, isDarkTheme


# 预设颜色列表
PRESET_COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
    "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"
]


def get_color_by_index(index: int) -> str:
    """根据索引获取颜色"""
    return PRESET_COLORS[index % len(PRESET_COLORS)]


class ColorBadge(QWidget):
    """带颜色的状态徽章"""

    clicked = Signal()

    def __init__(self, color: str, text: str = "", parent=None, clickable: bool = False):
        super().__init__(parent)
        self._color = color
        self._text = text
        self._clickable = clickable
        self.setupUI()

    def setupUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # 颜色圆点
        dot = QFrame(self)
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"""
            QFrame {{
                background-color: {self._color};
                border-radius: 5px;
            }}
        """)
        layout.addWidget(dot)

        # 文本
        if self._text:
            label = CaptionLabel(self)
            label.setText(self._text)
            layout.addWidget(label)

        layout.addStretch()

        # 可点击样式
        if self._clickable:
            self.setCursor(Qt.PointingHandCursor)
            self.setStyleSheet("""
                ColorBadge:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                    border-radius: 4px;
                }
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._clickable:
            self.clicked.emit()
        super().mousePressEvent(event)


class ColorBar(QWidget):
    """垂直颜色条（用于卡片侧边）"""

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedWidth(4)
        self.setStyleSheet(f"""
            ColorBar {{
                background-color: {self._color};
                border-radius: 2px;
            }}
        """)


class ColorDot(QWidget):
    """颜色圆点（更小的圆点）"""

    def __init__(self, color: str, size: int = 8, parent=None):
        super().__init__(parent)
        self._color = color
        self._size = size
        self.setFixedSize(size, size)
        self.setStyleSheet(f"""
            ColorDot {{
                background-color: {self._color};
                border-radius: {size // 2}px;
            }}
        """)
