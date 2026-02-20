"""添加客户/APP/模板对话框"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout
from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, BodyLabel, LineEdit,
    ComboBox, PushButton, InfoBar
)

from api import customer_api, app_api, template_api, APIError
from models.experiment import CustomerCreateRequest, AppCreateRequest, TemplateCreateRequest


class AddEntityDialog(MessageBoxBase):
    """添加客户/APP/模板对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._customers = []
        self._apps = []
        self._loading = False  # 防止加载时触发信号

        # 标题
        self.titleLabel = SubtitleLabel(self)
        self.titleLabel.setText("添加客户 / 应用 / 模板")
        self.viewLayout.addWidget(self.titleLabel)

        # ====== 客户区域 ======
        self.customerSectionLabel = BodyLabel(self)
        self.customerSectionLabel.setText("【客户】")
        self.customerSectionLabel.setStyleSheet("font-weight: bold; color: #0078d4;")
        self.viewLayout.addWidget(self.customerSectionLabel)

        customerLayout = QHBoxLayout()
        self.customerCombo = ComboBox(self)
        self.customerCombo.setPlaceholderText("选择客户")
        self.customerCombo.setFixedWidth(200)
        self.customerCombo.currentIndexChanged.connect(self._onCustomerSelected)
        customerLayout.addWidget(self.customerCombo)

        self.customerNameEdit = LineEdit(self)
        self.customerNameEdit.setPlaceholderText("新客户名称")
        self.customerNameEdit.setFixedWidth(150)
        customerLayout.addWidget(self.customerNameEdit)

        self.createCustomerBtn = PushButton(self)
        self.createCustomerBtn.setText("创建")
        self.createCustomerBtn.clicked.connect(self._createCustomer)
        customerLayout.addWidget(self.createCustomerBtn)

        customerWidget = QWidget()
        customerWidget.setLayout(customerLayout)
        self.viewLayout.addWidget(customerWidget)

        # ====== 应用区域 ======
        self.appSectionLabel = BodyLabel(self)
        self.appSectionLabel.setText("【应用】(需先选择客户)")
        self.appSectionLabel.setStyleSheet("font-weight: bold; color: #0078d4;")
        self.viewLayout.addWidget(self.appSectionLabel)

        appLayout = QHBoxLayout()
        self.appCombo = ComboBox(self)
        self.appCombo.setPlaceholderText("选择应用")
        self.appCombo.setFixedWidth(200)
        self.appCombo.currentIndexChanged.connect(self._onAppSelected)
        appLayout.addWidget(self.appCombo)

        self.appNameEdit = LineEdit(self)
        self.appNameEdit.setPlaceholderText("新应用名称")
        self.appNameEdit.setFixedWidth(150)
        appLayout.addWidget(self.appNameEdit)

        self.createAppBtn = PushButton(self)
        self.createAppBtn.setText("创建")
        self.createAppBtn.clicked.connect(self._createApp)
        appLayout.addWidget(self.createAppBtn)

        appWidget = QWidget()
        appWidget.setLayout(appLayout)
        self.viewLayout.addWidget(appWidget)

        # ====== 模板区域 ======
        self.templateSectionLabel = BodyLabel(self)
        self.templateSectionLabel.setText("【模板】(需先选择应用)")
        self.templateSectionLabel.setStyleSheet("font-weight: bold; color: #0078d4;")
        self.viewLayout.addWidget(self.templateSectionLabel)

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
        self.createTemplateBtn.setText("创建")
        self.createTemplateBtn.clicked.connect(self._createTemplate)
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
        self._loading = True
        try:
            self._customers = customer_api.list()
            self.customerCombo.clear()
            self.customerCombo.addItem("请选择客户")
            for c in self._customers:
                self.customerCombo.addItem(c.name)
            self.customerCombo.setCurrentIndex(0)
            self._loadApps([])
        except APIError as e:
            InfoBar.error(
                title="加载失败",
                content=e.message,
                parent=self
            )
        finally:
            self._loading = False

    def _loadApps(self, apps):
        """加载应用列表"""
        self._loading = True
        try:
            self._apps = apps
            self.appCombo.clear()
            self.appCombo.addItem("请选择应用")
            for a in apps:
                self.appCombo.addItem(a.name)
            self.appCombo.setCurrentIndex(0)
            self._loadTemplates([])
        finally:
            self._loading = False

    def _loadTemplates(self, templates):
        """加载模板列表"""
        self._loading = True
        try:
            self.templateCombo.clear()
            self.templateCombo.addItem("请选择模板")
            for t in templates:
                self.templateCombo.addItem(t.name)
            self.templateCombo.setCurrentIndex(0)
        finally:
            self._loading = False

    def _onCustomerSelected(self, index):
        """选择客户"""
        if self._loading:
            return
        # index 0 是占位符
        if index > 0 and index <= len(self._customers):
            customer_id = self._customers[index - 1].id
            try:
                apps = app_api.list(customer_id=customer_id)
                self._loadApps(apps)
            except APIError:
                self._loadApps([])
        else:
            self._loadApps([])

    def _onAppSelected(self, index):
        """选择应用"""
        if self._loading:
            return
        # index 0 是占位符
        if index > 0 and index <= len(self._apps):
            app_id = self._apps[index - 1].id
            try:
                templates = template_api.list(app_id=app_id)
                self._loadTemplates(templates)
            except APIError:
                self._loadTemplates([])
        else:
            self._loadTemplates([])

    def _createCustomer(self):
        """创建客户"""
        name = self.customerNameEdit.text().strip()
        if not name:
            InfoBar.warning(title="提示", content="请输入客户名称", parent=self)
            return

        try:
            customer_api.create(CustomerCreateRequest(name=name))
            InfoBar.success(title="成功", content=f"客户 '{name}' 创建成功", parent=self)
            self.customerNameEdit.clear()
            self._loadCustomers()
        except APIError as e:
            InfoBar.error(title="创建失败", content=e.message, parent=self)

    def _createApp(self):
        """创建应用"""
        customer_idx = self.customerCombo.currentIndex()
        if customer_idx <= 0 or customer_idx > len(self._customers):
            InfoBar.warning(title="提示", content="请先选择客户", parent=self)
            return

        name = self.appNameEdit.text().strip()
        if not name:
            InfoBar.warning(title="提示", content="请输入应用名称", parent=self)
            return

        try:
            customer_id = self._customers[customer_idx - 1].id
            app_api.create(AppCreateRequest(customer_id=customer_id, name=name))
            InfoBar.success(title="成功", content=f"应用 '{name}' 创建成功", parent=self)
            self.appNameEdit.clear()
            apps = app_api.list(customer_id=customer_id)
            self._loadApps(apps)
        except APIError as e:
            InfoBar.error(title="创建失败", content=e.message, parent=self)

    def _createTemplate(self):
        """创建模板"""
        app_idx = self.appCombo.currentIndex()
        if app_idx <= 0 or app_idx > len(self._apps):
            InfoBar.warning(title="提示", content="请先选择应用", parent=self)
            return

        name = self.templateNameEdit.text().strip()
        if not name:
            InfoBar.warning(title="提示", content="请输入模板名称", parent=self)
            return

        try:
            app_id = self._apps[app_idx - 1].id
            template_api.create(TemplateCreateRequest(app_id=app_id, name=name))
            InfoBar.success(title="成功", content=f"模板 '{name}' 创建成功", parent=self)
            self.templateNameEdit.clear()
            templates = template_api.list(app_id=app_id)
            self._loadTemplates(templates)
        except APIError as e:
            InfoBar.error(title="创建失败", content=e.message, parent=self)

    def validate(self) -> bool:
        """验证 - 直接关闭"""
        return True
