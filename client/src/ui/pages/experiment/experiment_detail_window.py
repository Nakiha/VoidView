"""实验详情独立窗口"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QSplitter
from qfluentwidgets import (
    FluentWindow, BodyLabel, SubtitleLabel,
    CardWidget, SmoothScrollArea, FluentIcon, IconWidget,
    PrimaryPushButton, InfoBar, MessageBoxBase, ComboBox
)

from api import experiment_api, template_api, customer_api, app_api, APIError
from models.experiment import ExperimentResponse, ExperimentTemplateLinkRequest
from .template_detail_panel import TemplateDetailPanel


class TemplateCard(CardWidget):
    """模板卡片"""

    cardClicked = Signal(int)  # template_index

    def __init__(self, template_name: str, index: int, accent_color: str = "#0078D4", parent=None):
        super().__init__(parent)
        self._template_name = template_name
        self._index = index
        self._accent_color = accent_color
        self._selected = False
        self.setupUI()
        # 连接 CardWidget 内置的 clicked 信号
        self.clicked.connect(lambda: self.cardClicked.emit(self._index))

    def setupUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 左侧选中指示条（Fluent Design accent indicator）
        self.indicator = QFrame(self)
        self.indicator.setFixedWidth(3)
        self.indicator.setStyleSheet("background-color: transparent;")
        layout.addWidget(self.indicator)

        # 内容区域
        contentWidget = QWidget(self)
        contentLayout = QVBoxLayout(contentWidget)
        contentLayout.setContentsMargins(12, 10, 12, 10)
        contentLayout.setSpacing(4)

        # 模板名称
        nameLabel = BodyLabel(contentWidget)
        nameLabel.setText(self._template_name)
        nameLabel.setWordWrap(True)
        contentLayout.addWidget(nameLabel)

        layout.addWidget(contentWidget, 1)

        # 设置点击样式
        self.setCursor(Qt.PointingHandCursor)

    def setSelected(self, selected: bool):
        """设置选中状态 - Fluent Design 左侧指示条"""
        self._selected = selected
        if selected:
            # 左侧显示实验装饰色指示条
            self.indicator.setStyleSheet(f"background-color: {self._accent_color};")
        else:
            self.indicator.setStyleSheet("background-color: transparent;")


class AddTemplateCard(CardWidget):
    """添加模板卡片"""

    addClicked = Signal()  # 点击添加按钮

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        # 连接 CardWidget 内置的 clicked 信号
        self.clicked.connect(self.addClicked.emit)

    def setupUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 左侧占位（与 TemplateCard 的 indicator 对齐）
        spacer = QFrame(self)
        spacer.setFixedWidth(3)
        spacer.setStyleSheet("background-color: transparent;")
        layout.addWidget(spacer)

        # 内容区域
        contentWidget = QWidget(self)
        contentLayout = QHBoxLayout(contentWidget)
        contentLayout.setContentsMargins(12, 10, 12, 10)
        contentLayout.setSpacing(8)

        # 加号图标
        self.addIcon = IconWidget(FluentIcon.ADD, contentWidget)
        self.addIcon.setFixedSize(20, 20)
        contentLayout.addWidget(self.addIcon)

        # 提示文字
        hintLabel = BodyLabel(contentWidget)
        hintLabel.setText("添加模板")
        hintLabel.setStyleSheet("color: rgba(255, 255, 255, 0.6);")
        contentLayout.addWidget(hintLabel, 1)

        layout.addWidget(contentWidget, 1)

        # 设置点击样式
        self.setCursor(Qt.PointingHandCursor)


class TemplateListPanel(QWidget):
    """模板列表面板（左侧导航）"""

    templateSelected = Signal(int)  # template_index
    addTemplateRequested = Signal()  # 请求添加模板

    def __init__(self, parent=None):
        super().__init__(parent)
        self._template_names = []
        self._cards = []
        self._selectedIndex = -1
        self._accent_color = "#0078D4"
        self._addCard = None
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 滚动区域
        self.scrollArea = SmoothScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setStyleSheet("""
            SmoothScrollArea {
                border: none;
                background: transparent;
            }
        """)

        # 卡片容器
        self.cardContainer = QWidget()
        self.cardContainer.setStyleSheet("background: transparent;")
        self.cardLayout = QVBoxLayout(self.cardContainer)
        self.cardLayout.setContentsMargins(8, 8, 8, 8)
        self.cardLayout.setSpacing(4)
        self.cardLayout.addStretch()

        self.scrollArea.setWidget(self.cardContainer)
        layout.addWidget(self.scrollArea)

        # 左侧导航面板样式（较暗的背景）
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.1);")

    def setAccentColor(self, color: str):
        """设置装饰色"""
        self._accent_color = color
        # 更新已选中卡片的指示条颜色
        for i, card in enumerate(self._cards):
            if i == self._selectedIndex:
                card.setSelected(True)

    def setTemplates(self, template_names: list[str]):
        """设置模板列表"""
        self._template_names = template_names
        self._renderCards()

    def _renderCards(self):
        """渲染卡片"""
        # 清除现有卡片（包括添加卡片）
        self._clearCards()

        # 创建模板卡片
        for i, name in enumerate(self._template_names):
            card = TemplateCard(name, i, self._accent_color, self.cardContainer)
            card.cardClicked.connect(self._onCardClicked)
            self.cardLayout.insertWidget(self.cardLayout.count() - 1, card)
            self._cards.append(card)

        # 添加"添加模板"卡片
        self._addCard = AddTemplateCard(self.cardContainer)
        self._addCard.addClicked.connect(self.addTemplateRequested.emit)
        self.cardLayout.insertWidget(self.cardLayout.count() - 1, self._addCard)

        # 默认选中第一个
        if self._cards:
            self._onCardClicked(0)

    def _clearCards(self):
        """清除所有卡片（包括添加卡片）"""
        for card in self._cards:
            card.deleteLater()
        self._cards = []
        self._selectedIndex = -1

        # 清除添加卡片
        if self._addCard:
            self._addCard.deleteLater()
            self._addCard = None

    def _onCardClicked(self, index: int):
        """卡片点击事件"""
        # 更新选中状态
        for i, card in enumerate(self._cards):
            card.setSelected(i == index)

        self._selectedIndex = index
        self.templateSelected.emit(index)


class AddTemplateToExperimentDialog(MessageBoxBase):
    """添加模板到实验对话框"""

    def __init__(self, experiment_id: int, existing_template_names: list[str], parent=None):
        super().__init__(parent)
        self._experiment_id = experiment_id
        self._existing_template_names = existing_template_names
        self._customers = []
        self._apps = []
        self._templates = []
        self._loading = False
        self._selected_template_id = None
        self._existing_template_indices = []  # 记录已添加模板的索引

        # 允许点击遮罩层关闭对话框
        self.setClosableOnMaskClicked(True)

        # ESC 键关闭对话框
        self.escShortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.escShortcut.activated.connect(self.reject)

        # 标题
        self.titleLabel = SubtitleLabel(self)
        self.titleLabel.setText("选择模板添加到实验")
        self.viewLayout.addWidget(self.titleLabel)

        # ====== 客户区域 ======
        self.customerCombo = ComboBox(self)
        self.customerCombo.setPlaceholderText("选择客户")
        self.customerCombo.setFixedWidth(350)
        self.customerCombo.currentIndexChanged.connect(self._onCustomerSelected)
        self.viewLayout.addWidget(self.customerCombo)

        # ====== 应用区域 ======
        self.appCombo = ComboBox(self)
        self.appCombo.setPlaceholderText("选择应用")
        self.appCombo.setFixedWidth(350)
        self.appCombo.currentIndexChanged.connect(self._onAppSelected)
        self.viewLayout.addWidget(self.appCombo)

        # ====== 模板区域 ======
        self.templateCombo = ComboBox(self)
        self.templateCombo.setPlaceholderText("选择模板")
        self.templateCombo.setFixedWidth(350)
        self.templateCombo.currentIndexChanged.connect(self._onTemplateSelected)
        self.viewLayout.addWidget(self.templateCombo)

        # 隐藏底部按钮区域
        self.buttonGroup.hide()
        self.yesButton.hide()
        self.cancelButton.hide()

        # 添加"新增模板"按钮
        self.addTemplateBtn = PrimaryPushButton(self)
        self.addTemplateBtn.setText("新增模板到实验")
        self.addTemplateBtn.setFixedWidth(350)
        self.addTemplateBtn.clicked.connect(self._addTemplateToExperiment)
        self.viewLayout.addWidget(self.addTemplateBtn)

        self.widget.setMinimumWidth(400)

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
            InfoBar.error(title="加载失败", content=e.message, parent=self, duration=5000)
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
        self._existing_template_indices = []  # 记录已添加模板的索引
        try:
            self._templates = templates
            self.templateCombo.clear()
            self.templateCombo.addItem("请选择模板")
            for t in templates:
                # 构建完整路径名用于比较
                full_name = self._getTemplateFullName(t.id)
                # 标记已存在的模板
                is_existing = full_name in self._existing_template_names
                display_name = f"{t.name} (已添加)" if is_existing else t.name
                self.templateCombo.addItem(display_name)
                # 记录已添加模板的索引
                if is_existing:
                    self._existing_template_indices.append(self.templateCombo.count() - 1)
            self.templateCombo.setCurrentIndex(0)
            self._selected_template_id = None
        finally:
            self._loading = False

    def _getTemplateFullName(self, template_id: int) -> str:
        """获取模板的完整路径名（客户/应用/模板）"""
        for t in self._templates:
            if t.id == template_id:
                # 找到对应的应用和客户
                app = next((a for a in self._apps if a.id == t.app_id), None)
                if app:
                    customer = next((c for c in self._customers if c.id == app.customer_id), None)
                    if customer:
                        return f"{customer.name}/{app.name}/{t.name}"
                return t.name
        return ""

    def _onCustomerSelected(self, index):
        """选择客户"""
        if self._loading:
            return
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
        if index > 0 and index <= len(self._apps):
            app_id = self._apps[index - 1].id
            try:
                templates = template_api.list(app_id=app_id)
                self._loadTemplates(templates)
            except APIError:
                self._loadTemplates([])
        else:
            self._loadTemplates([])

    def _onTemplateSelected(self, index):
        """选择模板"""
        if self._loading:
            return
        # 检查是否选择了已添加的模板
        if index in self._existing_template_indices:
            InfoBar.warning(title="提示", content="该模板已添加到实验中", parent=self, duration=5000)
            self.templateCombo.setCurrentIndex(0)
            self._selected_template_id = None
            return
        if index > 0 and index <= len(self._templates):
            self._selected_template_id = self._templates[index - 1].id
        else:
            self._selected_template_id = None

    def _addTemplateToExperiment(self):
        """添加模板到实验"""
        if self._selected_template_id is None:
            InfoBar.warning(title="提示", content="请选择一个模板", parent=self, duration=5000)
            return

        try:
            # 直接添加新模板（API会处理去重）
            experiment_api.link_templates(
                self._experiment_id,
                ExperimentTemplateLinkRequest(template_ids=[self._selected_template_id])
            )
            InfoBar.success(title="成功", content="模板已添加到实验", parent=self)
            self.accept()
        except APIError as e:
            InfoBar.error(title="添加失败", content=e.message, parent=self, duration=5000)

    def validate(self) -> bool:
        return True


class ExperimentDetailWindow(FluentWindow):
    """实验详情独立窗口"""

    def __init__(self, experiment_id: int, parent=None):
        super().__init__(parent)
        self._experiment_id = experiment_id
        self._experiment: ExperimentResponse = None

        # 设置为独立窗口（不随主窗口最小化）
        self.setWindowFlags(Qt.Window)

        self.setWindowTitle("实验详情")
        self.resize(1000, 700)
        self.setMinimumSize(700, 500)

        # 启用 Mica 效果
        self.micaEnabled = True

        # 隐藏导航栏（单页面窗口不需要）
        self.navigationInterface.hide()
        self.navigationInterface.panel.setReturnButtonVisible(False)
        self.stackedWidget.hide()

        # 调整内容区域边距：移除左侧导航栏预留空间
        self.widgetLayout.setContentsMargins(0, 32, 0, 0)

        # 调整标题栏高度
        self.titleBar.setFixedHeight(32)

        # 在标题栏左侧添加装饰色方块
        self._createTitleBarColorDot()

        # 调整标题栏位置（移除导航栏预留空间）
        self._adjustTitleBar()

        # 创建内容页面
        self.contentPage = self._createContentPage()
        self.widgetLayout.addWidget(self.contentPage)

        # 加载数据
        self._loadExperiment()

    def _createTitleBarColorDot(self):
        """在标题栏左侧创建装饰色方块"""
        self.titleBarColorDot = QFrame(self.titleBar)
        self.titleBarColorDot.setFixedSize(14, 14)
        self.titleBarColorDot.setStyleSheet("""
            background-color: #0078D4;
            border-radius: 4px;
        """)
        self.titleBarColorDot.move(12, (self.titleBar.height() - 14) // 2)

    def _adjustTitleBar(self):
        """调整标题栏位置，移除导航栏预留空间"""
        self.titleBar.move(0, 0)
        self.titleBar.resize(self.width(), self.titleBar.height())

        # 调整标题标签位置，通过设置左内边距增加与装饰色方块的间距
        if hasattr(self.titleBar, 'titleLabel'):
            self.titleBar.titleLabel.setStyleSheet("padding-left: 14px;")

        # 更新装饰色方块位置
        if hasattr(self, 'titleBarColorDot'):
            self.titleBarColorDot.move(12, (self.titleBar.height() - 14) // 2)

    def resizeEvent(self, event):
        """重写 resizeEvent，调整标题栏位置"""
        super().resizeEvent(event)
        self._adjustTitleBar()

    def _createContentPage(self) -> QWidget:
        """创建内容页面"""
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建分割器
        self.splitter = QSplitter(Qt.Horizontal, page)
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QSplitter::handle:hover {
                background-color: rgba(0, 120, 212, 0.5);
            }
        """)

        # 左侧模板列表面板
        self.templateListPanel = TemplateListPanel(self.splitter)
        self.templateListPanel.setMinimumWidth(150)
        self.templateListPanel.setMaximumWidth(400)
        self.templateListPanel.templateSelected.connect(self._onTemplateSelected)
        self.templateListPanel.addTemplateRequested.connect(self._onAddTemplateRequested)

        # 右侧模板详情面板
        self.templateDetailPanel = TemplateDetailPanel(self.splitter)

        # 添加到分割器
        self.splitter.addWidget(self.templateListPanel)
        self.splitter.addWidget(self.templateDetailPanel)

        # 设置初始比例 1:4
        self.splitter.setSizes([200, 800])

        # 设置拉伸因子，右侧拉伸优先
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        layout.addWidget(self.splitter)

        return page

    def _loadExperiment(self):
        """加载实验数据"""
        try:
            self._experiment = experiment_api.get(self._experiment_id)
            self._renderContent()
        except APIError:
            pass  # TODO: 错误处理

    def _renderContent(self):
        """渲染内容"""
        # 更新窗口标题
        self.setWindowTitle(f"实验 - {self._experiment.name}")

        # 更新标题栏装饰色
        color = self._experiment.color or "#0078D4"
        self.titleBarColorDot.setStyleSheet(f"""
            background-color: {color};
            border-radius: 4px;
        """)

        # 设置模板列表的装饰色
        self.templateListPanel.setAccentColor(color)

        # 设置模板列表
        if self._experiment.template_names:
            self.templateListPanel.setTemplates(self._experiment.template_names)

    def _onTemplateSelected(self, index: int):
        """模板选中事件"""
        if 0 <= index < len(self._experiment.template_names):
            template_name = self._experiment.template_names[index]
            template_id = self._experiment.template_ids[index] if index < len(self._experiment.template_ids) else None
            if template_id:
                self.templateDetailPanel.setTemplate(
                    experiment_id=self._experiment_id,
                    template_id=template_id,
                    template_name=template_name
                )

    def _onAddTemplateRequested(self):
        """请求添加模板"""
        dialog = AddTemplateToExperimentDialog(
            self._experiment_id,
            self._experiment.template_names,
            self
        )
        if dialog.exec():
            # 重新加载实验数据
            self._loadExperiment()
