"""用户列表页面"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem
from qfluentwidgets import (
    SubtitleLabel, TableWidget, PrimaryPushButton, PushButton,
    LineEdit, ComboBox, InfoBar, InfoBarPosition, MessageBoxBase,
    SwitchButton, BodyLabel
)

from api import users_api, APIError
from voidview_shared import UserRole


class UserListPage(QWidget):
    """用户列表页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        self.loadUsers()

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题栏
        headerLayout = QHBoxLayout()
        title = SubtitleLabel(self)
        title.setText("用户管理")
        headerLayout.addWidget(title)
        headerLayout.addStretch()

        self.createBtn = PrimaryPushButton(self)
        self.createBtn.setText("创建账号")
        self.createBtn.clicked.connect(self.showCreateDialog)
        headerLayout.addWidget(self.createBtn)

        layout.addLayout(headerLayout)

        # 用户表格
        self.table = TableWidget(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "用户名", "显示名称", "角色", "状态", "最后登录", "操作"
        ])
        self.table.verticalHeader().hide()
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)

        # 设置列宽
        self.table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.table)

    def loadUsers(self):
        """加载用户列表"""
        try:
            result = users_api.list_users()
            users = result.get("items", [])

            self.table.setRowCount(len(users))

            for row, user in enumerate(users):
                # 用户名
                self.table.setItem(row, 0, QTableWidgetItem(user.username))

                # 显示名称
                self.table.setItem(row, 1, QTableWidgetItem(user.display_name))

                # 角色
                roleText = "管理员" if user.role == UserRole.ROOT else "测试人员"
                self.table.setItem(row, 2, QTableWidgetItem(roleText))

                # 状态开关
                statusWidget = QWidget()
                statusLayout = QHBoxLayout(statusWidget)
                statusLayout.setContentsMargins(8, 4, 8, 4)

                switch = SwitchButton()
                switch.setChecked(user.is_active)
                switch.checkedChanged.connect(
                    lambda checked, uid=user.id: self.toggleUserStatus(uid, checked)
                )
                statusLayout.addWidget(switch)
                statusLayout.addStretch()

                self.table.setCellWidget(row, 3, statusWidget)

                # 最后登录
                lastLogin = user.last_login_at.strftime("%Y-%m-%d %H:%M") if user.last_login_at else "从未登录"
                self.table.setItem(row, 4, QTableWidgetItem(lastLogin))

                # 操作按钮
                actionWidget = QWidget()
                actionLayout = QHBoxLayout(actionWidget)
                actionLayout.setContentsMargins(8, 4, 8, 4)

                resetBtn = PushButton(actionWidget)
                resetBtn.setText("重置密码")
                resetBtn.clicked.connect(lambda checked, uid=user.id, uname=user.username: self.resetPassword(uid, uname))
                actionLayout.addWidget(resetBtn)

                self.table.setCellWidget(row, 5, actionWidget)

        except APIError as e:
            InfoBar.error(
                title="加载失败",
                content=e.message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

    def toggleUserStatus(self, user_id: int, active: bool):
        """切换用户状态"""
        try:
            result = users_api.toggle_active(user_id)
            InfoBar.success(
                title="成功",
                content=result.get("message", "操作成功"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except APIError as e:
            InfoBar.error(
                title="操作失败",
                content=e.message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            # 刷新列表恢复状态
            self.loadUsers()

    def resetPassword(self, user_id: int, username: str):
        """重置密码"""
        dialog = ResetPasswordDialog(username, self)
        if dialog.exec():
            new_password = dialog.getNewPassword()
            try:
                users_api.reset_password(user_id, new_password)
                InfoBar.success(
                    title="成功",
                    content=f"已重置 {username} 的密码",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except APIError as e:
                InfoBar.error(
                    title="重置失败",
                    content=e.message,
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )

    def showCreateDialog(self):
        """显示创建用户对话框"""
        dialog = CreateUserDialog(self)
        if dialog.exec():
            data = dialog.getData()
            try:
                users_api.create_user(
                    username=data['username'],
                    password=data['password'],
                    display_name=data['display_name'],
                    role=UserRole(data['role'])
                )
                InfoBar.success(
                    title="成功",
                    content=f"账号 {data['username']} 创建成功",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                self.loadUsers()
            except APIError as e:
                InfoBar.error(
                    title="创建失败",
                    content=e.message,
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )


class CreateUserDialog(MessageBoxBase):
    """创建用户对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 标题
        self.titleLabel = SubtitleLabel(self)
        self.titleLabel.setText("创建新账号")
        self.viewLayout.addWidget(self.titleLabel)

        # 用户名
        self.usernameLabel = BodyLabel(self)
        self.usernameLabel.setText("用户名")
        self.viewLayout.addWidget(self.usernameLabel)

        self.usernameEdit = LineEdit(self)
        self.usernameEdit.setPlaceholderText("登录用户名")
        self.viewLayout.addWidget(self.usernameEdit)

        # 显示名称
        self.displayNameLabel = BodyLabel(self)
        self.displayNameLabel.setText("显示名称")
        self.viewLayout.addWidget(self.displayNameLabel)

        self.displayNameEdit = LineEdit(self)
        self.displayNameEdit.setPlaceholderText("用户显示名称")
        self.viewLayout.addWidget(self.displayNameEdit)

        # 密码
        self.passwordLabel = BodyLabel(self)
        self.passwordLabel.setText("初始密码")
        self.viewLayout.addWidget(self.passwordLabel)

        self.passwordEdit = LineEdit(self)
        self.passwordEdit.setEchoMode(LineEdit.Password)
        self.passwordEdit.setPlaceholderText("至少6位")
        self.viewLayout.addWidget(self.passwordEdit)

        # 角色
        self.roleLabel = BodyLabel(self)
        self.roleLabel.setText("角色")
        self.viewLayout.addWidget(self.roleLabel)

        self.roleCombo = ComboBox(self)
        self.roleCombo.addItems(["tester", "root"])
        self.roleCombo.setCurrentIndex(0)
        self.viewLayout.addWidget(self.roleCombo)

        # 按钮
        self.yesButton.setText("创建")
        self.cancelButton.setText("取消")

        self.widget.setMinimumWidth(350)

    def validate(self) -> bool:
        """验证输入"""
        if not self.usernameEdit.text().strip():
            InfoBar.warning(
                title="提示",
                content="请输入用户名",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return False

        if not self.displayNameEdit.text().strip():
            InfoBar.warning(
                title="提示",
                content="请输入显示名称",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return False

        if len(self.passwordEdit.text()) < 6:
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

        return True

    def getData(self) -> dict:
        """获取表单数据"""
        return {
            'username': self.usernameEdit.text().strip(),
            'display_name': self.displayNameEdit.text().strip(),
            'password': self.passwordEdit.text(),
            'role': self.roleCombo.currentText()
        }


class ResetPasswordDialog(MessageBoxBase):
    """重置密码对话框"""

    def __init__(self, username: str, parent=None):
        super().__init__(parent)
        self.username = username

        # 标题
        self.titleLabel = SubtitleLabel(self)
        self.titleLabel.setText(f"重置密码 - {username}")
        self.viewLayout.addWidget(self.titleLabel)

        infoLabel = BodyLabel(self)
        infoLabel.setText("请输入新密码")
        self.viewLayout.addWidget(infoLabel)

        # 新密码
        self.passwordEdit = LineEdit(self)
        self.passwordEdit.setEchoMode(LineEdit.Password)
        self.passwordEdit.setPlaceholderText("新密码 (至少6位)")
        self.viewLayout.addWidget(self.passwordEdit)

        # 确认密码
        self.confirmEdit = LineEdit(self)
        self.confirmEdit.setEchoMode(LineEdit.Password)
        self.confirmEdit.setPlaceholderText("确认新密码")
        self.viewLayout.addWidget(self.confirmEdit)

        # 按钮
        self.yesButton.setText("确认重置")
        self.cancelButton.setText("取消")

    def validate(self) -> bool:
        """验证输入"""
        if len(self.passwordEdit.text()) < 6:
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

        if self.passwordEdit.text() != self.confirmEdit.text():
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

    def getNewPassword(self) -> str:
        """获取新密码"""
        return self.passwordEdit.text()
