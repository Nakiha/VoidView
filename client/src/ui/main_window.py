"""主窗口"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon,
    SubtitleLabel, BodyLabel, PushButton, AvatarWidget,
    InfoBar, InfoBarPosition, StrongBodyLabel
)

from app.config import settings
from app.app_state import app_state
from api import auth_api


class MainWindow(FluentWindow):
    """主窗口"""

    # 退出登录信号
    logoutRequested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VoidView - 视频质量评测系统")
        self.resize(settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)
        self.setMinimumSize(settings.WINDOW_MIN_WIDTH, settings.WINDOW_MIN_HEIGHT)

        # 创建页面
        self.homePage = self._createHomePage()
        self.experimentPage = self._createPlaceholderPage("实验管理", "实验管理功能开发中...")
        self.evaluationPage = self._createPlaceholderPage("评测", "评测功能开发中...")
        self.reviewPage = self._createPlaceholderPage("评审", "评审功能开发中...")
        self.statisticsPage = self._createPlaceholderPage("统计", "统计功能开发中...")
        self.userInfoPage = self._createUserInfoPage()

        # root 专用页面
        self.userManagementPage = None
        if app_state.is_root():
            from ui.pages.user_management.user_list_page import UserListPage
            self.userManagementPage = UserListPage(self)

        # 初始化导航
        self._setupNavigation()

    def _createHomePage(self) -> QWidget:
        """创建首页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)

        # 欢迎标题
        user = app_state.current_user
        title = StrongBodyLabel(page)
        title.setText(f"欢迎，{user.display_name if user else '用户'}")
        title.setStyleSheet("font-size: 24px; font-weight: 600;")
        layout.addWidget(title)

        layout.addSpacing(20)

        # 快速统计
        statsLayout = QHBoxLayout()

        # TODO: 添加实际的统计数据
        stats = [
            ("进行中的实验", 0),
            ("待评测", 0),
            ("待评审", 0),
        ]

        for labelText, count in stats:
            statWidget = QWidget()
            statLayout = QVBoxLayout(statWidget)
            statLayout.setContentsMargins(20, 20, 20, 20)

            countLabel = StrongBodyLabel(statWidget)
            countLabel.setText(str(count))
            countLabel.setStyleSheet("font-size: 32px; font-weight: bold;")
            statLayout.addWidget(countLabel)

            nameLabel = BodyLabel(statWidget)
            nameLabel.setText(labelText)
            statLayout.addWidget(nameLabel)

            statWidget.setStyleSheet("""
                QWidget {
                    background-color: rgba(255, 255, 255, 0.05);
                    border-radius: 8px;
                }
            """)
            statsLayout.addWidget(statWidget)

        statsLayout.addStretch()
        layout.addLayout(statsLayout)

        layout.addStretch()
        return page

    def _createPlaceholderPage(self, titleText: str, message: str) -> QWidget:
        """创建占位页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)

        titleLabel = StrongBodyLabel(page)
        titleLabel.setText(titleText)
        titleLabel.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(titleLabel, alignment=Qt.AlignCenter)

        msgLabel = BodyLabel(page)
        msgLabel.setText(message)
        layout.addWidget(msgLabel, alignment=Qt.AlignCenter)

        return page

    def _createUserInfoPage(self) -> QWidget:
        """创建用户信息页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)

        user = app_state.current_user

        # 标题
        title = StrongBodyLabel(page)
        title.setText("个人信息")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(title)

        layout.addSpacing(20)

        if user:
            # 用户信息卡片
            infoWidget = QWidget()
            infoLayout = QVBoxLayout(infoWidget)
            infoLayout.setSpacing(12)

            # 用户名
            usernameLabel = BodyLabel(infoWidget)
            usernameLabel.setText(f"用户名: {user.username}")
            infoLayout.addWidget(usernameLabel)

            # 显示名称
            displayNameLabel = BodyLabel(infoWidget)
            displayNameLabel.setText(f"显示名称: {user.display_name}")
            infoLayout.addWidget(displayNameLabel)

            # 角色
            roleText = "管理员" if user.role.value == "root" else "测试人员"
            roleLabel = BodyLabel(infoWidget)
            roleLabel.setText(f"角色: {roleText}")
            infoLayout.addWidget(roleLabel)

            infoWidget.setStyleSheet("""
                QWidget {
                    background-color: rgba(255, 255, 255, 0.05);
                    border-radius: 8px;
                    padding: 20px;
                }
            """)
            layout.addWidget(infoWidget)

        layout.addStretch()
        return page

    def _setupNavigation(self):
        """设置导航"""
        # 将页面添加到 stackedWidget
        self.stackedWidget.addWidget(self.homePage)
        self.stackedWidget.addWidget(self.experimentPage)
        self.stackedWidget.addWidget(self.evaluationPage)
        self.stackedWidget.addWidget(self.reviewPage)
        self.stackedWidget.addWidget(self.statisticsPage)
        self.stackedWidget.addWidget(self.userInfoPage)
        if self.userManagementPage:
            self.stackedWidget.addWidget(self.userManagementPage)

        # 主要导航项
        self.navigationInterface.addItem(
            routeKey='home',
            text='首页',
            icon=FluentIcon.HOME,
            onClick=lambda: self.switchTo(self.homePage)
        )
        self.navigationInterface.addItem(
            routeKey='experiment',
            text='实验管理',
            icon=FluentIcon.FOLDER,
            onClick=lambda: self.switchTo(self.experimentPage)
        )
        self.navigationInterface.addItem(
            routeKey='evaluation',
            text='评测',
            icon=FluentIcon.PLAY,
            onClick=lambda: self.switchTo(self.evaluationPage)
        )
        self.navigationInterface.addItem(
            routeKey='review',
            text='评审',
            icon=FluentIcon.ACCEPT,
            onClick=lambda: self.switchTo(self.reviewPage)
        )
        self.navigationInterface.addItem(
            routeKey='statistics',
            text='统计',
            icon=FluentIcon.BOOK_SHELF,
            onClick=lambda: self.switchTo(self.statisticsPage)
        )

        # 用户管理 (仅 root)
        if self.userManagementPage:
            self.navigationInterface.addItem(
                routeKey='users',
                text='用户管理',
                icon=FluentIcon.PEOPLE,
                onClick=lambda: self.switchTo(self.userManagementPage),
                position=NavigationItemPosition.BOTTOM
            )

        # 用户信息
        user = app_state.current_user
        if user:
            self.navigationInterface.addItem(
                routeKey='user_info',
                text=user.display_name,
                icon=FluentIcon.SETTING,
                onClick=lambda: self.switchTo(self.userInfoPage),
                position=NavigationItemPosition.BOTTOM
            )

        # 退出登录
        self.navigationInterface.addItem(
            routeKey='logout',
            text='退出登录',
            icon=FluentIcon.CLOSE,
            onClick=self._logout,
            position=NavigationItemPosition.BOTTOM
        )

        # 默认显示首页
        self.switchTo(self.homePage)

    def _logout(self):
        """退出登录"""
        from qfluentwidgets import MessageBox

        box = MessageBox("确认退出", "确定要退出登录吗？", self)
        if box.exec():
            auth_api.logout()
            app_state.logout()
            self.close()
            # 发出信号通知重新显示登录窗口
            self.logoutRequested.emit()
