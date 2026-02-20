"""服务器配置对话框"""

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    FluentWindow, SubtitleLabel, BodyLabel, LineEdit, PrimaryPushButton,
    PushButton, InfoBar, InfoBarPosition
)

from app.config import user_config
from api import api_client


class ServerConfigDialog(FluentWindow):
    """服务器配置对话框 - 当无法连接服务器时显示"""

    configSaved = Signal(str)       # 配置保存成功，传递新的服务器地址
    localModeRequested = Signal()   # 用户请求使用本地模式
    exitRequested = Signal()        # 用户请求退出

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("服务器配置")
        self.setFixedSize(500, 320)

        # 启用 Mica 效果
        self.micaEnabled = True

        # 隐藏导航栏
        self.navigationInterface.hide()

        # 隐藏返回按钮
        self.navigationInterface.panel.setReturnButtonVisible(False)

        # 禁用最大化按钮（对话框固定大小）
        self.titleBar.maxBtn.hide()

        # 隐藏 stackedWidget（不使用导航系统）
        self.stackedWidget.hide()

        # 调整内容区域边距：保留标题栏高度(48)，移除左侧导航栏宽度
        self.widgetLayout.setContentsMargins(0, 48, 0, 0)

        # 创建内容页面并直接添加到 widgetLayout
        self.contentPage = self._createContentPage()
        self.widgetLayout.addWidget(self.contentPage)

        # 调整标题栏位置（移除导航栏预留空间）
        self._adjustTitleBar()

        # 居中显示
        self._centerWindow()

    def _adjustTitleBar(self):
        """调整标题栏位置，移除导航栏预留空间"""
        self.titleBar.move(0, 0)
        self.titleBar.resize(self.width(), self.titleBar.height())

    def resizeEvent(self, event):
        """重写 resizeEvent，调整标题栏位置"""
        super().resizeEvent(event)
        self._adjustTitleBar()

    def _centerWindow(self):
        """将窗口居中显示"""
        from PySide6.QtGui import QScreen
        screen = QScreen.availableGeometry(self.screen())
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def _createContentPage(self) -> QWidget:
        """创建内容页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(12)

        # 标题
        titleLabel = SubtitleLabel(page)
        titleLabel.setText("无法连接到服务器")
        titleLabel.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(titleLabel)

        layout.addSpacing(4)

        # 说明文字
        hintLabel = BodyLabel(page)
        hintLabel.setText("请检查服务器是否已启动，或修改服务器地址后重试。\n您也可以选择启动本地服务器模式。")
        hintLabel.setWordWrap(True)
        layout.addWidget(hintLabel)

        layout.addSpacing(16)

        # 服务器地址输入
        serverLabel = BodyLabel(page)
        serverLabel.setText("服务器地址")
        layout.addWidget(serverLabel)

        self.serverEdit = LineEdit(page)
        self.serverEdit.setPlaceholderText("例如: http://localhost:8000/api/v1")
        self.serverEdit.setText(user_config.server_url)
        self.serverEdit.setFixedHeight(36)
        layout.addWidget(self.serverEdit)

        layout.addStretch()

        # 本地模式按钮
        self.localModeBtn = PushButton(page)
        self.localModeBtn.setText("启动本地服务器")
        self.localModeBtn.setFixedHeight(36)
        self.localModeBtn.clicked.connect(self.onLocalMode)
        layout.addWidget(self.localModeBtn)

        layout.addSpacing(16)

        # 底部按钮
        buttonLayout = QHBoxLayout()
        buttonLayout.setSpacing(12)
        buttonLayout.addStretch()

        self.exitBtn = PushButton(page)
        self.exitBtn.setText("退出")
        self.exitBtn.setFixedWidth(90)
        self.exitBtn.clicked.connect(self.onExit)
        buttonLayout.addWidget(self.exitBtn)

        self.retryBtn = PrimaryPushButton(page)
        self.retryBtn.setText("保存并重试")
        self.retryBtn.setFixedWidth(110)
        self.retryBtn.clicked.connect(self.onSaveAndRetry)
        buttonLayout.addWidget(self.retryBtn)

        layout.addLayout(buttonLayout)

        return page

    def onSaveAndRetry(self):
        """保存配置并重试"""
        server_url = self.serverEdit.text().strip()

        if not server_url:
            InfoBar.warning(
                title="提示",
                content="请输入服务器地址",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        # 验证 URL 格式
        if not server_url.startswith(("http://", "https://")):
            InfoBar.warning(
                title="提示",
                content="服务器地址必须以 http:// 或 https:// 开头",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        # 保存配置
        user_config.set_server_url(server_url)
        api_client.update_base_url(server_url)

        self.configSaved.emit(server_url)

    def onLocalMode(self):
        """使用本地模式"""
        self.localModeBtn.setEnabled(False)
        self.localModeBtn.setText("启动中...")
        self.localModeRequested.emit()

    def onExit(self):
        """退出应用"""
        self.exitRequested.emit()
