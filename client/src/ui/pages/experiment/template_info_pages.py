"""模板标签页组件 - 基础信息页和版本页"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import SubtitleLabel

from .editable_field import EditableField
from models.experiment import TemplateVersionResponse


class BasicInfoPage(QWidget):
    """基础信息标签页

    显示模板的基本备注信息
    """

    notesChanged = Signal(str)  # 备注变化信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self._experiment_id: Optional[int] = None
        self._template_id: Optional[int] = None
        self._notes: str = ""
        self.setupUI()

    def setupUI(self):
        # 页面背景透明
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background-color: transparent;")

        layout = QVBoxLayout(self)
        # 收窄边距，左侧对齐标签页页签文本（约16px）
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # 备注字段（移除重复的"基础信息"标题）
        self.notesField = EditableField(
            title="备注",
            content="",
            is_formatted=False,
            placeholder="暂无备注，点击编辑按钮添加...",
            parent=self
        )
        self.notesField.contentChanged.connect(self._onNotesChanged)
        layout.addWidget(self.notesField)

        layout.addStretch()

    def set_data(self, experiment_id: int, template_id: int, notes: str = ""):
        """设置数据"""
        self._experiment_id = experiment_id
        self._template_id = template_id
        self._notes = notes or ""
        self.notesField.setContent(self._notes)

    def _onNotesChanged(self, content: str):
        """备注变化"""
        self._notes = content
        self.notesChanged.emit(content)


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
