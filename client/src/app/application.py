"""QApplication 封装"""

import sys
from typing import Optional

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt
from qfluentwidgets import setThemeColor, setTheme, Theme, isDarkTheme

from app.config import settings
from app.app_state import app_state
from api import auth_api
from ui import LoginDialog, MainWindow, ChangePasswordDialog


class VoidViewApplication:
    """VoidView 应用程序"""

    def __init__(self):
        # 创建 QApplication
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("VoidView")
        self.app.setApplicationVersion("0.1.0")

        # 设置主题色 (VoidView 主题蓝)
        setThemeColor("#0078d4")

        # 自动跟随系统主题
        setTheme(Theme.AUTO)

        # 窗口引用
        self._loginDialog: Optional[LoginDialog] = None
        self._mainWindow: Optional[MainWindow] = None

    def run(self):
        """运行应用"""
        self.showLogin()
        return self.app.exec()

    def showLogin(self):
        """显示登录窗口"""
        # 关闭主窗口
        if self._mainWindow:
            self._mainWindow.close()
            self._mainWindow = None

        # 创建并显示登录窗口
        self._loginDialog = LoginDialog()
        self._loginDialog.loginSuccess.connect(self.onLoginSuccess)
        self._loginDialog.show()

    def onLoginSuccess(self, user):
        """登录成功回调"""
        # 保存用户状态
        app_state.set_user(user)

        # 关闭登录窗口
        if self._loginDialog:
            self._loginDialog.close()
            self._loginDialog = None

        # 显示主窗口
        self._mainWindow = MainWindow()
        self._mainWindow.logoutRequested.connect(self.showLogin)
        self._mainWindow.show()
