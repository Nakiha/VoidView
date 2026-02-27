"""模板详情面板 - 标签页设计"""

from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QStackedWidget
from qfluentwidgets import (
    BodyLabel, SubtitleLabel, FluentIcon,
    TransparentToolButton, MessageBoxBase, LineEdit, InfoBar
)

from api import version_api, APIError
from models.experiment import (
    TemplateVersionResponse, TemplateVersionCreateRequest, TemplateVersionUpdateRequest
)
from .template_info_pages import BasicInfoPage, VersionTabPage


class AddVersionDialog(MessageBoxBase):
    """添加版本对话框"""

    def __init__(self, default_name: str, parent=None):
        super().__init__(parent)
        self._default_name = default_name

        # 允许点击遮罩关闭
        self.setClosableOnMaskClicked(True)

        # 标题
        self.titleLabel = SubtitleLabel(self)
        self.titleLabel.setText("添加实验版本")
        self.viewLayout.addWidget(self.titleLabel)

        # 版本名称输入
        self.nameEdit = LineEdit(self)
        self.nameEdit.setPlaceholderText("输入版本名称")
        self.nameEdit.setText(default_name)
        self.nameEdit.selectAll()
        self.viewLayout.addWidget(self.nameEdit)

        # 设置中文按钮文字
        self.yesButton.setText("确定")
        self.cancelButton.setText("取消")

        # 设置焦点
        self.nameEdit.setFocus()

        self.widget.setMinimumWidth(300)

    def get_version_name(self) -> str:
        """获取版本名称"""
        return self.nameEdit.text().strip()

    def validate(self) -> bool:
        """验证输入"""
        name = self.get_version_name()
        if not name:
            InfoBar.warning(title="提示", content="请输入版本名称", parent=self, duration=5000)
            return False
        return True


class VersionTab(QWidget):
    """版本标签页内容 - 旧版兼容，将被替换"""

    def __init__(self, version_name: str, is_basic_info: bool = False, parent=None):
        super().__init__(parent)
        self._version_name = version_name
        self._is_basic_info = is_basic_info
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        if self._is_basic_info:
            # 基础信息页面
            titleLabel = SubtitleLabel(self)
            titleLabel.setText("基础信息")
            layout.addWidget(titleLabel)

            placeholderLabel = BodyLabel(self)
            placeholderLabel.setText("加载中...")
            layout.addWidget(placeholderLabel)
        else:
            # 版本页面
            titleLabel = SubtitleLabel(self)
            titleLabel.setText(f"版本: {self._version_name}")
            layout.addWidget(titleLabel)

            placeholderLabel = BodyLabel(self)
            placeholderLabel.setText("加载中...")
            layout.addWidget(placeholderLabel)

        layout.addStretch()


class TabSeparator(QFrame):
    """标签分隔线"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(1, 20)

class TabBarButton(QWidget):
    """标签栏按钮 - Fluent Design 风格"""

    clicked = Signal()

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text
        self._selected = False
        self._hovered = False
        self.setupUI()

    def setupUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(0)

        # 标签文本
        self.textLabel = BodyLabel(self)
        self.textLabel.setText(self._text)
        layout.addWidget(self.textLabel, 0, Qt.AlignCenter)

        # 确保 QWidget 能够显示背景样式
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.setFixedHeight(32)
        self._updateStyle()

    def setSelected(self, selected: bool):
        """设置选中状态"""
        self._selected = selected
        self._updateStyle()

    def enterEvent(self, event):
        """鼠标进入"""
        self._hovered = True
        self._updateStyle()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开"""
        self._hovered = False
        self._updateStyle()
        super().leaveEvent(event)

    def _updateStyle(self):
        """更新样式 - Win11 记事本风格"""
        # 文本标签始终透明背景，只改变文字颜色
        self.textLabel.setStyleSheet("background-color: transparent; border: none; padding: 0;")

        if self._selected:
            # 选中状态：与内容区域同层级的背景，上圆角下方直角连接内容
            self.setStyleSheet("""
                background-color: rgba(255, 255, 255, 0.05);
                border: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border-bottom-left-radius: 0;
                border-bottom-right-radius: 0;
            """)
        elif self._hovered:
            # 悬浮状态：半亮效果
            self.setStyleSheet("""
                background-color: rgba(255, 255, 255, 0.03);
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border-bottom-left-radius: 0;
                border-bottom-right-radius: 0;
                border: none;
            """)
        else:
            # 未选中状态：透明背景
            self.setStyleSheet("""
                background-color: transparent;
                border: none;
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class TabBar(QWidget):
    """标签栏 - Win11 记事本风格"""

    tabClicked = Signal(int)  # index
    addClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons = []
        self._separators = []  # 分隔线列表
        self.setupUI()

    def setupUI(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # 添加按钮 - 紧跟在标签后面
        self.addButton = TransparentToolButton(self)
        self.addButton.setIcon(FluentIcon.ADD)
        self.addButton.setFixedSize(32, 32)
        self.addButton.clicked.connect(self.addClicked.emit)
        self.layout.addWidget(self.addButton)

        # 添加弹性空间
        self.layout.addStretch()

        self.setFixedHeight(32)

    def addTab(self, text: str) -> int:
        """添加标签，返回索引"""
        index = len(self._buttons)

        # 添加分隔线（如果已有标签）
        if index > 0:
            separator = TabSeparator(self)
            # 插入到 addButton 之前，位于新标签之前
            self.layout.insertWidget(index * 2 - 1, separator)
            self._separators.append(separator)

        # 创建标签按钮
        button = TabBarButton(text, self)
        button.clicked.connect(lambda: self._onTabClicked(button))

        # 插入到 addButton 之前（考虑分隔线）
        insert_pos = index * 2  # 每个标签前有一个分隔线位置
        self.layout.insertWidget(insert_pos, button)
        self._buttons.append(button)
        return index

    def removeTab(self, index: int):
        """移除标签"""
        if 0 <= index < len(self._buttons):
            # 移除标签
            button = self._buttons.pop(index)
            self.layout.removeWidget(button)
            button.deleteLater()

            # 移除对应的分隔线
            if index < len(self._separators):
                separator = self._separators.pop(index)
                self.layout.removeWidget(separator)
                separator.deleteLater()
            elif self._separators:
                # 如果移除的是最后一个标签，移除前一个分隔线
                separator = self._separators.pop()
                self.layout.removeWidget(separator)
                separator.deleteLater()

    def setCurrentIndex(self, index: int):
        """设置当前选中的标签"""
        for i, button in enumerate(self._buttons):
            button.setSelected(i == index)

        # 更新分隔线可见性：选中标签两侧的分隔线隐藏
        self._updateSeparators(index)

    def _updateSeparators(self, selected_index: int):
        """更新分隔线可见性 - 选中标签两侧的分隔线隐藏"""
        for i, separator in enumerate(self._separators):
            # 分隔线 i 在标签 i 和 i+1 之间
            # 如果 i 或 i+1 是选中的，则隐藏
            if i == selected_index - 1 or i == selected_index:
                separator.hide()
            else:
                separator.show()

    def _onTabClicked(self, button: TabBarButton):
        """标签点击"""
        if button in self._buttons:
            index = self._buttons.index(button)
            self.tabClicked.emit(index)


class TemplateDetailPanel(QWidget):
    """模板详情面板 - 标签页设计"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._versions: List[TemplateVersionResponse] = []  # 版本列表（从 API 加载）
        self._version_pages: List[VersionTabPage] = []  # 版本页面列表
        self._current_index = 0
        self._experiment_id: Optional[int] = None
        self._template_id: Optional[int] = None
        self._basic_notes: str = ""  # 基础信息备注
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标签栏（透明背景，选中标签有与内容同层级的背景）
        self.tabBar = TabBar(self)
        self.tabBar.tabClicked.connect(self._onTabClicked)
        self.tabBar.addClicked.connect(self._onAddVersion)
        layout.addWidget(self.tabBar)

        # 内容区域 - 与选中标签同层级背景
        self.stackedWidget = QStackedWidget(self)
        self.stackedWidget.setStyleSheet("background-color: rgba(255, 255, 255, 0.05);")
        layout.addWidget(self.stackedWidget)

        # 初始化基础信息标签页
        self._addBasicInfoTab()

    def _addBasicInfoTab(self):
        """添加基础信息标签页"""
        self._basicInfoPage = BasicInfoPage(self)
        self._basicInfoPage.notesChanged.connect(self._onBasicNotesChanged)
        self.stackedWidget.addWidget(self._basicInfoPage)
        self.tabBar.addTab("基础信息")
        self._current_index = 0
        self.tabBar.setCurrentIndex(0)

    def _onBasicNotesChanged(self, notes: str):
        """基础信息备注变化"""
        if self._experiment_id is None or self._template_id is None:
            return
        try:
            version_api.update_notes(self._experiment_id, self._template_id, notes)
            self._basic_notes = notes
        except APIError as e:
            InfoBar.error(title="保存失败", content=e.message, parent=self, duration=5000)

    def _onTabClicked(self, index: int):
        """标签点击"""
        self._current_index = index
        self.stackedWidget.setCurrentIndex(index)
        self.tabBar.setCurrentIndex(index)

    def _onAddVersion(self):
        """添加新版本"""
        if self._experiment_id is None or self._template_id is None:
            InfoBar.warning(title="提示", content="请先选择模板", parent=self, duration=5000)
            return

        # 计算默认版本名
        version_num = len(self._versions) + 1
        default_name = f"{version_num:03d}"  # 001, 002, 003...

        dialog = AddVersionDialog(default_name, self)
        if dialog.exec():
            version_name = dialog.get_version_name()
            try:
                # 调用 API 创建版本
                new_version = version_api.create(
                    experiment_id=self._experiment_id,
                    template_id=self._template_id,
                    data=TemplateVersionCreateRequest(name=version_name)
                )
                self._versions.append(new_version)

                # 创建版本页面
                page = self._createVersionPage(new_version)
                self._version_pages.append(page)
                self.stackedWidget.addWidget(page)

                # 添加标签
                index = self.tabBar.addTab(f"版本 {version_name}")

                # 切换到新标签
                self._current_index = index
                self.stackedWidget.setCurrentIndex(index)
                self.tabBar.setCurrentIndex(index)

            except APIError as e:
                InfoBar.error(title="创建失败", content=e.message, parent=self, duration=5000)

    def _createVersionPage(self, version: TemplateVersionResponse) -> VersionTabPage:
        """创建版本页面"""
        page = VersionTabPage(self)
        page.set_version(version)
        page.notesChanged.connect(self._onVersionNotesChanged)
        page.templateChanged.connect(self._onVersionTemplateChanged)
        return page

    def _onVersionNotesChanged(self, version_id: int, notes: str):
        """版本备注变化"""
        try:
            version_api.update(version_id, TemplateVersionUpdateRequest(notes=notes))
        except APIError as e:
            InfoBar.error(title="保存失败", content=e.message, parent=self, duration=5000)

    def _onVersionTemplateChanged(self, version_id: int, template_content: str):
        """版本模板配置变化"""
        try:
            version_api.update(version_id, TemplateVersionUpdateRequest(template_content=template_content))
        except APIError as e:
            InfoBar.error(title="保存失败", content=e.message, parent=self, duration=5000)

    def _loadVersions(self):
        """从 API 加载版本列表"""
        if self._experiment_id is None or self._template_id is None:
            return

        try:
            # 加载基础信息备注
            self._basic_notes = version_api.get_notes(self._experiment_id, self._template_id)
            self._basicInfoPage.set_data(self._experiment_id, self._template_id, self._basic_notes)

            # 加载版本列表
            self._versions = version_api.list(
                experiment_id=self._experiment_id,
                template_id=self._template_id
            )

            # 创建版本标签页
            for version in self._versions:
                page = self._createVersionPage(version)
                self._version_pages.append(page)
                self.stackedWidget.addWidget(page)
                self.tabBar.addTab(f"版本 {version.name}")

        except APIError as e:
            InfoBar.error(title="加载版本失败", content=e.message, parent=self, duration=5000)

    def setTemplate(self, experiment_id: int, template_id: int, template_name: str):
        """设置当前模板"""
        # 保存实验和模板 ID
        self._experiment_id = experiment_id
        self._template_id = template_id

        # 清除现有版本标签页（保留基础信息）
        while len(self._versions) > 0:
            self._versions.pop()
            self._version_pages.pop()
            # 移除最后一个标签（从后往前移除）
            self.tabBar.removeTab(len(self.tabBar._buttons) - 1)
            last_widget = self.stackedWidget.widget(self.stackedWidget.count() - 1)
            if last_widget:
                self.stackedWidget.removeWidget(last_widget)
                last_widget.deleteLater()

        # 切换到基础信息页
        self._current_index = 0
        self.stackedWidget.setCurrentIndex(0)
        self.tabBar.setCurrentIndex(0)

        # 从 API 加载版本列表
        self._loadVersions()
