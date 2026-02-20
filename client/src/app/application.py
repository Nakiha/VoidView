"""QApplication 封装"""

import sys
import ctypes
import threading
from typing import Optional
from pathlib import Path

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QThread, Signal, qInstallMessageHandler
from PySide6.QtGui import QIcon
from qfluentwidgets import setThemeColor, setTheme, Theme, InfoBar, InfoBarPosition, SubtitleLabel, IndeterminateProgressRing

from voidview_shared import setup_logging, get_logger

from app.config import user_config
from app.app_state import app_state
from app.local_server import local_server
from api import auth_api, api_client
from ui import LoginDialog, MainWindow, ChangePasswordDialog, ServerConfigDialog
from utils import get_logo_path

# 初始化日志
setup_logging(
    app_name="voidview-client",
    level="DEBUG",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    dev_mode=True,
)

logger = get_logger()


def _qt_message_handler(mode, context, message):
    """Qt 消息处理器 - 将 Qt 日志重定向到 loguru"""
    from PySide6.QtCore import QtMsgType

    # 映射 Qt 消息类型到日志级别
    level_map = {
        QtMsgType.QtDebugMsg: "DEBUG",
        QtMsgType.QtInfoMsg: "INFO",
        QtMsgType.QtWarningMsg: "WARNING",
        QtMsgType.QtCriticalMsg: "ERROR",
        QtMsgType.QtFatalMsg: "CRITICAL",
    }
    level = level_map.get(mode, "INFO")

    # 添加上下文信息
    location = ""
    if context.file:
        location = f" [{context.file}:{context.line}]"

    # 使用 loguru 记录
    logger.log(level, f"[Qt]{location} {message}")


# 安装 Qt 消息处理器
qInstallMessageHandler(_qt_message_handler)


def _exception_hook(exc_type, exc_value, exc_tb):
    """全局异常钩子 - 捕获未处理的异常并记录到日志"""
    import traceback

    # 格式化异常信息
    tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logger.critical(f"未捕获的异常:\n{tb_str}")

    # 调用默认的异常处理器
    sys.__excepthook__(exc_type, exc_value, exc_tb)


def _thread_exception_hook(args):
    """线程异常钩子 - 捕获线程中未处理的异常"""
    import traceback

    # 格式化异常信息
    tb_str = ''.join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_tb))
    thread_name = args.thread.name if args.thread else "unknown"
    logger.critical(f"线程 [{thread_name}] 未捕获的异常:\n{tb_str}")


# 安装全局异常钩子
sys.excepthook = _exception_hook
threading.excepthook = _thread_exception_hook


def _set_windows_app_id():
    """设置 Windows 应用程序 ID，用于任务栏和任务管理器显示"""
    if sys.platform == "win32":
        app_id = "VoidView.VideoQualityEval.1"
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except (AttributeError, OSError):
            pass  # 忽略旧版 Windows 不支持的情况


class ServerCheckWorker(QThread):
    """服务端健康检查工作线程"""
    finished = Signal(bool)  # 检查完成，传递是否成功

    def run(self):
        """执行健康检查"""
        try:
            result = api_client.ping()
            self.finished.emit(result)
        except Exception as e:
            logger.debug(f"服务器检查失败: {e}")
            self.finished.emit(False)


class LocalServerStartWorker(QThread):
    """本地服务器启动工作线程"""
    success = Signal(str)  # 启动成功，传递服务器 URL
    failed = Signal(str)   # 启动失败，传递错误信息

    def run(self):
        """启动本地服务器"""
        try:
            if local_server.start():
                if local_server.wait_for_ready(timeout=15.0):
                    self.success.emit(local_server.url)
                else:
                    self.failed.emit("本地服务器启动超时")
            else:
                self.failed.emit("本地服务器启动失败")
        except Exception as e:
            logger.error(f"启动本地服务器时发生错误: {e}")
            self.failed.emit(f"启动失败: {str(e)}")


class ConnectingSplashScreen(QWidget):
    """连接中的启动画面"""

    serverConnected = Signal()
    serverDisconnected = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._check_worker = None
        self.setupUI()
        self.startServerCheck()

    def setupUI(self):
        """设置界面"""
        self.setFixedSize(400, 200)
        self.setWindowTitle("VoidView - 视频质量评测系统")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Logo
        logo_path = get_logo_path()
        if logo_path.exists():
            from PySide6.QtSvgWidgets import QSvgWidget
            logoWidget = QSvgWidget(str(logo_path), self)
            logoWidget.setFixedSize(48, 48)
            layout.addWidget(logoWidget, alignment=Qt.AlignCenter)

        # 状态文字
        self.statusLabel = SubtitleLabel(self)
        self.statusLabel.setText("正在连接服务器...")
        self.statusLabel.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.statusLabel, alignment=Qt.AlignCenter)

        # 加载指示器
        self.progressRing = IndeterminateProgressRing(self)
        self.progressRing.setFixedSize(32, 32)
        layout.addWidget(self.progressRing, alignment=Qt.AlignCenter)

        # 应用样式
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
            }
            SubtitleLabel {
                color: #ffffff;
            }
        """)

    def startServerCheck(self):
        """开始检查服务器"""
        self._check_worker = ServerCheckWorker()
        self._check_worker.finished.connect(self.onServerCheckFinished)
        self._check_worker.start()

    def onServerCheckFinished(self, success: bool):
        """服务器检查完成"""
        if success:
            self.statusLabel.setText("连接成功")
            self.serverConnected.emit()
        else:
            self.serverDisconnected.emit()

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self._check_worker and self._check_worker.isRunning():
            self._check_worker.quit()
            self._check_worker.wait()
        super().closeEvent(event)


class VoidViewApplication:
    """VoidView 应用程序"""

    def __init__(self):
        # 设置 Windows 应用程序 ID (必须在创建 QApplication 之前)
        _set_windows_app_id()

        # 创建 QApplication
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("VoidView")
        self.app.setApplicationVersion("0.1.0")
        self.app.setOrganizationName("VoidView")
        self.app.setApplicationDisplayName("VoidView - 视频质量评测系统")

        # 设置应用图标
        logo_path = get_logo_path()
        if logo_path.exists():
            self.app.setWindowIcon(QIcon(str(logo_path)))

        # 设置主题色 (VoidView 主题蓝)
        setThemeColor("#0078d4")

        # 自动跟随系统主题
        setTheme(Theme.AUTO)

        # 应用退出时清理资源
        self.app.aboutToQuit.connect(self._onAppQuit)

        # 窗口引用
        self._splashScreen: Optional[ConnectingSplashScreen] = None
        self._loginDialog: Optional[LoginDialog] = None
        self._mainWindow: Optional[MainWindow] = None
        self._serverConfigDialog: Optional[ServerConfigDialog] = None
        self._localServerWorker: Optional[LocalServerStartWorker] = None

        logger.info("VoidView 客户端初始化完成")

    def run(self):
        """运行应用"""
        # 直接显示连接中的启动画面
        self.showConnectingSplash()
        return self.app.exec()

    def showConnectingSplash(self):
        """显示连接中的启动画面"""
        # 关闭其他窗口
        self._closeAllWindows()

        # 创建并显示启动画面
        self._splashScreen = ConnectingSplashScreen()
        self._splashScreen.serverConnected.connect(self.onServerConnected)
        self._splashScreen.serverDisconnected.connect(self.showServerConfigDialog)
        self._splashScreen.show()

    def onServerConnected(self):
        """服务器连接成功"""
        logger.info("服务器连接成功")
        if self._splashScreen:
            self._splashScreen.close()
            self._splashScreen = None
        self.showLogin()

    def showServerConfigDialog(self):
        """显示服务器配置对话框"""
        # 关闭启动画面
        if self._splashScreen:
            self._splashScreen.close()
            self._splashScreen = None

        self._closeAllWindows()

        # 创建并显示配置对话框
        self._serverConfigDialog = ServerConfigDialog()
        self._serverConfigDialog.configSaved.connect(self.onConfigSaved)
        self._serverConfigDialog.localModeRequested.connect(self.onLocalModeRequested)
        self._serverConfigDialog.exitRequested.connect(self.app.quit)
        self._serverConfigDialog.show()

    def onConfigSaved(self, new_url: str):
        """配置保存后的回调"""
        logger.info(f"服务器地址已更新: {new_url}")
        # 关闭配置对话框
        if self._serverConfigDialog:
            self._serverConfigDialog.close()
            self._serverConfigDialog = None

        # 重新检查服务器 - 显示启动画面
        self.showConnectingSplash()

    def onLocalModeRequested(self):
        """用户请求使用本地模式"""
        logger.info("用户请求启动本地服务器模式")

        # 启动本地服务器
        self._localServerWorker = LocalServerStartWorker()
        self._localServerWorker.success.connect(self.onLocalServerStarted)
        self._localServerWorker.failed.connect(self.onLocalServerFailed)
        self._localServerWorker.start()

    def onLocalServerStarted(self, server_url: str):
        """本地服务器启动成功"""
        logger.info(f"本地服务器已启动: {server_url}")

        # 更新配置
        user_config.set_server_url(server_url)
        api_client.update_base_url(server_url)

        # 关闭配置对话框
        if self._serverConfigDialog:
            self._serverConfigDialog.close()
            self._serverConfigDialog = None

        # 显示登录窗口
        self.showLogin()

    def onLocalServerFailed(self, error: str):
        """本地服务器启动失败"""
        logger.error(f"本地服务器启动失败: {error}")

        # 显示错误提示
        if self._serverConfigDialog:
            InfoBar.error(
                title="启动失败",
                content=error,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self._serverConfigDialog
            )
            self._serverConfigDialog.localModeBtn.setEnabled(True)
            self._serverConfigDialog.localModeBtn.setText("启动本地服务器")

    def showLogin(self):
        """显示登录窗口"""
        # 关闭其他窗口
        self._closeAllWindows()

        # 创建并显示登录窗口
        self._loginDialog = LoginDialog()
        self._loginDialog.loginSuccess.connect(self.onLoginSuccess)
        self._loginDialog.show()

    def onLoginSuccess(self, user):
        """登录成功回调"""
        logger.info(f"用户登录成功: {user.username}")
        # 保存用户状态
        app_state.set_user(user)

        # 关闭登录窗口
        if self._loginDialog:
            self._loginDialog.close()
            self._loginDialog = None

        # 显示主窗口
        self._mainWindow = MainWindow()
        self._mainWindow.logoutRequested.connect(self.onLogout)
        self._mainWindow.show()

    def onLogout(self):
        """用户退出登录"""
        logger.info("用户退出登录")
        # 停止本地服务器（如果正在运行）
        if local_server.is_running:
            local_server.stop()
        self.showLogin()

    def _closeAllWindows(self):
        """关闭所有窗口"""
        if self._splashScreen:
            self._splashScreen.close()
            self._splashScreen = None
        if self._loginDialog:
            self._loginDialog.close()
            self._loginDialog = None
        if self._mainWindow:
            self._mainWindow.close()
            self._mainWindow = None
        if self._serverConfigDialog:
            self._serverConfigDialog.close()
            self._serverConfigDialog = None

    def _onAppQuit(self):
        """应用退出时的清理工作"""
        logger.info("应用正在退出，清理资源...")

        # 停止本地服务器（如果正在运行）
        if local_server.is_running:
            logger.info("停止本地服务器...")
            local_server.stop()

        logger.info("资源清理完成")
