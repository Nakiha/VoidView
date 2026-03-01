"""输入文件组件 - 支持文件上传和管理"""

import os
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse

from PySide6.QtCore import Qt, Signal, QMimeData, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFileDialog,
    QAbstractItemView, QSizePolicy, QListWidgetItem
)
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from qfluentwidgets import (
    BodyLabel, StrongBodyLabel, CaptionLabel, TransparentToolButton,
    ListWidget, FluentIcon,
    MessageBoxBase, SubtitleLabel, InfoBar, CardWidget, isDarkTheme
)

from app.config import user_config


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def get_server_hostname() -> str:
    """从服务器 URL 提取主机名"""
    try:
        parsed = urlparse(user_config.server_url)
        return parsed.hostname or "localhost"
    except Exception:
        return "localhost"


class FileUploadDialog(MessageBoxBase):
    """文件上传对话框 - 支持拖拽和文件选择"""

    filesSelected = Signal(list)  # 选中文件列表

    def __init__(self, parent=None):
        super().__init__(parent)
        self._files: List[str] = []

        self.setClosableOnMaskClicked(True)
        self.yesButton.setText("上传")
        self.cancelButton.setText("取消")

        # 标题
        self.titleLabel = SubtitleLabel("上传文件", self)
        self.viewLayout.addWidget(self.titleLabel)

        # 拖拽区域
        self.dropArea = FileDropArea(self)
        self.dropArea.setFixedHeight(150)
        self.dropArea.filesDropped.connect(self._onFilesDropped)
        self.viewLayout.addWidget(self.dropArea)

        # 已选文件列表
        self.fileListLabel = BodyLabel("已选择 0 个文件", self)
        self.viewLayout.addWidget(self.fileListLabel)

        self.widget.setMinimumWidth(450)

        # 连接 yesButton 点击信号，在关闭前发射 filesSelected
        self.yesButton.clicked.disconnect()  # 断开默认连接
        self.yesButton.clicked.connect(self._onYesClicked)

    def _onYesClicked(self):
        """上传按钮点击"""
        if self.validate():
            self.filesSelected.emit(self._files)
            self.accept()

    def _onFilesDropped(self, files: List[str]):
        """文件被拖入"""
        self._files = files
        self.fileListLabel.setText(f"已选择 {len(files)} 个文件")

    def get_files(self) -> List[str]:
        """获取选中的文件列表"""
        return self._files

    def validate(self) -> bool:
        """验证"""
        if not self._files:
            InfoBar.warning(title="提示", content="请选择要上传的文件", parent=self, duration=5000)
            return False
        return True


class FileDropArea(CardWidget):
    """文件拖拽区域"""

    filesDropped = Signal(list)  # 文件被拖入

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._is_drag_over = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)

        layout.addStretch()

        # 提示
        self.hintLabel = SubtitleLabel("拖拽文件到此处", self)
        self.hintLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.hintLabel)

        self.subHintLabel = CaptionLabel("或点击此区域选择文件", self)
        self.subHintLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.subHintLabel)

        layout.addStretch()

    def _update_style(self, is_drag_over: bool):
        """更新样式"""
        if is_drag_over:
            self.setStyleSheet("""
                FileDropArea {
                    background-color: rgba(76, 175, 80, 0.2);
                    border: 2px dashed #4CAF50;
                    border-radius: 8px;
                }
            """)
            self.hintLabel.setText("松开以上传文件")
            self.hintLabel.setStyleSheet("color: #4CAF50;")
        else:
            self.setStyleSheet("")
            self.hintLabel.setText("拖拽文件到这里")
            self.hintLabel.setStyleSheet("")

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._is_drag_over = True
            self._update_style(True)

    def dragLeaveEvent(self, event):
        """拖拽离开"""
        self._is_drag_over = False
        self._update_style(False)

    def dropEvent(self, event: QDropEvent):
        """拖拽放下"""
        self._is_drag_over = False
        self._update_style(False)
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                files.append(path)
        if files:
            self.filesDropped.emit(files)

    def mousePressEvent(self, event):
        """点击选择文件"""
        if event.button() == Qt.LeftButton:
            self._selectFiles()

    def _selectFiles(self):
        """打开文件选择对话框"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择文件",
            "",
            "所有文件 (*.*)"
        )
        if files:
            self.filesDropped.emit(files)


class InputFileField(QWidget):
    """输入文件组件

    布局：
    - 第一行：标题 + 服务器地址 + 统计信息（文件数、总大小、可用空间）+ 按钮
    - 第二行：文件列表（占据剩余空间）
    """

    filesChanged = Signal(list)  # 文件列表变化信号

    def __init__(
        self,
        storage_path: str = "",
        placeholder: str = "暂无输入文件",
        parent=None
    ):
        super().__init__(parent)
        self._storage_path = storage_path
        self._placeholder = placeholder
        self._files: List[dict] = []  # [{name, size}, ...]
        self._experiment_id: Optional[int] = None
        self._template_id: Optional[int] = None
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 允许组件扩展
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 整个组件背景透明
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background-color: transparent;")

        # 第一行：标题 + 统计信息 + 按钮
        headerLayout = QHBoxLayout()
        headerLayout.setContentsMargins(0, 0, 0, 0)
        headerLayout.setSpacing(8)

        self.titleLabel = StrongBodyLabel("输入文件", self)
        headerLayout.addWidget(self.titleLabel)

        # 服务器地址（灰色次要文字）
        self.serverLabel = CaptionLabel(self)
        self.serverLabel.setText(f"({get_server_hostname()})")
        self.serverLabel.setStyleSheet("color: gray;")
        headerLayout.addWidget(self.serverLabel)

        # 统计信息（灰色次要文字）
        self.fileCountLabel = CaptionLabel("文件数: 0", self)
        self.fileCountLabel.setStyleSheet("color: gray;")
        headerLayout.addWidget(self.fileCountLabel)

        self.totalSizeLabel = CaptionLabel("总大小: 0 B", self)
        self.totalSizeLabel.setStyleSheet("color: gray;")
        headerLayout.addWidget(self.totalSizeLabel)

        self.freeSpaceLabel = CaptionLabel("可用空间: --", self)
        self.freeSpaceLabel.setStyleSheet("color: gray;")
        headerLayout.addWidget(self.freeSpaceLabel)

        headerLayout.addStretch()

        # 复制路径按钮
        self.copyPathBtn = TransparentToolButton(self)
        self.copyPathBtn.setIcon(FluentIcon.COPY)
        self.copyPathBtn.setFixedSize(28, 28)
        self.copyPathBtn.setToolTip("复制存储路径")
        self.copyPathBtn.clicked.connect(self._onCopyPath)
        headerLayout.addWidget(self.copyPathBtn)

        # 上传按钮
        self.uploadBtn = TransparentToolButton(self)
        self.uploadBtn.setIcon(FluentIcon.ADD)
        self.uploadBtn.setFixedSize(28, 28)
        self.uploadBtn.setToolTip("上传文件")
        self.uploadBtn.clicked.connect(self._onUpload)
        headerLayout.addWidget(self.uploadBtn)

        layout.addLayout(headerLayout)

        # 文件列表（占据剩余空间）
        self.fileList = ListWidget(self)
        self.fileList.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.fileList.setSelectionMode(QAbstractItemView.SingleSelection)
        # 添加背景色提升视觉层级
        self._updateListStyle()
        layout.addWidget(self.fileList, 1)  # stretch=1 占据剩余空间

        # 更新可用空间
        self._updateFreeSpace()

    def _updateListStyle(self):
        """更新列表样式，根据主题设置背景色"""
        # Fluent Design: 列表背景比页面稍深/浅一级
        if isDarkTheme():
            bg_color = "rgba(255, 255, 255, 0.05)"
            border_color = "rgba(255, 255, 255, 0.08)"
            item_hover = "rgba(255, 255, 255, 0.08)"
            item_selected = "rgba(255, 255, 255, 0.12)"
        else:
            bg_color = "rgba(0, 0, 0, 0.03)"
            border_color = "rgba(0, 0, 0, 0.05)"
            item_hover = "rgba(0, 0, 0, 0.05)"
            item_selected = "rgba(0, 0, 0, 0.08)"

        self.fileList.setStyleSheet(f"""
            ListWidget {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                outline: none;
            }}
            ListWidget::item {{
                background-color: transparent;
                border: none;
                padding: 0px 2px;
                border-radius: 4px;
            }}
            ListWidget::item:hover {{
                background-color: {item_hover};
            }}
            ListWidget::item:selected {{
                background-color: {item_selected};
            }}
            ListWidget::item:selected:!active {{
                background-color: {item_selected};
            }}
        """)

    def _onCopyPath(self):
        """复制存储路径"""
        # 如果没有存储路径，尝试从后端加载
        if not self._storage_path and self._experiment_id is not None and self._template_id is not None:
            from api.experiment import version_api
            try:
                data = version_api.get_input_files(self._experiment_id, self._template_id)
                self._storage_path = data.get("storage_path", "")
            except Exception:
                pass

        if self._storage_path:
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(self._storage_path)
            InfoBar.success(
                title="已复制",
                content=f"路径已复制到剪贴板",
                parent=self.window(),
                duration=2000
            )
        else:
            InfoBar.warning(
                title="提示",
                content="存储路径未设置",
                parent=self.window(),
                duration=3000
            )

    def _onUpload(self):
        """上传文件"""
        dialog = FileUploadDialog(self.window())
        dialog.filesSelected.connect(self._onFilesSelected)

        if dialog.exec():
            # 文件会在 _onFilesSelected 中处理
            pass

    def _onFilesSelected(self, files: List[str]):
        """文件被选中"""
        # 添加文件到列表
        for file_path in files:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            self._files.append({
                "name": file_name,
                "size": file_size,
                "path": file_path
            })

        self._updateFileList()
        self.filesChanged.emit(self._files)
        self._save_to_backend()

        InfoBar.success(
            title="上传成功",
            content=f"已添加 {len(files)} 个文件",
            parent=self.window(),
            duration=3000
        )

    def _updateFileList(self):
        """更新文件列表显示"""
        self.fileList.clear()
        total_size = 0

        for file_info in self._files:
            item = QListWidgetItem(f"{file_info['name']}  ({format_file_size(file_info['size'])})")
            self.fileList.addItem(item)
            total_size += file_info['size']

        # 更新统计信息
        self.fileCountLabel.setText(f"文件数: {len(self._files)}")
        self.totalSizeLabel.setText(f"总大小: {format_file_size(total_size)}")

    def _updateFreeSpace(self):
        """更新可用空间（从后端重新加载数据）"""
        # 可用空间现在从后端获取，这里只在没有加载后端数据时显示 --
        if self._experiment_id is not None and self._template_id is not None:
            # 有实验和模板ID时，从后端加载
            self.load_from_backend()
        else:
            self.freeSpaceLabel.setText("可用空间: --")

    def set_storage_path(self, path: str):
        """设置存储路径"""
        self._storage_path = path
        # 可用空间需要从后端获取，这里只显示 --
        self.freeSpaceLabel.setText("可用空间: --")

    def set_files(self, files: List[dict]):
        """设置文件列表"""
        self._files = files
        self._updateFileList()

    def get_files(self) -> List[dict]:
        """获取文件列表"""
        return self._files

    def clear_files(self):
        """清空文件列表"""
        self._files = []
        self._updateFileList()
        self._save_to_backend()

    def set_experiment_template(self, experiment_id: int, template_id: int):
        """设置实验和模板ID，用于后端交互"""
        self._experiment_id = experiment_id
        self._template_id = template_id

    def load_from_backend(self):
        """从后端加载输入文件数据"""
        if self._experiment_id is None or self._template_id is None:
            return

        from api.experiment import version_api
        try:
            data = version_api.get_input_files(self._experiment_id, self._template_id)
            self._storage_path = data.get("storage_path", "")
            self._files = data.get("input_files", [])
            self._updateFileList()
            # 使用后端返回的可用空间
            free_space = data.get("free_space")
            if free_space is not None:
                self.freeSpaceLabel.setText(f"可用空间: {format_file_size(free_space)}")
            else:
                self.freeSpaceLabel.setText("可用空间: --")
        except Exception as e:
            InfoBar.warning(
                title="加载失败",
                content=f"无法加载输入文件: {str(e)}",
                parent=self.window(),
                duration=3000
            )

    def _save_to_backend(self):
        """保存输入文件数据到后端"""
        if self._experiment_id is None or self._template_id is None:
            return

        from api.experiment import version_api
        try:
            version_api.update_input_files(
                self._experiment_id,
                self._template_id,
                self._storage_path,
                self._files
            )
        except Exception as e:
            InfoBar.warning(
                title="保存失败",
                content=f"无法保存输入文件: {str(e)}",
                parent=self.window(),
                duration=3000
            )
