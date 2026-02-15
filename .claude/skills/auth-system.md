# 账号与权限系统

此 SKILL 用于指导 VoidView 项目中账号系统的设计和实现。

## 权限模型

### 角色定义

| 角色 | 权限说明 |
|------|----------|
| `root` | 系统管理员，唯一可以创建/禁用账号的角色，可以查看和操作所有数据 |
| `tester` | 测试人员，可以参与主观评测和评审流程，只能查看分配给自己的任务 |

### 权限矩阵

| 操作 | root | tester |
|------|:----:|:------:|
| 登录系统 | ✅ | ✅ |
| 修改自己的密码 | ✅ | ✅ |
| 创建新账号 | ✅ | ❌ |
| 禁用/启用账号 | ✅ | ❌ |
| 重置他人密码 | ✅ | ❌ |
| 创建客户/应用/模板 | ✅ | ❌ |
| 创建实验 | ✅ | ✅ |
| 录入客观指标 | ✅ | ✅ |
| 进行主观评测 | ✅ | ✅ |
| 参与评审 | ✅ | ✅ |
| 查看所有数据 | ✅ | 仅相关 |
| 导出数据 | ✅ | 仅相关 |

## 账号初始化

### 系统初始化流程

```
┌─────────────────────────────────────────────────────────────┐
│                     系统首次启动                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 检查数据库是否存在                                       │
│     └── 不存在 → 创建数据库和表                              │
│                                                             │
│  2. 检查 root 账号是否存在                                   │
│     └── 不存在 → 创建默认 root 账号                          │
│         - 用户名: root                                      │
│         - 密码: root123 (首次登录必须修改)                   │
│         - 角色: root                                        │
│                                                             │
│  3. 显示登录界面                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 初始化代码

```python
# src/app/initializer.py
from data.database import SessionLocal, init_db
from core.models.user import User, UserRole, UserService


def initialize_system():
    """系统初始化"""
    # 1. 初始化数据库
    init_db()

    # 2. 初始化 root 账号
    db = SessionLocal()
    try:
        user_service = UserService(db)
        root = user_service.init_root_user()
        if root:
            print("已创建默认 root 账号，首次登录请使用: root / root123")
    finally:
        db.close()
```

## 登录流程

```
┌─────────────────────────────────────────────────────────────┐
│                       登录流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  用户输入用户名密码                                          │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────┐                                           │
│  │ 验证账号密码 │──失败──▶ 显示错误，清空密码                 │
│  └──────┬──────┘                                           │
│         │ 成功                                              │
│         ▼                                                   │
│  ┌─────────────────┐                                       │
│  │ 检查是否需要改密 │                                       │
│  └──────┬──────────┘                                       │
│         │                                                   │
│    ┌────┴────┐                                              │
│    │         │                                              │
│   需要      不需要                                           │
│    │         │                                              │
│    ▼         │                                              │
│  强制修改    │                                              │
│  密码界面    │                                              │
│    │         │                                              │
│    └────┬────┘                                              │
│         │                                                   │
│         ▼                                                   │
│  进入主界面                                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 用户管理界面 (root 专用)

```python
# src/ui/pages/user_management.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    TableWidget, PushButton, PrimaryPushButton, LineEdit,
    ComboBox, SubtitleLabel, MessageBox, InfoBar, SwitchButton
)
from core.models.user import User, UserRole, UserService


class UserManagementPage(QWidget):
    """用户管理页面 - 仅 root 可访问"""

    def __init__(self, current_user: User, db, parent=None):
        super().__init__(parent)
        if not current_user.is_root():
            raise PermissionError("此页面仅管理员可访问")

        self.current_user = current_user
        self.db = db
        self.user_service = UserService(db)
        self.setupUI()
        self.loadUsers()

    def setupUI(self):
        layout = QVBoxLayout(self)

        # 标题和操作按钮
        headerLayout = QHBoxLayout()
        title = SubtitleLabel("用户管理", self)
        headerLayout.addWidget(title)
        headerLayout.addStretch()

        self.createBtn = PrimaryPushButton("创建新账号", self)
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
        layout.addWidget(self.table)

    def loadUsers(self):
        users = self.db.query(User).all()
        self.table.setRowCount(len(users))

        for row, user in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(user.username))
            self.table.setItem(row, 1, QTableWidgetItem(user.display_name))
            self.table.setItem(row, 2, QTableWidgetItem(user.role.value))

            # 状态开关
            statusWidget = QWidget()
            statusLayout = QHBoxLayout(statusWidget)
            statusLayout.setContentsMargins(4, 4, 4, 4)
            switch = SwitchButton()
            switch.setChecked(user.is_active)
            switch.checkedChanged.connect(
                lambda checked, u=user: self.toggleUserStatus(u, checked)
            )
            # root 账号不能禁用自己
            if user.id == self.current_user.id:
                switch.setEnabled(False)
            statusLayout.addWidget(switch)
            self.table.setCellWidget(row, 3, statusWidget)

            # 最后登录时间
            last_login = user.last_login_at.strftime("%Y-%m-%d %H:%M") if user.last_login_at else "从未"
            self.table.setItem(row, 4, QTableWidgetItem(last_login))

            # 操作按钮
            actionWidget = QWidget()
            actionLayout = QHBoxLayout(actionWidget)
            actionLayout.setContentsMargins(4, 4, 4, 4)

            resetBtn = PushButton("重置密码", actionWidget)
            resetBtn.clicked.connect(lambda checked, u=user: self.resetPassword(u))
            actionLayout.addWidget(resetBtn)

            self.table.setCellWidget(row, 5, actionWidget)

    def showCreateDialog(self):
        """显示创建用户对话框"""
        dialog = CreateUserDialog(self)
        if dialog.exec():
            data = dialog.getData()
            self.user_service.create_user(
                username=data['username'],
                password=data['password'],
                display_name=data['display_name'],
                created_by=self.current_user.id,
                role=UserRole(data['role'])
            )
            InfoBar.success("成功", f"账号 {data['username']} 创建成功", self)
            self.loadUsers()

    def toggleUserStatus(self, user: User, active: bool):
        """切换用户状态"""
        if user.id == self.current_user.id:
            InfoBar.warning("提示", "不能禁用自己的账号", self)
            return

        user.is_active = active
        self.db.commit()
        status = "启用" if active else "禁用"
        InfoBar.success("成功", f"已{status}账号 {user.username}", self)

    def resetPassword(self, user: User):
        """重置用户密码"""
        box = MessageBox(
            "确认重置",
            f"确定要重置 {user.username} 的密码吗？\n密码将被重置为: 123456",
            self
        )
        if box.exec():
            user.set_password("123456")
            user.must_change_password = True
            self.db.commit()
            InfoBar.success("成功", f"密码已重置为 123456", self)


class CreateUserDialog(MessageBox):
    """创建用户对话框"""

    def __init__(self, parent=None):
        super().__init__("创建新账号", "", parent)

        self.usernameEdit = LineEdit(self)
        self.usernameEdit.setPlaceholderText("登录用户名")

        self.displayNameEdit = LineEdit(self)
        self.displayNameEdit.setPlaceholderText("显示名称")

        self.passwordEdit = LineEdit(self)
        self.passwordEdit.setEchoMode(LineEdit.Password)
        self.passwordEdit.setPlaceholderText("初始密码")

        self.roleCombo = ComboBox(self)
        self.roleCombo.addItems(["tester", "root"])

        self.viewLayout.addWidget(QLabel("用户名:"))
        self.viewLayout.addWidget(self.usernameEdit)
        self.viewLayout.addWidget(QLabel("显示名称:"))
        self.viewLayout.addWidget(self.displayNameEdit)
        self.viewLayout.addWidget(QLabel("初始密码:"))
        self.viewLayout.addWidget(self.passwordEdit)
        self.viewLayout.addWidget(QLabel("角色:"))
        self.viewLayout.addWidget(self.roleCombo)

        self.yesButton.setText("创建")
        self.cancelButton.setText("取消")

    def validate(self) -> bool:
        if not self.usernameEdit.text().strip():
            InfoBar.error("错误", "请输入用户名", self)
            return False
        if not self.passwordEdit.text():
            InfoBar.error("错误", "请输入初始密码", self)
            return False
        if len(self.passwordEdit.text()) < 6:
            InfoBar.error("错误", "密码长度不能少于6位", self)
            return False
        return True

    def getData(self) -> dict:
        return {
            'username': self.usernameEdit.text().strip(),
            'display_name': self.displayNameEdit.text().strip() or self.usernameEdit.text().strip(),
            'password': self.passwordEdit.text(),
            'role': self.roleCombo.currentText()
        }
```

## 导航菜单权限控制

```python
# src/ui/main_window.py
from qfluentwidgets import FluentWindow, NavigationItemPosition
from app.app_state import app_state


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setupNavigation()

    def setupNavigation(self):
        # 所有用户可见的页面
        self.experimentPage = ExperimentPage()
        self.evaluationPage = EvaluationPage()
        self.reviewPage = ReviewPage()
        self.statisticsPage = StatisticsPage()

        # 仅 root 可见的页面
        self.userManagementPage = None
        if app_state.is_root():
            self.userManagementPage = UserManagementPage(
                current_user=app_state.current_user,
                db=SessionLocal()
            )

        # 添加导航项
        self.addNavigationItem("实验管理", FluentIcon.DOCUMENT, self.experimentPage)
        self.addNavigationItem("评测", FluentIcon.VIDEO, self.evaluationPage)
        self.addNavigationItem("评审", FluentIcon.CHECKBOX, self.reviewPage)
        self.addNavigationItem("统计", FluentIcon.CHART, self.statisticsPage)

        # 用户管理 - 仅 root 可见，放在底部
        if self.userManagementPage:
            self.navigationInterface.addItem(
                routeKey='users',
                label='用户管理',
                icon=FluentIcon.PEOPLE,
                onClick=lambda: self.switchTo(self.userManagementPage),
                position=NavigationItemPosition.BOTTOM
            )

        # 当前用户信息显示
        self.navigationInterface.addItem(
            routeKey='user_info',
            label=app_state.current_user.display_name,
            icon=FluentIcon.PEOPLE,
            position=NavigationItemPosition.BOTTOM
        )

        # 退出登录
        self.navigationInterface.addItem(
            routeKey='logout',
            label='退出登录',
            icon=FluentIcon.EXIT,
            onClick=self.logout,
            position=NavigationItemPosition.BOTTOM
        )
```

## 安全注意事项

1. **密码存储**: 使用 bcrypt 哈希，不要明文存储
2. **默认密码**: root 默认密码必须在首次登录时修改
3. **会话管理**: 每次操作验证用户状态 (is_active)
4. **操作日志**: 记录敏感操作的执行人 (created_by, reviewer 等)
5. **root 保护**: root 账号不能被禁用或删除
