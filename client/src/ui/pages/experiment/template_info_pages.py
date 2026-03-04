"""模板标签页组件 - 基础信息页和版本页"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from qfluentwidgets import SubtitleLabel, SmoothScrollArea, ScrollBarHandleDisplayMode

from .editable_field import EditableField
from .input_file_field import InputFileField
from models.experiment import TemplateVersionResponse


class BasicInfoPage(SmoothScrollArea):
    """基础信息标签页

    显示模板的基本备注信息和输入文件，支持滚动
    """

    notesChanged = Signal(str)  # 备注变化信号
    filesChanged = Signal(list)  # 文件列表变化信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self._experiment_id: Optional[int] = None
        self._template_id: Optional[int] = None
        self._notes: str = ""
        self._storage_path: str = ""
        self.setupUI()

    def setupUI(self):
        # 页面背景透明
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background-color: transparent; border: none;")
        self.setWidgetResizable(True)

        # 设置滚动条仅在悬停时显示
        self.delegate.vScrollBar.setHandleDisplayMode(ScrollBarHandleDisplayMode.ON_HOVER)

        # 滚动内容容器
        self.contentWidget = QWidget(self)
        self.contentWidget.setAttribute(Qt.WA_TranslucentBackground, True)
        self.contentWidget.setStyleSheet("background-color: transparent;")
        self.setWidget(self.contentWidget)

        layout = QVBoxLayout(self.contentWidget)
        # 收窄边距，左侧对齐标签页页签文本（约16px）
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # 备注字段
        self.notesField = EditableField(
            title="备注",
            content="",
            is_formatted=False,
            placeholder="暂无备注，点击编辑按钮添加...",
            parent=self.contentWidget
        )
        self.notesField.contentChanged.connect(self._onNotesChanged)
        layout.addWidget(self.notesField)

        # 输入文件组件（最小高度在 resize 时动态设置）
        self.inputFileField = InputFileField(
            storage_path="",
            parent=self.contentWidget
        )
        self.inputFileField.filesChanged.connect(self._onFilesChanged)
        layout.addWidget(self.inputFileField)

    def resizeEvent(self, event):
        """窗口大小变化时，动态调整输入文件组件的最小高度"""
        super().resizeEvent(event)
        # 输入文件组件的最小高度 = 标签页高度 - 边距
        # 这样总内容高度 = 备注高度 + 标签页高度，超出可视区域
        # 用户滚动下去后，文件列表刚好填满整个标签页
        margins = self.contentWidget.layout().contentsMargins()
        page_height = self.height() - margins.top() - margins.bottom()
        self.inputFileField.setMinimumHeight(max(page_height, 200))

    def set_data(self, experiment_id: int, template_id: int, notes: str = "", storage_path: str = ""):
        """设置数据"""
        self._experiment_id = experiment_id
        self._template_id = template_id
        self._notes = notes or ""
        self._storage_path = storage_path
        self.notesField.setContent(self._notes)

        # 设置实验和模板ID，并从后端加载输入文件
        self.inputFileField.set_experiment_template(experiment_id, template_id)
        self.inputFileField.load_from_backend()

    def _onNotesChanged(self, content: str):
        """备注变化"""
        self._notes = content
        self.notesChanged.emit(content)

    def _onFilesChanged(self, files: list):
        """文件列表变化"""
        self.filesChanged.emit(files)


class VersionTabPage(QWidget):
    """版本标签页

    显示特定版本的备注和模板配置
    """

    notesChanged = Signal(int, str)  # (version_id, notes)
    templateChanged = Signal(int, str)  # (version_id, template_content)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._version: Optional[TemplateVersionResponse] = None
        self.setupUI()

    def setupUI(self):
        # 页面背景透明
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background-color: transparent;")

        layout = QVBoxLayout(self)
        # 收窄边距，左侧对齐标签页页签文本（约16px）
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # 备注字段
        self.notesField = EditableField(
            title="备注",
            content="",
            is_formatted=False,
            placeholder="暂无备注，点击编辑按钮添加...",
            parent=self
        )
        self.notesField.contentChanged.connect(self._onNotesChanged)
        layout.addWidget(self.notesField)

        # 模板配置字段（格式化文本）
        self.templateField = EditableField(
            title="模板配置",
            content="",
            is_formatted=True,
            placeholder="暂无模板配置，点击编辑按钮添加 JSON 或 YAML...",
            parent=self
        )
        self.templateField.contentChanged.connect(self._onTemplateChanged)
        layout.addWidget(self.templateField)

        layout.addStretch()

    def set_version(self, version: TemplateVersionResponse):
        """设置版本数据"""
        self._version = version
        # 从版本对象获取 notes 和 template_content
        self.notesField.setContent(version.notes or "")
        self.templateField.setContent(version.template_content or "")

    def _onNotesChanged(self, content: str):
        """备注变化"""
        if self._version:
            self.notesChanged.emit(self._version.id, content)

    def _onTemplateChanged(self, content: str):
        """模板配置变化"""
        if self._version:
            self.templateChanged.emit(self._version.id, content)
