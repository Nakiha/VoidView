"""悬浮工具栏"""

from PySide6.QtCore import Qt, Signal, QTimer, QEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout
from qfluentwidgets import PrimaryPushButton, PushButton, FluentIcon


class FloatingToolbar(QWidget):
    """右下角悬浮工具栏"""

    addEntityClicked = Signal()
    addExperimentClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._has_selection = False
        self.setupUI()
        self._adjustPosition()

        # 安装事件过滤器以监听父窗口大小变化
        if parent:
            parent.installEventFilter(self)

    def setupUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # 按钮1: 添加客户/APP/模板
        self.addEntityBtn = PrimaryPushButton(self)
        self.addEntityBtn.setText("添加客户/APP/模板")
        self.addEntityBtn.setIcon(FluentIcon.ADD)
        self.addEntityBtn.clicked.connect(self.addEntityClicked)
        layout.addWidget(self.addEntityBtn)

        # 按钮2: 选中行添加实验
        self.addExperimentBtn = PushButton(self)
        self.addExperimentBtn.setText("选中行添加实验")
        self.addExperimentBtn.setIcon(FluentIcon.ADD_TO)
        self.addExperimentBtn.clicked.connect(self.addExperimentClicked)
        self.addExperimentBtn.setVisible(False)  # 初始隐藏
        layout.addWidget(self.addExperimentBtn)

        self.setStyleSheet("""
            FloatingToolbar {
                background-color: rgba(32, 32, 32, 0.95);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)

        self.adjustSize()

    def setHasSelection(self, has_selection: bool):
        """设置是否有选中项"""
        self._has_selection = has_selection
        self.addExperimentBtn.setVisible(has_selection)
        self.adjustSize()
        self._adjustPosition()

    def _adjustPosition(self):
        """调整位置到右下角"""
        parent = self.parentWidget()
        if parent:
            margin = 20
            # 使用 QTimer 延迟调整位置，确保布局已完成
            QTimer.singleShot(0, lambda: self._doAdjustPosition(parent, margin))

    def _doAdjustPosition(self, parent, margin):
        """实际执行位置调整"""
        self.move(
            parent.width() - self.width() - margin,
            parent.height() - self.height() - margin
        )

    def eventFilter(self, obj, event):
        """事件过滤器 - 监听父窗口大小变化"""
        if event.type() == QEvent.Resize:
            self._adjustPosition()
        return super().eventFilter(obj, event)

    def showEvent(self, event):
        """显示时调整位置"""
        super().showEvent(event)
        self._adjustPosition()
