"""登录对话框 - Fluent Design 风格"""

from PySide6.QtCore import Signal, Qt, QThread
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtSvgWidgets import QSvgWidget
from qfluentwidgets import (
    FluentWindow, SubtitleLabel, BodyLabel, LineEdit, PrimaryPushButton,
    InfoBar, InfoBarPosition, MessageBoxBase
)

from api import auth_api, APIError, ServerUnreachableError
from models import UserResponse
from utils import get_logo_path


class LoginWorker(QThread):
    """后台登录工作线程"""
    success = Signal(object)  # 登录成功，传递 user 对象
    error = Signal(str)       # 登录失败，传递错误消息

    def __init__(self, username: str, password: str, parent=None):
        super().__init__(parent)
        self.username = username
        self.password = password

    def run(self):
        """执行登录"""
        try:
            token_response = auth_api.login(self.username, self.password)
            self.success.emit(token_response.user)
        except APIError as e:
            self.error.emit(e.message)
        except ServerUnreachableError as e:
            self.error.emit(e.message)
        except Exception as e:
            self.error.emit(f"登录失败: {str(e)}")


class LoginDialog(FluentWindow):
    """登录对话框 - Fluent Design 风格"""

    loginSuccess = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_user = None
        self._pending_user = None
        self._login_worker = None  # 登录工作线程

        self.setWindowTitle("VoidView - 登录")
        self.setFixedSize(700, 480)

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
        mainLayout = QHBoxLayout(page)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        # 左侧装饰面板
        leftPanel = QWidget()
        leftPanel.setFixedWidth(260)
        leftPanel.setObjectName("leftPanel")
        leftLayout = QVBoxLayout(leftPanel)
        leftLayout.setContentsMargins(32, 32, 32, 32)
        leftLayout.setSpacing(16)

        leftLayout.addStretch()

        # Logo/图标 (使用 SVG)
        logo_path = get_logo_path()
        if logo_path.exists():
            logoWidget = QSvgWidget(str(logo_path), leftPanel)
            logoWidget.setFixedSize(64, 64)
            leftLayout.addWidget(logoWidget, alignment=Qt.AlignCenter)
        else:
            # 回退到文字
            logoLabel = SubtitleLabel(leftPanel)
            logoLabel.setText("◆")
            logoLabel.setAlignment(Qt.AlignCenter)
            logoLabel.setStyleSheet("font-size: 48px; color: #0078d4;")
            leftLayout.addWidget(logoLabel)

        # 应用名称
        nameLabel = SubtitleLabel(leftPanel)
        nameLabel.setText("VoidView")
        nameLabel.setAlignment(Qt.AlignCenter)
        leftLayout.addWidget(nameLabel)

        # 副标题
        subtitleLabel = BodyLabel(leftPanel)
        subtitleLabel.setText("视频质量评测系统")
        subtitleLabel.setAlignment(Qt.AlignCenter)
        leftLayout.addWidget(subtitleLabel)

        leftLayout.addStretch()

        # 版本信息
        versionLabel = BodyLabel(leftPanel)
        versionLabel.setText("v0.1.0")
        versionLabel.setAlignment(Qt.AlignCenter)
        versionLabel.setStyleSheet("color: rgba(255, 255, 255, 0.5);")
        leftLayout.addWidget(versionLabel)

        mainLayout.addWidget(leftPanel)

        # 右侧登录表单
        rightPanel = QWidget()
        rightPanel.setObjectName("rightPanel")
        rightLayout = QVBoxLayout(rightPanel)
        rightLayout.setContentsMargins(48, 48, 48, 48)
        rightLayout.setSpacing(16)

        rightLayout.addStretch()

        # 欢迎标题
        welcomeLabel = SubtitleLabel(rightPanel)
        welcomeLabel.setText("欢迎回来")
        welcomeLabel.setStyleSheet("font-size: 24px; font-weight: 600;")
        rightLayout.addWidget(welcomeLabel)

        # 提示文字
        hintLabel = BodyLabel(rightPanel)
        hintLabel.setText("请登录您的账号以继续")
        rightLayout.addWidget(hintLabel)

        rightLayout.addSpacing(24)

        # 用户名
        usernameTitle = BodyLabel(rightPanel)
        usernameTitle.setText("用户名")
        rightLayout.addWidget(usernameTitle)

        self.usernameEdit = LineEdit(rightPanel)
        self.usernameEdit.setPlaceholderText("请输入用户名")
        self.usernameEdit.setClearButtonEnabled(True)
        self.usernameEdit.setFixedHeight(36)
        rightLayout.addWidget(self.usernameEdit)

        rightLayout.addSpacing(8)

        # 密码
        passwordTitle = BodyLabel(rightPanel)
        passwordTitle.setText("密码")
        rightLayout.addWidget(passwordTitle)

        self.passwordEdit = LineEdit(rightPanel)
        self.passwordEdit.setPlaceholderText("请输入密码")
        self.passwordEdit.setEchoMode(LineEdit.Password)
        self.passwordEdit.setClearButtonEnabled(True)
        self.passwordEdit.setFixedHeight(36)
        rightLayout.addWidget(self.passwordEdit)

        rightLayout.addSpacing(16)

        # 登录按钮
        self.loginBtn = PrimaryPushButton(rightPanel)
        self.loginBtn.setText("登录")
        self.loginBtn.setFixedHeight(36)
        self.loginBtn.clicked.connect(self.attemptLogin)
        rightLayout.addWidget(self.loginBtn)

        # 回车登录
        self.usernameEdit.returnPressed.connect(self.attemptLogin)
        self.passwordEdit.returnPressed.connect(self.attemptLogin)

        rightLayout.addStretch()

        mainLayout.addWidget(rightPanel, 1)

        # 左侧面板样式
        leftPanel.setStyleSheet("""
            #leftPanel {
                background-color: rgba(0, 120, 212, 0.8);
            }
        """)

        return page

    def attemptLogin(self):
        """尝试登录"""
        # 如果正在登录，忽略
        if self._login_worker and self._login_worker.isRunning():
            return

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

        # 禁用登录按钮，显示加载状态
        self.loginBtn.setEnabled(False)
        self.loginBtn.setText("登录中...")

        # 创建并启动登录工作线程
        self._login_worker = LoginWorker(username, password)
        self._login_worker.success.connect(self.onLoginSuccess)
        self._login_worker.error.connect(self.onLoginError)
        self._login_worker.start()

    def onLoginSuccess(self, user):
        """登录成功回调"""
        self.current_user = user
        self.resetLoginButton()
        self.loginSuccess.emit(self.current_user)

    def onLoginError(self, message: str):
        """登录失败回调"""
        self.resetLoginButton()
        InfoBar.error(
            title="登录失败",
            content=message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
        self.passwordEdit.clear()
        self.passwordEdit.setFocus()

    def resetLoginButton(self):
        """重置登录按钮状态"""
        self.loginBtn.setEnabled(True)
        self.loginBtn.setText("登录")

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 确保工作线程被正确清理
        if self._login_worker and self._login_worker.isRunning():
            self._login_worker.quit()
            self._login_worker.wait()
        super().closeEvent(event)

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
