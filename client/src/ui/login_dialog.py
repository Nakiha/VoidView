"""登录对话框 - Fluent Design 风格

遵循 Microsoft Fluent Design System 原则：
- Light/Depth/Motion/Material/Scale
- 主题感知颜色，自动适配明暗模式
- 层次感与深度效果
"""

from PySide6.QtCore import Signal, Qt, QThread, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect, QSpacerItem, QSizePolicy
from PySide6.QtGui import QColor, QLinearGradient, QPalette, QFont
from PySide6.QtSvgWidgets import QSvgWidget
from qfluentwidgets import (
    FluentWindow, SubtitleLabel, BodyLabel, StrongBodyLabel,
    CaptionLabel, LineEdit, PrimaryPushButton, PushButton,
    InfoBar, InfoBarPosition, MessageBoxBase, isDarkTheme,
    setTheme, Theme, FluentIcon, IconWidget
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


class AcrylicLeftPanel(QWidget):
    """左侧品牌面板 - Fluent Design 风格
    
    特点：
    - 渐变背景色（亮色/暗色主题自适应）
    - 品牌色强调
    - 清晰的视觉层次
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("acrylicLeftPanel")
        self.setFixedWidth(280)
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """设置 UI 布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 48, 40, 48)
        layout.setSpacing(0)
        
        # 顶部留白
        layout.addStretch(1)
        
        # Logo 区域
        logo_container = QWidget()
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(16)
        
        # Logo 图标
        logo_path = get_logo_path()
        if logo_path.exists():
            logoWidget = QSvgWidget(str(logo_path), logo_container)
            logoWidget.setFixedSize(72, 72)
            logo_layout.addWidget(logoWidget, alignment=Qt.AlignCenter)
        else:
            # 回退到图标字体
            iconLabel = IconWidget(FluentIcon.VIDEO, logo_container)
            iconLabel.setFixedSize(72, 72)
            logo_layout.addWidget(iconLabel, alignment=Qt.AlignCenter)
        
        logo_layout.addSpacing(8)
        
        # 应用名称 - 使用 StrongBodyLabel
        nameLabel = StrongBodyLabel("VoidView", logo_container)
        nameLabel.setAlignment(Qt.AlignCenter)
        name_font = nameLabel.font()
        name_font.setPointSize(20)
        name_font.setWeight(QFont.DemiBold)
        nameLabel.setFont(name_font)
        logo_layout.addWidget(nameLabel)
        
        # 副标题
        subtitleLabel = BodyLabel("视频质量评测系统", logo_container)
        subtitleLabel.setAlignment(Qt.AlignCenter)
        sub_font = subtitleLabel.font()
        sub_font.setPointSize(11)
        subtitleLabel.setFont(sub_font)
        logo_layout.addWidget(subtitleLabel)
        
        layout.addWidget(logo_container)
        
        # 底部留白
        layout.addStretch(2)
        
        # 底部版本信息
        versionLabel = CaptionLabel("v0.1.0", self)
        versionLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(versionLabel)
    
    def _apply_style(self):
        """应用样式 - 主题感知"""
        # 样式会在 paintEvent 中动态绘制
        pass
    
    def paintEvent(self, event):
        """重绘事件 - 绘制渐变背景"""
        from PySide6.QtGui import QPainter, QPen, QBrush
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 根据主题选择渐变色
        if isDarkTheme():
            # 暗色模式：深蓝渐变
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0, QColor("#1a1a2e"))
            gradient.setColorAt(0.5, QColor("#16213e"))
            gradient.setColorAt(1, QColor("#0f3460"))
        else:
            # 亮色模式：品牌蓝渐变
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0, QColor("#0078d4"))
            gradient.setColorAt(0.5, QColor("#106ebe"))
            gradient.setColorAt(1, QColor("#005a9e"))
        
        painter.fillRect(self.rect(), QBrush(gradient))
        
        # 添加右侧边框线作为分隔
        if isDarkTheme():
            pen = QPen(QColor(255, 255, 255, 20), 1)
        else:
            pen = QPen(QColor(255, 255, 255, 40), 1)
        painter.setPen(pen)
        painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())


class LoginFormPanel(QWidget):
    """右侧登录表单面板
    
    Fluent Design 特点：
    - 清晰的视觉层次
    - 适当的留白和间距
    - 主题感知的文字颜色
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("loginFormPanel")
        self._setup_ui()
    
    def _setup_ui(self):
        """设置 UI 布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 56, 48, 56)
        layout.setSpacing(0)
        
        # 顶部留白
        layout.addStretch(1)
        
        # 欢迎区域
        welcome_container = QWidget()
        welcome_layout = QVBoxLayout(welcome_container)
        welcome_layout.setContentsMargins(0, 0, 0, 0)
        welcome_layout.setSpacing(8)
        
        # 欢迎标题 - 使用 StrongBodyLabel，主题感知
        welcomeLabel = StrongBodyLabel("欢迎回来", welcome_container)
        welcome_font = welcomeLabel.font()
        welcome_font.setPointSize(28)
        welcome_font.setWeight(QFont.DemiBold)
        welcomeLabel.setFont(welcome_font)
        welcome_layout.addWidget(welcomeLabel)
        
        # 提示文字 - 主题感知
        hintLabel = BodyLabel("请登录您的账号以继续", welcome_container)
        hint_font = hintLabel.font()
        hint_font.setPointSize(12)
        hintLabel.setFont(hint_font)
        welcome_layout.addWidget(hintLabel)
        
        layout.addWidget(welcome_container)
        layout.addSpacing(40)
        
        # 表单区域
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(20)
        
        # 用户名
        username_container = QWidget()
        username_layout = QVBoxLayout(username_container)
        username_layout.setContentsMargins(0, 0, 0, 0)
        username_layout.setSpacing(8)
        
        usernameTitle = BodyLabel("用户名", username_container)
        username_layout.addWidget(usernameTitle)
        
        self.usernameEdit = LineEdit(username_container)
        self.usernameEdit.setPlaceholderText("请输入用户名")
        self.usernameEdit.setClearButtonEnabled(True)
        self.usernameEdit.setFixedHeight(40)
        username_layout.addWidget(self.usernameEdit)
        
        form_layout.addWidget(username_container)
        
        # 密码
        password_container = QWidget()
        password_layout = QVBoxLayout(password_container)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(8)
        
        passwordTitle = BodyLabel("密码", password_container)
        password_layout.addWidget(passwordTitle)
        
        self.passwordEdit = LineEdit(password_container)
        self.passwordEdit.setPlaceholderText("请输入密码")
        self.passwordEdit.setEchoMode(LineEdit.Password)
        self.passwordEdit.setClearButtonEnabled(True)
        self.passwordEdit.setFixedHeight(40)
        password_layout.addWidget(self.passwordEdit)
        
        form_layout.addWidget(password_container)
        
        layout.addWidget(form_container)
        layout.addSpacing(32)
        
        # 登录按钮
        self.loginBtn = PrimaryPushButton("登录", self)
        self.loginBtn.setFixedHeight(40)
        self.loginBtn.clicked.connect(self._on_login_clicked)
        layout.addWidget(self.loginBtn)
        
        # 底部留白
        layout.addStretch(2)
        
        # 设置 tab 顺序
        self.setTabOrder(self.usernameEdit, self.passwordEdit)
        self.setTabOrder(self.passwordEdit, self.loginBtn)
    
    def _on_login_clicked(self):
        """登录按钮点击 - 转发信号"""
        # 由父窗口连接处理
        pass


class LoginDialog(FluentWindow):
    """登录对话框 - Fluent Design 风格
    
    遵循原则：
    1. Light - 光影效果和层次
    2. Depth - 视觉层次和分隔
    3. Motion - 平滑过渡（由 qfluentwidgets 提供）
    4. Material - Mica/Acrylic 材质
    5. Scale - 响应式布局
    
    主题适配：
    - 自动跟随系统主题
    - 所有文字颜色主题感知
    - 渐变和背景色动态调整
    """
    
    loginSuccess = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_user = None
        self._pending_user = None
        self._login_worker = None

        self.setWindowTitle("VoidView - 登录")
        self.setFixedSize(720, 500)

        # 启用 Mica 效果 (Windows 11 材质)
        self.micaEnabled = True

        # 隐藏导航栏（登录界面不需要）
        self.navigationInterface.hide()
        self.navigationInterface.panel.setReturnButtonVisible(False)

        # 禁用最大化按钮
        self.titleBar.maxBtn.hide()

        # 隐藏 stackedWidget
        self.stackedWidget.hide()

        # 调整内容区域边距
        self.widgetLayout.setContentsMargins(0, 48, 0, 0)

        # 创建内容页面
        self.contentPage = self._createContentPage()
        self.widgetLayout.addWidget(self.contentPage)

        # 调整标题栏位置
        self._adjustTitleBar()

        # 居中显示
        self._centerWindow()

    def _adjustTitleBar(self):
        """调整标题栏位置"""
        self.titleBar.move(0, 0)
        self.titleBar.resize(self.width(), self.titleBar.height())

    def resizeEvent(self, event):
        """重写 resizeEvent"""
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
        """创建内容页面 - 左右分栏布局"""
        page = QWidget()
        page.setObjectName("loginContentPage")
        
        mainLayout = QHBoxLayout(page)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        # 左侧品牌面板
        self.leftPanel = AcrylicLeftPanel(page)
        mainLayout.addWidget(self.leftPanel)

        # 右侧登录表单
        self.formPanel = LoginFormPanel(page)
        mainLayout.addWidget(self.formPanel, 1)

        # 连接信号
        self.formPanel.usernameEdit.returnPressed.connect(self.attemptLogin)
        self.formPanel.passwordEdit.returnPressed.connect(self.attemptLogin)
        self.formPanel.loginBtn.clicked.disconnect()
        self.formPanel.loginBtn.clicked.connect(self.attemptLogin)

        return page

    def attemptLogin(self):
        """尝试登录"""
        if self._login_worker and self._login_worker.isRunning():
            return

        username = self.formPanel.usernameEdit.text().strip()
        password = self.formPanel.passwordEdit.text()

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

        # 禁用登录按钮
        self.formPanel.loginBtn.setEnabled(False)
        self.formPanel.loginBtn.setText("登录中...")

        # 创建并启动登录线程
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
        self.formPanel.passwordEdit.clear()
        self.formPanel.passwordEdit.setFocus()

    def resetLoginButton(self):
        """重置登录按钮状态"""
        self.formPanel.loginBtn.setEnabled(True)
        self.formPanel.loginBtn.setText("登录")

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self._login_worker and self._login_worker.isRunning():
            self._login_worker.quit()
            self._login_worker.wait()
        super().closeEvent(event)

    def clearForm(self):
        """清空表单"""
        self.formPanel.usernameEdit.clear()
        self.formPanel.passwordEdit.clear()
        self.formPanel.usernameEdit.setFocus()


class ChangePasswordDialog(MessageBoxBase):
    """修改密码对话框 - Fluent Design 风格"""

    def __init__(self, must_change: bool = False, parent=None):
        super().__init__(parent)
        self.must_change = must_change

        # 标题
        self.titleLabel = SubtitleLabel("修改密码" if not must_change else "首次登录，请修改密码", self)
        self.viewLayout.addWidget(self.titleLabel)

        # 当前密码 (如果不是强制修改)
        if not must_change:
            self.oldPasswordLabel = BodyLabel("当前密码", self)
            self.viewLayout.addWidget(self.oldPasswordLabel)

            self.oldPasswordEdit = LineEdit(self)
            self.oldPasswordEdit.setEchoMode(LineEdit.Password)
            self.oldPasswordEdit.setPlaceholderText("请输入当前密码")
            self.viewLayout.addWidget(self.oldPasswordEdit)

        # 新密码
        self.newPasswordLabel = BodyLabel("新密码", self)
        self.viewLayout.addWidget(self.newPasswordLabel)

        self.newPasswordEdit = LineEdit(self)
        self.newPasswordEdit.setEchoMode(LineEdit.Password)
        self.newPasswordEdit.setPlaceholderText("请输入新密码 (至少6位)")
        self.viewLayout.addWidget(self.newPasswordEdit)

        # 确认新密码
        self.confirmPasswordLabel = BodyLabel("确认新密码", self)
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
