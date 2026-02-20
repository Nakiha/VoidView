"""服务器配置对话框"""

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    SubtitleLabel, BodyLabel, LineEdit, PrimaryPushButton, PushButton,
    InfoBar, InfoBarPosition, isDarkTheme, PushButton
)

from app.config import user_config
from api import api_client


class ServerConfigDialog(QWidget):
    """服务器配置对话框 - 当无法连接服务器时显示"""

    configSaved = Signal(str)       # 配置保存成功，传递新的服务器地址
    localModeRequested = Signal()   # 用户请求使用本地模式
    exitRequested = Signal()        # 用户请求退出

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()

    def setupUI(self):
        """设置界面"""
        self.setFixedSize(500, 350)
        self.setWindowTitle("服务器配置")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        # 标题
        titleLabel = SubtitleLabel(self)
        titleLabel.setText("无法连接到服务器")
        titleLabel.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(titleLabel)

        # 说明文字
        hintLabel = BodyLabel(self)
        hintLabel.setText("请检查服务器是否已启动，或修改服务器地址后重试。\n您也可以选择启动本地服务器模式。")
        hintLabel.setWordWrap(True)
        layout.addWidget(hintLabel)

        layout.addSpacing(10)

        # 服务器地址输入
        serverLabel = BodyLabel(self)
        serverLabel.setText("服务器地址:")
        layout.addWidget(serverLabel)

        self.serverEdit = LineEdit(self)
        self.serverEdit.setPlaceholderText("例如: http://localhost:8000/api/v1")
        self.serverEdit.setText(user_config.server_url)
        self.serverEdit.setFixedHeight(36)
        layout.addWidget(self.serverEdit)

        layout.addStretch()

        # 本地模式按钮
        self.localModeBtn = PushButton(self)
        self.localModeBtn.setText("启动本地服务器")
        self.localModeBtn.setFixedHeight(36)
        self.localModeBtn.clicked.connect(self.onLocalMode)
        layout.addWidget(self.localModeBtn)

        layout.addSpacing(10)

        # 底部按钮
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()

        self.exitBtn = PushButton(self)
        self.exitBtn.setText("退出")
        self.exitBtn.setFixedWidth(80)
        self.exitBtn.clicked.connect(self.onExit)
        buttonLayout.addWidget(self.exitBtn)

        self.retryBtn = PrimaryPushButton(self)
        self.retryBtn.setText("保存并重试")
        self.retryBtn.setFixedWidth(120)
        self.retryBtn.clicked.connect(self.onSaveAndRetry)
        buttonLayout.addWidget(self.retryBtn)

        layout.addLayout(buttonLayout)

        # 应用样式
        self.applyStyleSheet()

    def applyStyleSheet(self):
        """应用样式表"""
        isDark = isDarkTheme()

        if isDark:
            self.setStyleSheet("""
                QWidget {
                    background-color: #1a1a1a;
                }
                SubtitleLabel {
                    color: #ffffff;
                }
                BodyLabel {
                    color: #cccccc;
                }
                LineEdit {
                    background-color: #2d2d2d;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                    padding: 8px 12px;
                    color: #ffffff;
                }
                LineEdit:focus {
                    border: 2px solid #0078d4;
                }
                PushButton {
                    background-color: #2d2d2d;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                    padding: 8px 16px;
                    color: #ffffff;
                }
                PushButton:hover {
                    background-color: #3d3d3d;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: #ffffff;
                }
                SubtitleLabel {
                    color: #1a1a1a;
                }
                BodyLabel {
                    color: #666666;
                }
                LineEdit {
                    background-color: #ffffff;
                    border: 1px solid #d1d1d1;
                    border-radius: 4px;
                    padding: 8px 12px;
                    color: #1a1a1a;
                }
                LineEdit:focus {
                    border: 2px solid #0078d4;
                }
                PushButton {
                    background-color: #f5f5f5;
                    border: 1px solid #d1d1d1;
                    border-radius: 4px;
                    padding: 8px 16px;
                    color: #1a1a1a;
                }
                PushButton:hover {
                    background-color: #e5e5e5;
                }
            """)

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
