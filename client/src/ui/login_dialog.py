"""登录对话框 - Fluent Design 风格"""

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtGui import QFont
from qfluentwidgets import (
    SubtitleLabel, BodyLabel, LineEdit, PrimaryPushButton, PushButton,
    InfoBar, InfoBarPosition, FluentIcon, MessageBoxBase,
    isDarkTheme, TransparentToolButton, IconWidget
)

from api import auth_api, APIError
from models import UserResponse


class LoginDialog(QWidget):
    """登录对话框 - Fluent Design 风格"""

    loginSuccess = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_user = None
        self._pending_user = None
        self.setupUI()

    def setupUI(self):
        # 主布局
        mainLayout = QHBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        # 左侧装饰面板 (仅宽屏时显示)
        self.leftPanel = QWidget()
        self.leftPanel.setFixedWidth(280)
        self.leftPanel.setObjectName("leftPanel")
        self.setupLeftPanel()
        mainLayout.addWidget(self.leftPanel)

        # 右侧登录表单
        self.rightPanel = QWidget()
        self.rightPanel.setObjectName("rightPanel")
        self.setupRightPanel()
        mainLayout.addWidget(self.rightPanel, 1)

        # 设置窗口
        self.setFixedWidth(700)
        self.setFixedHeight(500)

        # 应用样式
        self.applyStyleSheet()

    def setupLeftPanel(self):
        """设置左侧装饰面板"""
        layout = QVBoxLayout(self.leftPanel)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        layout.addStretch()

        # Logo/图标
        logoLabel = SubtitleLabel(self.leftPanel)
        logoLabel.setText("◆")
        logoLabel.setAlignment(Qt.AlignCenter)
        logoLabel.setStyleSheet("font-size: 64px; color: #0078d4;")
        layout.addWidget(logoLabel)

        # 应用名称
        nameLabel = SubtitleLabel(self.leftPanel)
        nameLabel.setText("VoidView")
        nameLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(nameLabel)

        # 副标题
        subtitleLabel = BodyLabel(self.leftPanel)
        subtitleLabel.setText("视频质量评测系统")
        subtitleLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitleLabel)

        layout.addStretch()

        # 版本信息
        versionLabel = BodyLabel(self.leftPanel)
        versionLabel.setText("v0.1.0")
        versionLabel.setAlignment(Qt.AlignCenter)
        versionLabel.setStyleSheet("color: rgba(255, 255, 255, 0.5);")
        layout.addWidget(versionLabel)

    def setupRightPanel(self):
        """设置右侧登录表单"""
        layout = QVBoxLayout(self.rightPanel)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(20)

        layout.addStretch()

        # 欢迎标题
        welcomeLabel = SubtitleLabel(self.rightPanel)
        welcomeLabel.setText("欢迎回来")
        welcomeLabel.setStyleSheet("font-size: 28px; font-weight: 600;")
        layout.addWidget(welcomeLabel)

        # 提示文字
        hintLabel = BodyLabel(self.rightPanel)
        hintLabel.setText("请登录您的账号以继续")
        layout.addWidget(hintLabel)

        layout.addSpacing(20)

        # 用户名
        usernameTitle = BodyLabel(self.rightPanel)
        usernameTitle.setText("用户名")
        layout.addWidget(usernameTitle)

        self.usernameEdit = LineEdit(self.rightPanel)
        self.usernameEdit.setPlaceholderText("请输入用户名")
        self.usernameEdit.setClearButtonEnabled(True)
        self.usernameEdit.setFixedHeight(40)
        layout.addWidget(self.usernameEdit)

        layout.addSpacing(8)

        # 密码
        passwordTitle = BodyLabel(self.rightPanel)
        passwordTitle.setText("密码")
        layout.addWidget(passwordTitle)

        self.passwordEdit = LineEdit(self.rightPanel)
        self.passwordEdit.setPlaceholderText("请输入密码")
        self.passwordEdit.setEchoMode(LineEdit.Password)
        self.passwordEdit.setClearButtonEnabled(True)
        self.passwordEdit.setFixedHeight(40)
        layout.addWidget(self.passwordEdit)

        layout.addSpacing(16)

        # 登录按钮
        self.loginBtn = PrimaryPushButton(self.rightPanel)
        self.loginBtn.setText("登录")
        self.loginBtn.setFixedHeight(40)
        self.loginBtn.clicked.connect(self.attemptLogin)
        layout.addWidget(self.loginBtn)

        # 回车登录
        self.usernameEdit.returnPressed.connect(self.attemptLogin)
        self.passwordEdit.returnPressed.connect(self.attemptLogin)

        layout.addStretch()

    def applyStyleSheet(self):
        """应用样式表"""
        isDark = isDarkTheme()

        if isDark:
            self.setStyleSheet("""
                #leftPanel {
                    background-color: #202020;
                }
                #rightPanel {
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
                PrimaryPushButton {
                    background-color: #0078d4;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: 600;
                }
                PrimaryPushButton:hover {
                    background-color: #1084d8;
                }
                PrimaryPushButton:pressed {
                    background-color: #006cbd;
                }
            """)
        else:
            self.setStyleSheet("""
                #leftPanel {
                    background-color: #0078d4;
                }
                #rightPanel {
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
                PrimaryPushButton {
                    background-color: #0078d4;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: 600;
                }
                PrimaryPushButton:hover {
                    background-color: #1084d8;
                }
                PrimaryPushButton:pressed {
                    background-color: #006cbd;
                }
            """)

    def attemptLogin(self):
        """尝试登录"""
        username = self.usernameEdit.text().strip()
        password = self.passwordEdit.text()

        if not username or not password:
            InfoBar.warning(
                title="提示",
                content="请输入用户名和密码",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        try:
            token_response = auth_api.login(username, password)
            self.current_user = token_response.user
            self.loginSuccess.emit(self.current_user)

        except APIError as e:
            InfoBar.error(
                title="登录失败",
                content=e.message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            self.passwordEdit.clear()
            self.passwordEdit.setFocus()

    def clearForm(self):
        """清空表单"""
        self.usernameEdit.clear()
        self.passwordEdit.clear()
        self.usernameEdit.setFocus()


class ChangePasswordDialog(MessageBoxBase):
    """修改密码对话框"""

    def __init__(self, must_change: bool = False, parent=None):
        super().__init__(parent)
        self.must_change = must_change

        # 标题
        self.titleLabel = SubtitleLabel(self)
        self.titleLabel.setText("修改密码" if not must_change else "首次登录，请修改密码")
        self.viewLayout.addWidget(self.titleLabel)

        # 当前密码 (如果不是强制修改)
        if not must_change:
            self.oldPasswordLabel = BodyLabel(self)
            self.oldPasswordLabel.setText("当前密码")
            self.viewLayout.addWidget(self.oldPasswordLabel)

            self.oldPasswordEdit = LineEdit(self)
            self.oldPasswordEdit.setEchoMode(LineEdit.Password)
            self.oldPasswordEdit.setPlaceholderText("请输入当前密码")
            self.viewLayout.addWidget(self.oldPasswordEdit)

        # 新密码
        self.newPasswordLabel = BodyLabel(self)
        self.newPasswordLabel.setText("新密码")
        self.viewLayout.addWidget(self.newPasswordLabel)

        self.newPasswordEdit = LineEdit(self)
        self.newPasswordEdit.setEchoMode(LineEdit.Password)
        self.newPasswordEdit.setPlaceholderText("请输入新密码 (至少6位)")
        self.viewLayout.addWidget(self.newPasswordEdit)

        # 确认新密码
        self.confirmPasswordLabel = BodyLabel(self)
        self.confirmPasswordLabel.setText("确认新密码")
        self.viewLayout.addWidget(self.confirmPasswordLabel)

        self.confirmPasswordEdit = LineEdit(self)
        self.confirmPasswordEdit.setEchoMode(LineEdit.Password)
        self.confirmPasswordEdit.setPlaceholderText("请再次输入新密码")
        self.viewLayout.addWidget(self.confirmPasswordEdit)

        # 按钮
        self.yesButton.setText("确认修改")
        self.cancelButton.setText("取消")

        # 如果是强制修改，禁用取消按钮
        if must_change:
            self.cancelButton.setEnabled(False)
            self.widget.setMinimumWidth(400)

    def validate(self) -> bool:
        """验证输入"""
        new_pwd = self.newPasswordEdit.text()
        confirm_pwd = self.confirmPasswordEdit.text()

        if len(new_pwd) < 6:
            InfoBar.warning(
                title="提示",
                content="密码长度不能少于6位",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return False

        if new_pwd != confirm_pwd:
            InfoBar.warning(
                title="提示",
                content="两次输入的密码不一致",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return False

        return True

    def getOldPassword(self) -> str:
        """获取旧密码"""
        return self.oldPasswordEdit.text() if hasattr(self, 'oldPasswordEdit') else ""

    def getNewPassword(self) -> str:
        """获取新密码"""
        return self.newPasswordEdit.text()
