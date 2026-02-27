"""可编辑字段组件 - 支持文本和格式化文本编辑"""

import json
from typing import Optional, Callable
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy
from qfluentwidgets import (
    BodyLabel, StrongBodyLabel, TransparentToolButton,
    FluentIcon, MessageBoxBase, TextEdit, InfoBar, SubtitleLabel
)


class EditDialog(MessageBoxBase):
    """编辑对话框"""

    def __init__(
        self,
        title: str,
        initial_content: str,
        is_formatted: bool = False,
        parent=None
    ):
        super().__init__(parent)
        self._title = title
        self._initial_content = initial_content
        self._is_formatted = is_formatted
        self._format_error: Optional[str] = None

        # 允许点击遮罩关闭
        self.setClosableOnMaskClicked(True)

        # 设置中文按钮文字
        self.yesButton.setText("保存")
        self.cancelButton.setText("取消")

        # 标题
        self.titleLabel = SubtitleLabel(self)
        self.titleLabel.setText(title)
        self.viewLayout.addWidget(self.titleLabel)

        # 文本编辑器
        self.textEdit = TextEdit(self)
        self.textEdit.setPlainText(initial_content)
        self.textEdit.setPlaceholderText("请输入内容..." if not is_formatted else "请输入 JSON 或 YAML 格式内容...")
        self.textEdit.setFixedHeight(200)
        self.textEdit.textChanged.connect(self._onTextChanged)
        self.viewLayout.addWidget(self.textEdit)

        # 格式错误提示标签
        self.errorLabel = BodyLabel(self)
        self.errorLabel.setStyleSheet("color: #F44336;")
        self.errorLabel.setWordWrap(True)
        self.errorLabel.hide()
        self.viewLayout.addWidget(self.errorLabel)

        self.widget.setMinimumWidth(450)

    def _onTextChanged(self):
        """文本变化时检测格式"""
        if self._is_formatted:
            self._validateFormat()

    def _validateFormat(self) -> bool:
        """验证格式"""
        content = self.textEdit.toPlainText().strip()
        if not content:
            self._format_error = None
            self.errorLabel.hide()
            return True

        # 尝试 JSON
        try:
            json.loads(content)
            self._format_error = None
            self.errorLabel.hide()
            return True
        except json.JSONDecodeError:
            pass

        # 尝试 YAML（简单检测）
        try:
            import yaml
            yaml.safe_load(content)
            self._format_error = None
            self.errorLabel.hide()
            return True
        except Exception:
            pass

        self._format_error = "格式不正确：内容不是有效的 JSON 或 YAML 格式"
        self.errorLabel.setText(self._format_error)
        self.errorLabel.show()
        return False

    def get_content(self) -> str:
        """获取编辑后的内容"""
        return self.textEdit.toPlainText()

    def has_format_error(self) -> bool:
        """是否有格式错误"""
        return self._format_error is not None

    def validate(self) -> bool:
        """验证 - 允许保存即使格式不对，但提示用户"""
        return True  # 始终允许保存


class EditableField(QWidget):
    """可编辑字段组件

    布局：
    - 第一行：左侧标题，右侧编辑按钮
    - 第二行：内容文本
    """

    contentChanged = Signal(str)  # 内容变化信号

    def __init__(
        self,
        title: str,
        content: str = "",
        is_formatted: bool = False,
        placeholder: str = "暂无内容",
        parent=None
    ):
        super().__init__(parent)
        self._title = title
        self._content = content
        self._is_formatted = is_formatted
        self._placeholder = placeholder
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 整个组件背景透明
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background-color: transparent;")

        # 第一行：标题 + 编辑按钮
        headerLayout = QHBoxLayout()
        headerLayout.setContentsMargins(0, 0, 0, 0)
        headerLayout.setSpacing(8)

        self.titleLabel = StrongBodyLabel(self)
        self.titleLabel.setText(self._title)
        self.titleLabel.setAttribute(Qt.WA_TranslucentBackground, True)
        self.titleLabel.setStyleSheet("background-color: transparent;")
        headerLayout.addWidget(self.titleLabel)

        headerLayout.addStretch()

        self.editButton = TransparentToolButton(self)
        self.editButton.setIcon(FluentIcon.EDIT)
        self.editButton.setFixedSize(28, 28)
        self.editButton.clicked.connect(self._onEditClicked)
        headerLayout.addWidget(self.editButton)

        layout.addLayout(headerLayout)

        # 第二行：内容文本（背景透明）
        self.contentLabel = BodyLabel(self)
        self.contentLabel.setWordWrap(True)
        self.contentLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.contentLabel.setAttribute(Qt.WA_TranslucentBackground, True)
        self.contentLabel.setStyleSheet("background-color: transparent;")
        self._updateContentDisplay()
        layout.addWidget(self.contentLabel)

    def _updateContentDisplay(self):
        """更新内容显示"""
        if self._content:
            self.contentLabel.setText(self._content)
            self.contentLabel.setStyleSheet("")
        else:
            self.contentLabel.setText(self._placeholder)
            self.contentLabel.setStyleSheet("color: rgba(255, 255, 255, 0.5);")

    def _onEditClicked(self):
        """编辑按钮点击"""
        dialog = EditDialog(
            title=f"编辑 {self._title}",
            initial_content=self._content,
            is_formatted=self._is_formatted,
            parent=self.window()
        )

        if dialog.exec():
            new_content = dialog.get_content()

            # 如果是格式化文本且有格式错误，显示警告
            if self._is_formatted and dialog.has_format_error():
                InfoBar.warning(
                    title="格式警告",
                    content="内容格式不正确，已保存但可能无法正常解析",
                    parent=self.window(),
                    duration=5000
                )

            if new_content != self._content:
                self._content = new_content
                self._updateContentDisplay()
                self.contentChanged.emit(new_content)

    def setContent(self, content: str):
        """设置内容"""
        self._content = content
        self._updateContentDisplay()

    def getContent(self) -> str:
        """获取内容"""
        return self._content
