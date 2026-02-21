"""实验列表页面"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem, QLabel
from qfluentwidgets import (
    SubtitleLabel, TableWidget, PrimaryPushButton, PushButton,
    LineEdit, ComboBox, InfoBar, InfoBarPosition, MessageBoxBase,
    BodyLabel
)

from api import experiment_api, customer_api, app_api, template_api, APIError
from voidview_shared import ExperimentStatus
from models import ExperimentResponse


class ExperimentListPage(QWidget):
    """实验列表页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._page = 1
        self._pageSize = 20
        self._total = 0
        self._experiments = []
        self._customers = []
        self._apps = []
        self._templates = []
        self.setupUI()
        self.loadInitialData()

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题栏
        headerLayout = QHBoxLayout()
        title = SubtitleLabel(self)
        title.setText("实验管理")
        headerLayout.addWidget(title)
        headerLayout.addStretch()

        self.createBtn = PrimaryPushButton(self)
        self.createBtn.setText("创建实验")
        self.createBtn.clicked.connect(self.showCreateDialog)
        headerLayout.addWidget(self.createBtn)

        # 客户管理按钮
        self.customerBtn = PushButton(self)
        self.customerBtn.setText("客户管理")
        self.customerBtn.clicked.connect(self.showCustomerDialog)
        headerLayout.addWidget(self.customerBtn)

        layout.addLayout(headerLayout)

        # 筛选栏
        filterLayout = QHBoxLayout()

        # 客户筛选
        customerLabel = BodyLabel(self)
        customerLabel.setText("客户:")
        filterLayout.addWidget(customerLabel)

        self.customerCombo = ComboBox(self)
        self.customerCombo.setPlaceholderText("全部客户")
        self.customerCombo.setFixedWidth(150)
        self.customerCombo.currentIndexChanged.connect(self.onCustomerChanged)
        filterLayout.addWidget(self.customerCombo)

        filterLayout.addSpacing(16)

        # 应用筛选
        appLabel = BodyLabel(self)
        appLabel.setText("应用:")
        filterLayout.addWidget(appLabel)

        self.appCombo = ComboBox(self)
        self.appCombo.setPlaceholderText("全部应用")
        self.appCombo.setFixedWidth(150)
        self.appCombo.currentIndexChanged.connect(self.onAppChanged)
        filterLayout.addWidget(self.appCombo)

        filterLayout.addSpacing(16)

        # 模板筛选
        templateLabel = BodyLabel(self)
        templateLabel.setText("模板:")
        filterLayout.addWidget(templateLabel)

        self.templateCombo = ComboBox(self)
        self.templateCombo.setPlaceholderText("全部模板")
        self.templateCombo.setFixedWidth(150)
        self.templateCombo.currentIndexChanged.connect(self.onFilterChanged)
        filterLayout.addWidget(self.templateCombo)

        filterLayout.addSpacing(16)

        # 状态筛选
        statusLabel = BodyLabel(self)
        statusLabel.setText("状态:")
        filterLayout.addWidget(statusLabel)

        self.statusCombo = ComboBox(self)
        self.statusCombo.addItems(["全部状态", "草稿", "进行中", "已完成", "已归档"])
        self.statusCombo.setCurrentIndex(0)
        self.statusCombo.setFixedWidth(120)
        self.statusCombo.currentIndexChanged.connect(self.onFilterChanged)
        filterLayout.addWidget(self.statusCombo)

        filterLayout.addStretch()

        # 刷新按钮
        self.refreshBtn = PushButton(self)
        self.refreshBtn.setText("刷新")
        self.refreshBtn.clicked.connect(self.loadExperiments)
        filterLayout.addWidget(self.refreshBtn)

        layout.addLayout(filterLayout)

        # 实验表格
        self.table = TableWidget(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "实验名称", "模板", "状态", "参考类型", "创建时间", "操作"
        ])
        self.table.verticalHeader().hide()
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)
        self.table.horizontalHeader().setStretchLastSection(True)

        # 设置列宽
        self.table.setColumnWidth(0, 250)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 150)

        layout.addWidget(self.table)

        # 分页信息
        self.pageInfoLabel = BodyLabel(self)
        self.pageInfoLabel.setText("共 0 条记录")
        layout.addWidget(self.pageInfoLabel)

    def loadInitialData(self):
        """加载初始数据"""
        try:
            # 加载客户列表
            self._customers = customer_api.list()
            self.customerCombo.clear()
            self.customerCombo.addItem("全部客户")
            for c in self._customers:
                self.customerCombo.addItem(c.name)

            # 加载实验列表
            self.loadExperiments()
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

    def loadExperiments(self):
        """加载实验列表"""
        try:
            # 获取筛选条件
            template_id = self._getSelectedTemplateId()
            status = self._getSelectedStatus()

            result = experiment_api.list(
                page=self._page,
                page_size=self._pageSize,
                template_id=template_id,
                status=status
            )

            self._experiments = result.items
            self._total = result.total

            # 更新表格
            self.table.setRowCount(len(self._experiments))

            for row, exp in enumerate(self._experiments):
                # 实验名称
                self.table.setItem(row, 0, QTableWidgetItem(exp.name))

                # 模板 (需要从 template_id 获取，暂时显示 ID)
                self.table.setItem(row, 1, QTableWidgetItem(f"模板#{exp.template_id}"))

                # 状态
                statusText = self._getStatusText(exp.status)
                self.table.setItem(row, 2, QTableWidgetItem(statusText))

                # 参考类型
                refText = self._getReferenceText(exp.reference_type)
                self.table.setItem(row, 3, QTableWidgetItem(refText))

                # 创建时间
                createdAt = exp.created_at.strftime("%Y-%m-%d %H:%M") if exp.created_at else ""
                self.table.setItem(row, 4, QTableWidgetItem(createdAt))

                # 操作按钮
                actionWidget = QWidget()
                actionLayout = QHBoxLayout(actionWidget)
                actionLayout.setContentsMargins(0, 0, 0, 0)

                detailBtn = PushButton(actionWidget)
                detailBtn.setText("详情")
                detailBtn.clicked.connect(lambda checked, eid=exp.id: self.showDetail(eid))
                actionLayout.addWidget(detailBtn)

                deleteBtn = PushButton(actionWidget)
                deleteBtn.setText("删除")
                deleteBtn.clicked.connect(lambda checked, eid=exp.id: self.deleteExperiment(eid))
                actionLayout.addWidget(deleteBtn)

                self.table.setCellWidget(row, 5, actionWidget)

            # 更新分页信息
            self.pageInfoLabel.setText(f"共 {self._total} 条记录")

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

    def _getSelectedTemplateId(self) -> int:
        """获取选中的模板ID"""
        idx = self.templateCombo.currentIndex()
        if idx > 0 and idx <= len(self._templates):
            return self._templates[idx - 1].id
        return None

    def _getSelectedStatus(self) -> str:
        """获取选中的状态"""
        idx = self.statusCombo.currentIndex()
        statuses = [None, "draft", "running", "completed", "archived"]
        if idx < len(statuses):
            return statuses[idx]
        return None

    def _getStatusText(self, status) -> str:
        """获取状态文本"""
        statusMap = {
            ExperimentStatus.DRAFT: "草稿",
            ExperimentStatus.RUNNING: "进行中",
            ExperimentStatus.COMPLETED: "已完成",
            ExperimentStatus.ARCHIVED: "已归档",
        }
        return statusMap.get(status, str(status))

    def _getReferenceText(self, refType) -> str:
        """获取参考类型文本"""
        refMap = {
            "supplier": "供应商对齐",
            "self": "自对齐",
            "new": "全新模板",
        }
        return refMap.get(str(refType.value) if hasattr(refType, 'value') else str(refType), str(refType))

    def onCustomerChanged(self, index):
        """客户选择改变"""
        if index > 0 and index <= len(self._customers):
            customer_id = self._customers[index - 1].id
            try:
                self._apps = app_api.list(customer_id=customer_id)
                self.appCombo.clear()
                self.appCombo.addItem("全部应用")
                for a in self._apps:
                    self.appCombo.addItem(a.name)
            except APIError:
                pass
        else:
            self.appCombo.clear()
            self.appCombo.addItem("全部应用")
            self._apps = []

        self.onAppChanged(0)

    def onAppChanged(self, index):
        """应用选择改变"""
        if index > 0 and index <= len(self._apps):
            app_id = self._apps[index - 1].id
            try:
                self._templates = template_api.list(app_id=app_id)
                self.templateCombo.clear()
                self.templateCombo.addItem("全部模板")
                for t in self._templates:
                    self.templateCombo.addItem(t.name)
            except APIError:
                pass
        else:
            self.templateCombo.clear()
            self.templateCombo.addItem("全部模板")
            self._templates = []

        self.onFilterChanged(0)

    def onFilterChanged(self, index):
        """筛选条件改变"""
        self._page = 1
        self.loadExperiments()

    def onPageChanged(self, page):
        """页码改变"""
        self._page = page
        self.loadExperiments()

    def showDetail(self, experiment_id: int):
        """显示实验详情"""
        InfoBar.info(
            title="提示",
            content=f"实验详情功能开发中... (ID: {experiment_id})",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

    def deleteExperiment(self, experiment_id: int):
        """删除实验"""
        from qfluentwidgets import MessageBox

        box = MessageBox("确认删除", "确定要删除该实验吗？此操作不可恢复。", self)
        if box.exec():
            try:
                experiment_api.delete(experiment_id)
                InfoBar.success(
                    title="成功",
                    content="实验已删除",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                self.loadExperiments()
            except APIError as e:
                InfoBar.error(
                    title="删除失败",
                    content=e.message,
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )

    def showCreateDialog(self):
        """显示创建实验对话框"""
        dialog = CreateExperimentDialog(self._templates, self)
        if dialog.exec():
            data = dialog.getData()
            try:
                experiment_api.create(data)
                InfoBar.success(
                    title="成功",
                    content=f"实验 '{data.name}' 创建成功",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                self.loadExperiments()
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

    def showCustomerDialog(self):
        """显示客户管理对话框"""
        dialog = CustomerManageDialog(self)
        dialog.exec()
        # 刷新客户列表和模板列表
        self.loadInitialData()


class CreateExperimentDialog(MessageBoxBase):
    """创建实验对话框"""

    def __init__(self, templates, parent=None):
        super().__init__(parent)
        self._templates = templates or []

        # 标题
        self.titleLabel = SubtitleLabel(self)
        self.titleLabel.setText("创建新实验")
        self.viewLayout.addWidget(self.titleLabel)

        # 实验名称
        self.nameLabel = BodyLabel(self)
        self.nameLabel.setText("实验名称")
        self.viewLayout.addWidget(self.nameLabel)

        self.nameEdit = LineEdit(self)
        self.nameEdit.setPlaceholderText("例如: xx客户third_app实验")
        self.viewLayout.addWidget(self.nameEdit)

        # 模板选择
        self.templateLabel = BodyLabel(self)
        self.templateLabel.setText("转码模板")
        self.viewLayout.addWidget(self.templateLabel)

        self.templateCombo = ComboBox(self)
        if self._templates:
            for t in self._templates:
                self.templateCombo.addItem(f"{t.name} (ID: {t.id})")
        else:
            self.templateCombo.setPlaceholderText("请先创建模板")
        self.viewLayout.addWidget(self.templateCombo)

        # 参考类型
        self.refLabel = BodyLabel(self)
        self.refLabel.setText("参考类型")
        self.viewLayout.addWidget(self.refLabel)

        self.refCombo = ComboBox(self)
        self.refCombo.addItems(["全新模板", "供应商对齐", "自对齐"])
        self.refCombo.setCurrentIndex(0)
        self.viewLayout.addWidget(self.refCombo)

        # 按钮
        self.yesButton.setText("创建")
        self.cancelButton.setText("取消")

        self.widget.setMinimumWidth(400)

    def validate(self) -> bool:
        """验证输入"""
        if not self.nameEdit.text().strip():
            InfoBar.warning(
                title="提示",
                content="请输入实验名称",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return False

        if not self._templates:
            InfoBar.warning(
                title="提示",
                content="请先在客户管理中创建模板",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return False

        return True

    def getData(self):
        """获取表单数据"""
        from models import ExperimentCreateRequest
        from voidview_shared import ReferenceType

        refMap = {
            0: ReferenceType.NEW,
            1: ReferenceType.SUPPLIER,
            2: ReferenceType.SELF,
        }

        template_idx = self.templateCombo.currentIndex()
        template_id = self._templates[template_idx].id if template_idx < len(self._templates) else None

        return ExperimentCreateRequest(
            template_id=template_id,
            name=self.nameEdit.text().strip(),
            reference_type=refMap[self.refCombo.currentIndex()]
        )


class CustomerManageDialog(MessageBoxBase):
    """客户管理对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._customers = []
        self._apps = []
        self._templates = []
        self._parent = parent

        # 标题
        self.titleLabel = SubtitleLabel(self)
        self.titleLabel.setText("客户 / 应用 / 模板管理")
        self.viewLayout.addWidget(self.titleLabel)

        # ====== 客户区域 ======
        self.customerSectionLabel = BodyLabel(self)
        self.customerSectionLabel.setText("【客户】")
        self.customerSectionLabel.setStyleSheet("font-weight: bold; color: #0078d4;")
        self.viewLayout.addWidget(self.customerSectionLabel)

        # 客户选择和创建
        customerLayout = QHBoxLayout()
        self.customerCombo = ComboBox(self)
        self.customerCombo.setPlaceholderText("选择客户")
        self.customerCombo.setFixedWidth(200)
        self.customerCombo.currentIndexChanged.connect(self.onCustomerSelected)
        customerLayout.addWidget(self.customerCombo)

        self.customerNameEdit = LineEdit(self)
        self.customerNameEdit.setPlaceholderText("新客户名称")
        self.customerNameEdit.setFixedWidth(150)
        customerLayout.addWidget(self.customerNameEdit)

        self.createCustomerBtn = PushButton(self)
        self.createCustomerBtn.setText("创建客户")
        self.createCustomerBtn.clicked.connect(self.createCustomer)
        customerLayout.addWidget(self.createCustomerBtn)

        customerWidget = QWidget()
        customerWidget.setLayout(customerLayout)
        self.viewLayout.addWidget(customerWidget)

        # ====== 应用区域 ======
        self.appSectionLabel = BodyLabel(self)
        self.appSectionLabel.setText("【应用】(需先选择客户)")
        self.appSectionLabel.setStyleSheet("font-weight: bold; color: #0078d4;")
        self.viewLayout.addWidget(self.appSectionLabel)

        # 应用选择和创建
        appLayout = QHBoxLayout()
        self.appCombo = ComboBox(self)
        self.appCombo.setPlaceholderText("选择应用")
        self.appCombo.setFixedWidth(200)
        self.appCombo.currentIndexChanged.connect(self.onAppSelected)
        appLayout.addWidget(self.appCombo)

        self.appNameEdit = LineEdit(self)
        self.appNameEdit.setPlaceholderText("新应用名称")
        self.appNameEdit.setFixedWidth(150)
        appLayout.addWidget(self.appNameEdit)

        self.createAppBtn = PushButton(self)
        self.createAppBtn.setText("创建应用")
        self.createAppBtn.clicked.connect(self.createApp)
        appLayout.addWidget(self.createAppBtn)

        appWidget = QWidget()
        appWidget.setLayout(appLayout)
        self.viewLayout.addWidget(appWidget)

        # ====== 模板区域 ======
        self.templateSectionLabel = BodyLabel(self)
        self.templateSectionLabel.setText("【模板】(需先选择应用)")
        self.templateSectionLabel.setStyleSheet("font-weight: bold; color: #0078d4;")
        self.viewLayout.addWidget(self.templateSectionLabel)

        # 模板选择和创建
        templateLayout = QHBoxLayout()
        self.templateCombo = ComboBox(self)
        self.templateCombo.setPlaceholderText("选择模板")
        self.templateCombo.setFixedWidth(200)
        templateLayout.addWidget(self.templateCombo)

        self.templateNameEdit = LineEdit(self)
        self.templateNameEdit.setPlaceholderText("新模板名称(如 hd5)")
        self.templateNameEdit.setFixedWidth(150)
        templateLayout.addWidget(self.templateNameEdit)

        self.createTemplateBtn = PushButton(self)
        self.createTemplateBtn.setText("创建模板")
        self.createTemplateBtn.clicked.connect(self.createTemplate)
        templateLayout.addWidget(self.createTemplateBtn)

        templateWidget = QWidget()
        templateWidget.setLayout(templateLayout)
        self.viewLayout.addWidget(templateWidget)

        # 按钮
        self.yesButton.setText("完成")
        self.cancelButton.hide()

        self.widget.setMinimumWidth(500)

        # 加载数据
        self._loadCustomers()

    def _loadCustomers(self):
        """加载客户列表"""
        try:
            self._customers = customer_api.list()
            self.customerCombo.clear()
            self.customerCombo.setPlaceholderText("选择客户")
            for c in self._customers:
                self.customerCombo.addItem(c.name)
            self._loadApps([])
            self._loadTemplates([])
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

    def _loadApps(self, apps):
        """加载应用列表"""
        self._apps = apps
        self.appCombo.clear()
        self.appCombo.setPlaceholderText("选择应用")
        for a in apps:
            self.appCombo.addItem(a.name)
        self._loadTemplates([])

    def _loadTemplates(self, templates):
        """加载模板列表"""
        self._templates = templates
        self.templateCombo.clear()
        self.templateCombo.setPlaceholderText("选择模板")
        for t in templates:
            self.templateCombo.addItem(t.name)

    def onCustomerSelected(self, index):
        """选择客户"""
        if index >= 0 and index < len(self._customers):
            customer_id = self._customers[index].id
            try:
                apps = app_api.list(customer_id=customer_id)
                self._loadApps(apps)
            except APIError:
                self._loadApps([])
        else:
            self._loadApps([])

    def onAppSelected(self, index):
        """选择应用"""
        if index >= 0 and index < len(self._apps):
            app_id = self._apps[index].id
            try:
                templates = template_api.list(app_id=app_id)
                self._loadTemplates(templates)
            except APIError:
                self._loadTemplates([])
        else:
            self._loadTemplates([])

    def createCustomer(self):
        """创建客户"""
        name = self.customerNameEdit.text().strip()
        if not name:
            InfoBar.warning(
                title="提示",
                content="请输入客户名称",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        try:
            from models import CustomerCreateRequest
            customer_api.create(CustomerCreateRequest(name=name))
            InfoBar.success(
                title="成功",
                content=f"客户 '{name}' 创建成功",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            self.customerNameEdit.clear()
            self._loadCustomers()
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

    def createApp(self):
        """创建应用"""
        if not self._customers:
            InfoBar.warning(
                title="提示",
                content="请先选择客户",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        customer_idx = self.customerCombo.currentIndex()
        if customer_idx < 0 or customer_idx >= len(self._customers):
            InfoBar.warning(
                title="提示",
                content="请先选择客户",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        name = self.appNameEdit.text().strip()
        if not name:
            InfoBar.warning(
                title="提示",
                content="请输入应用名称",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        try:
            from models import AppCreateRequest
            customer_id = self._customers[customer_idx].id
            app_api.create(AppCreateRequest(customer_id=customer_id, name=name))
            InfoBar.success(
                title="成功",
                content=f"应用 '{name}' 创建成功",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            self.appNameEdit.clear()
            # 刷新应用列表
            apps = app_api.list(customer_id=customer_id)
            self._loadApps(apps)
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

    def createTemplate(self):
        """创建模板"""
        if not self._apps:
            InfoBar.warning(
                title="提示",
                content="请先选择应用",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        app_idx = self.appCombo.currentIndex()
        if app_idx < 0 or app_idx >= len(self._apps):
            InfoBar.warning(
                title="提示",
                content="请先选择应用",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        name = self.templateNameEdit.text().strip()
        if not name:
            InfoBar.warning(
                title="提示",
                content="请输入模板名称",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        try:
            from models import TemplateCreateRequest
            app_id = self._apps[app_idx].id
            template_api.create(TemplateCreateRequest(app_id=app_id, name=name))
            InfoBar.success(
                title="成功",
                content=f"模板 '{name}' 创建成功",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            self.templateNameEdit.clear()
            # 刷新模板列表
            templates = template_api.list(app_id=app_id)
            self._loadTemplates(templates)
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

    def validate(self) -> bool:
        """验证 - 直接关闭"""
        return True
