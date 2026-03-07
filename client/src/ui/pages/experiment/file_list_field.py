"""通用文件列表组件 - 支持输入文件(可上传)和输出文件(只读)"""

import os
from pathlib import Path
from typing import Optional, List, Literal
from urllib.parse import urlparse

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFileDialog,
    QAbstractItemView, QSizePolicy, QListWidgetItem
)
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from qfluentwidgets import (
    BodyLabel, StrongBodyLabel, CaptionLabel, TransparentToolButton,
    ListWidget, FluentIcon, ComboBox,
    MessageBoxBase, SubtitleLabel, InfoBar, CardWidget, isDarkTheme
)

from app.config import user_config
from voidview_shared import get_logger

logger = get_logger()


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

    filesSelected = Signal(list, str)  # (文件列表, 目标类型: "shared"/"private")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._files: List[str] = []
        self._target: str = "private"  # 默认私有

        self.setClosableOnMaskClicked(True)
        self.yesButton.setText("上传")
        self.cancelButton.setText("取消")

        # 标题
        self.titleLabel = SubtitleLabel("上传文件", self)
        self.viewLayout.addWidget(self.titleLabel)

        # 上传目标选择
        targetLayout = QHBoxLayout()
        targetLabel = BodyLabel("上传到:", self)
        self.targetComboBox = ComboBox(self)
        self.targetComboBox.addItems(["私有输入 (仅此模板)", "共享输入 (所有模板)"])
        self.targetComboBox.setCurrentIndex(0)
        self.targetComboBox.currentIndexChanged.connect(self._onTargetChanged)
        targetLayout.addWidget(targetLabel)
        targetLayout.addWidget(self.targetComboBox)
        targetLayout.addStretch()
        self.viewLayout.addLayout(targetLayout)

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

    def _onTargetChanged(self, index: int):
        """上传目标变更"""
        self._target = "shared" if index == 1 else "private"

    def get_target(self) -> str:
        """获取上传目标"""
        return self._target

    def _onYesClicked(self):
        """上传按钮点击"""
        if self.validate():
            self.filesSelected.emit(self._files, self._target)
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


class FileListField(QWidget):
    """通用文件列表组件

    支持两种模式：
    - input: 输入文件，支持上传，显示共享/私有标记
    - output: 输出文件，只读显示

    布局：
    - 第一行：标题 + 服务器地址 + 统计信息（文件数、总大小、可用空间）+ 按钮
    - 第二行：文件列表（占据剩余空间）
    """

    filesChanged = Signal(list)  # 文件列表变化信号

    def __init__(
        self,
        mode: Literal["input", "output"] = "input",
        storage_path: str = "",
        placeholder: str = "",
        parent=None
    ):
        super().__init__(parent)
        self._mode = mode
        self._storage_path = storage_path
        self._placeholder = placeholder or ("暂无输入文件" if mode == "input" else "暂无输出文件")
        self._files: List[dict] = []  # [{name, size}, ...]
        self._experiment_id: Optional[int] = None
        self._template_id: Optional[int] = None
        self._version_id: Optional[int] = None  # 仅输出文件需要
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

        # 标题
        title = "输入文件" if self._mode == "input" else "输出文件"
        self.titleLabel = StrongBodyLabel(title, self)
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

        # 输入模式显示可用空间
        if self._mode == "input":
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
        # ExtendedSelection 支持: 单选、Ctrl+点击切换、Shift+点击范围选择
        self.fileList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # 点击空白处取消选择
        self.fileList.mousePressEvent = self._onListMousePress
        # 添加背景色提升视觉层级
        self._updateListStyle()
        layout.addWidget(self.fileList, 1)  # stretch=1 占据剩余空间

    def _onListMousePress(self, event):
        """处理列表鼠标点击 - 点击空白处取消选择"""
        # 获取点击位置对应的 item
        item = self.fileList.itemAt(event.position().toPoint())
        if item is None:
            # 点击在空白区域，清除选择
            self.fileList.clearSelection()
        else:
            # 调用父类方法处理正常的选择逻辑
            ListWidget.mousePressEvent(self.fileList, event)

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
        if self._storage_path:
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(self._storage_path)
            InfoBar.success(
                title="已复制",
                content="路径已复制到剪贴板",
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
        if self._mode == "input":
            # 输入模式：使用带共享/私有选择的对话框
            dialog = FileUploadDialog(self.window())
            dialog.filesSelected.connect(self._onFilesSelected)
            if dialog.exec():
                pass
        else:
            # 输出模式：使用简单的文件选择
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "选择输出文件",
                "",
                "所有文件 (*.*)"
            )
            if files:
                self._onOutputFilesSelected(files)

    def _onFilesSelected(self, files: List[str], target: str = "private"):
        """文件被选中 - 上传到服务端（仅输入模式）

        Args:
            files: 文件路径列表
            target: 上传目标 - "shared"(共享) 或 "private"(私有)
        """
        if self._experiment_id is None or self._template_id is None:
            InfoBar.warning(
                title="无法上传",
                content="请先保存实验后再上传文件",
                parent=self.window(),
                duration=3000
            )
            return

        from api.experiment import version_api

        # 显示上传进度提示
        target_name = "共享目录" if target == "shared" else "私有目录"
        InfoBar.info(
            title="正在上传",
            content=f"正在上传 {len(files)} 个文件到{target_name}...",
            parent=self.window(),
            duration=5000
        )

        try:
            # 上传文件到服务端
            version_api.upload_input_files(
                self._experiment_id,
                self._template_id,
                files,
                target=target
            )

            # 上传成功后重新加载完整列表（共享+私有）
            self.load_from_backend()

            self.filesChanged.emit(self._files)

            InfoBar.success(
                title="上传成功",
                content=f"已上传 {len(files)} 个文件到{target_name}",
                parent=self.window(),
                duration=3000
            )
        except Exception as e:
            logger.error(f"文件上传失败: {e}", exc_info=True)
            InfoBar.error(
                title="上传失败",
                content=f"文件上传失败: {str(e)}",
                parent=self.window(),
                duration=5000
            )

    def _onOutputFilesSelected(self, files: List[str]):
        """输出文件被选中 - 上传到服务端

        Args:
            files: 文件路径列表
        """
        if self._experiment_id is None or self._template_id is None or self._version_id is None:
            InfoBar.warning(
                title="无法上传",
                content="请先保存版本后再上传文件",
                parent=self.window(),
                duration=3000
            )
            return

        from api.experiment import version_api

        # 显示上传进度提示
        InfoBar.info(
            title="正在上传",
            content=f"正在上传 {len(files)} 个输出文件...",
            parent=self.window(),
            duration=5000
        )

        try:
            # 上传文件到服务端
            version_api.upload_output_files(
                self._experiment_id,
                self._template_id,
                self._version_id,
                files
            )

            # 上传成功后重新加载
            self.load_from_backend()

            InfoBar.success(
                title="上传成功",
                content=f"已上传 {len(files)} 个输出文件",
                parent=self.window(),
                duration=3000
            )
        except Exception as e:
            logger.error(f"输出文件上传失败: {e}", exc_info=True)
            InfoBar.error(
                title="上传失败",
                content=f"输出文件上传失败: {str(e)}",
                parent=self.window(),
                duration=5000
            )

    def _updateFileList(self):
        """更新文件列表显示"""
        from PySide6.QtGui import QColor

        self.fileList.clear()
        total_size = 0

        # 获取当前主题的共享文件标签颜色（仅输入模式）
        if self._mode == "input":
            if isDarkTheme():
                shared_color = QColor("#4ECDC4")  # 青色，在深色主题下可见
            else:
                shared_color = QColor("#00897B")  # 深青色

        for file_info in self._files:
            name = file_info["name"]
            size_str = format_file_size(file_info["size"])

            # 输入模式：共享文件添加标记
            if self._mode == "input":
                source = file_info.get("source", "private")
                if source == "shared":
                    display_text = f"[共享] {name}  ({size_str})"
                else:
                    display_text = f"{name}  ({size_str})"
            else:
                # 输出模式：简单显示
                display_text = f"{name}  ({size_str})"

            item = QListWidgetItem(display_text)

            # 输入模式：共享文件使用不同的颜色
            if self._mode == "input" and file_info.get("source") == "shared":
                item.setForeground(shared_color)

            self.fileList.addItem(item)
            total_size += file_info['size']

        # 更新统计信息
        self.fileCountLabel.setText(f"文件数: {len(self._files)}")
        self.totalSizeLabel.setText(f"总大小: {format_file_size(total_size)}")

    def set_storage_path(self, path: str):
        """设置存储路径"""
        self._storage_path = path
        if self._mode == "input" and hasattr(self, 'freeSpaceLabel'):
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
        if self._mode == "input":
            self._save_to_backend()

    def set_experiment_template(self, experiment_id: int, template_id: int, version_id: Optional[int] = None):
        """设置实验、模板和版本ID，用于后端交互

        Args:
            experiment_id: 实验ID
            template_id: 模板ID
            version_id: 版本ID（仅输出模式需要）
        """
        self._experiment_id = experiment_id
        self._template_id = template_id
        self._version_id = version_id

    def load_from_backend(self):
        """从后端加载文件数据"""
        if self._experiment_id is None or self._template_id is None:
            return

        try:
            if self._mode == "input":
                self._load_input_files()
            else:
                self._load_output_files()
        except Exception as e:
            mode_name = "输入" if self._mode == "input" else "输出"
            logger.error(f"加载{mode_name}文件失败: experiment_id={self._experiment_id}, "
                        f"template_id={self._template_id}, version_id={self._version_id}, error={e}")
            InfoBar.warning(
                title="加载失败",
                content=f"无法加载{mode_name}文件: {str(e)}",
                parent=self.window(),
                duration=3000
            )

    def _load_input_files(self):
        """加载输入文件（包含共享+私有文件）"""
        from api.experiment import version_api

        data = version_api.get_input_files(
            self._experiment_id,
            self._template_id,
            include_shared=True
        )
        self._storage_path = data.get("storage_path", "")
        self._files = data.get("input_files", [])
        self._updateFileList()

        # 使用后端返回的可用空间
        free_space = data.get("free_space")
        if hasattr(self, 'freeSpaceLabel'):
            if free_space is not None:
                self.freeSpaceLabel.setText(f"可用空间: {format_file_size(free_space)}")
            else:
                self.freeSpaceLabel.setText("可用空间: --")

    def _load_output_files(self):
        """加载输出文件"""
        from api.experiment import version_api

        if self._version_id is None:
            return

        data = version_api.get_output_files(
            self._experiment_id,
            self._template_id,
            self._version_id
        )
        self._storage_path = data.get("storage_path", "")
        self._files = data.get("output_files", [])
        self._updateFileList()

    def _save_to_backend(self):
        """保存输入文件数据到后端（仅输入模式）"""
        if self._mode != "input":
            return

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
            logger.error(f"无法保存输入文件: {str(e)}")
            InfoBar.warning(
                title="保存失败",
                content=f"无法保存输入文件: {str(e)}",
                parent=self.window(),
                duration=3000
            )


# 保持向后兼容的别名
InputFileField = FileListField
